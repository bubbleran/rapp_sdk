import httpx
import logging
import os
from ..common import create_logger
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, InMemoryPushNotifier, TaskUpdater
from a2a.types import (
    AgentCard,
    InternalError,
    InvalidParamsError,
    Part,
    Task,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils import (
    new_agent_text_message,
    new_task,
)
from a2a.utils.errors import ServerError
from abc import ABC, abstractmethod
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command, Interrupt
from pydantic import BaseModel
from starlette.applications import Starlette
from typing import AsyncIterable, Literal, Mapping, Optional, Self
from typing_extensions import override

AgentTaskStatus = Literal["working", "input_required", "completed", "error"]
"""AgentTaskStatus is a type alias for the status of an agent task.

The possible values are:
- `working`: The agent is currently processing the task.
- `input_required`: The agent requires additional input from the user to proceed.
- `completed`: The agent has successfully completed the task.
- `error`: An error occurred during the task execution.
"""

class AgentTaskResult(BaseModel):
    """Result of an agent invocation.

    Attributes:
        task_status (AgentTaskStatus): The status of the agent task.
        content (str): The content of the agent's response or message.
    
    Attributes meaning:
    | `task_status`  | `content`                                                            |
    |----------------|----------------------------------------------------------------------|
    | working        | Ongoing task description or progress update.                         |
    | input_required | Description of the required user input or context.                   |
    | completed      | Final response or result of the agent's processing.                  |
    | error          | Error message indicating what went wrong during the task execution.  |
    """

    task_status: AgentTaskStatus
    content: str

class AgentState(BaseModel, ABC):
    """Abstract base class representing an agent's state.

    This class combines Pydantic's model validation with abstract state management
    requirements for agent operations. Subclasses should define concrete state models
    while implementing the required abstract methods.

    Note:
        Subclasses must implement all abstract methods and can define additional state
        fields using Pydantic's model field declarations.

    Abstract Methods:
        from_query: Factory method to create an agent state from an initial query
        update_after_checkpoint_restore: Refresh state after checkpoint restoration
        to_task_result: Convert current state to task result object
    
    Methods:
        is_waiting_for_human_input: Check if agent requires human input
    
    Example:
    ```python
    from br_rapp_sdk.agents import AgentState, AgentTaskResult
    from typing import List, Optional, Self
    from typing_extensions import override

    class MyAgentState(AgentState):
        user_inputs: List[str] = []
        assistant_outputs: List[str] = []
        question: str = ""
        answer: Optional[str] = None

        @classmethod
        def from_query(cls, query: str) -> Self:
            return cls(
                user_inputs=[query],
                question=query,
            )
        
        @override
        def update_after_checkpoint_restore(self, query: str) -> None:
            self.user_inputs.append(query)
            self.question = query
        
        @override
        def to_task_result(self) -> AgentTaskResult:
            if self.answer is None:
                return AgentTaskResult(
                    task_status="working",
                    content="Processing your request..."
                )
            return AgentTaskResult(
                task_status="completed",
                content=self.answer
            )
    """

    @classmethod
    @abstractmethod
    def from_query(
        cls,
        query: str
    ) -> Self:
        """Instantiate agent state from initial query.

        Factory method called by the execution framework to create a new state instance.
        Alternative to direct initialization, allowing state-specific construction logic.

        Args:
            query: Initial user query to bootstrap agent state

        Returns:
            Self: Fully initialized agent state instance
        """
        pass

    @abstractmethod
    def update_after_checkpoint_restore(self, query: str) -> None:
        """Update state with new query after checkpoint restoration.

        Called by the SDK when restoring from a saved checkpoint. Allows the state
        to synchronize with new execution parameters before resuming the graph.

        Args:
            query: New query to execute with the restored state
        """

    @abstractmethod
    def to_task_result(self) -> AgentTaskResult:
        """Convert current state to a task result object.

        Used to yield execution results during graph processing. This method defines
        how the agent's internal state translates to external-facing task results.

        Returns:
            AgentTaskResult: Task result representation of current state
        """

    def is_waiting_for_human_input(self) -> bool:
        """Check if agent is blocked waiting for human input.

        Default implementation returns `False`. Override in subclasses to implement
        human-in-the-loop pausing behavior.

        Returns:
            bool: True if agent requires human input to proceed, False otherwise
        """
        return False

class AgentGraph(ABC):
    """Abstract base class for agent graphs.
    
    Extend this class to implement the specific behavior of an agent.

    Example:
    ```python
    from br_rapp_sdk.agents import AgentGraph, AgentState
    from langgraph.runnables import RunnableConfig
    from langgraph.graph import StateGraph

    class MyAgentState(BaseModel):
        # Your state here
        # ...
        pass

    class MyAgentGraph(AgentGraph):
        def __init__(self):
            # Define the agent graph using langgraph.graph.StateGraph class
            graph_builder = StateGraph(MyAgentState)
            # Add nodes and edges to the graph as needed ...
            super().__init__(
                graph_builder=graph_builder,
                use_checkpoint=True,
                logger_name="my_agent"
            )
            self._log("Graph initialized", "info")
        
        # Your nodes logic here
        # ...
    """

    _graph: CompiledStateGraph
    _AgentStateType: type[AgentState]

    def __init__(
        self,
        graph_builder: StateGraph,
        use_checkpoint: bool = False,
        logger_name: Optional[str] = None,
    ):
        """Initialize the AgentGraph with a state graph and optional checkpointing and logger.
        Compile the state graph and set up the logger if the logger_name is provided.

        Args:
            graph_builder (StateGraph): The state graph builder.
            use_checkpoint (bool): Whether to use checkpointing. Defaults to False.
            logger_name (Optional[str]): The name of the logger to use. Defaults to None.
        """
        self._logger = None if logger_name is None else create_logger(
            name=logger_name,
            level=os.getenv("LOG_LEVEL", "info").lower(),
        )
        self._memory = MemorySaver() if use_checkpoint else None
        self._graph = graph_builder.compile(
            checkpointer=self._memory
        )
        self._AgentStateType = graph_builder.state_schema
        print(type(self._AgentStateType))
    
    def _log(
        self,
        message: str,
        level: Literal["info", "debug", "warning", "error", "critical"],
        exc_info: bool = None,
        extra: Mapping[str, object] | None = None
    ) -> None:
        """Log a message using the logger if the logger_name was provided in the constructor."""
        if not self._logger:
            return
        
        if level == "info":
            self._logger.info(message, extra=extra, exc_info=exc_info)
        elif level == "debug":
            self._logger.debug(message, extra=extra, exc_info=exc_info)
        elif level == "warning":
            self._logger.warning(message, extra=extra, exc_info=exc_info)
        elif level == "error":
            self._logger.error(message, extra=extra, exc_info=exc_info)
        elif level == "critical":
            self._logger.critical(message, extra=extra, exc_info=exc_info)
        else:
            raise ValueError(f"Invalid log level: {level}")
    
    async def astream(
        self,
        query: str,
        config: RunnableConfig,
    ) -> AsyncIterable[AgentTaskResult]:
        """Asynchronously stream results from the agent graph based on the query and configuration.
        This method performes the following steps:
        1. Looks for a checkpoint associated with the provided configuration.
        2. If no checkpoint is found, creates a new agent state from the query, 
            using the `from_query` method of the `AgentStateType`.
        3. If a checkpoint is found, restores the state from the checkpoint and updates it with the query
            using the `update_after_checkpoint_restore` method.
        4. Prepares the input for the graph execution, wrapping the state in a `Command` if the
            `is_waiting_for_human_input` method of the state returns `True`.
        5. Executes the graph with the `astream` method, passing the input and configuration.
        6. For each item in the stream:
            - If it is an interrupt, yields an `AgentTaskResult` with the status
            `input_required`. This enables human-in-the-loop interactions.
            - Otherwise, validates the item as an `AgentStateType` and converts it to an
            `AgentTaskResult` using the `to_task_result` method of the state. Then it yields the result.

        This method prints debug logs in the format `[<thread_id>]: <message>`.
        
        Args:
            query (str): The query to process.
            config (RunnableConfig): Configuration for the runnable.
        Returns:
            AsyncIterable[AgentTaskResult]: An asynchronous iterable of agent task results.
        """
        thread_id = config.get("configurable", {}).get("thread_id")

        checkpoint = self._memory.get(config) if self._memory else None
        if checkpoint is None:
            self._log(f"[{thread_id}]: No checkpoint", "debug")
            state = self._AgentStateType.from_query(query)
            self._log(f"[{thread_id}]: State initialized", "debug")
        else:
            self._log(f"[{thread_id}]: Checkpoint found", "debug")
            channel_values = checkpoint.get("channel_values", {})
            state = self._AgentStateType.model_validate(channel_values)
            self._log(f"[{thread_id}]: State restored", "debug")
            state.update_after_checkpoint_restore(query)
            self._log(f"[{thread_id}]: State updated", "debug")

        
        input = Command(resume=state) if state.is_waiting_for_human_input() else state
        
        stream = self._graph.astream(
            input=input,
            config=config,
            stream_mode="values",
        )
        self._log(f"[{thread_id}]: Graph execution started {'with Command' if state.is_waiting_for_human_input() else ''}", "debug")

        async for item in stream:
            if "__interrupt__" in item:
                intr: Interrupt = item.get("__interrupt__")[0]
                self._log(f"[{thread_id}]: Yielding Interrupt: {intr.value}", "debug")
                yield AgentTaskResult(
                    task_status="input_required",
                    content=intr.value,
                )
            else:
                state_item = self._AgentStateType.model_validate(item)
                task_result_item = state_item.to_task_result()
                self._log(f"[{thread_id}]: Yielding AgentTaskResult: [{task_result_item.task_status}] {task_result_item.content}", "debug")
                yield task_result_item


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MinimalAgentExecutor(AgentExecutor):
    """Minimal Agent Executor.
    
    Minimal implementation of the AgentExecutor interface used by the `AgentApplication` class to execute agent tasks.
    """

    def __init__(
        self,
        agent_graph: AgentGraph
    ):
        self.agent_graph = agent_graph

    @override
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        if not self._request_ok(context):
            raise ServerError(error=InvalidParamsError())

        query = context.get_user_input()
        task = context.current_task
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)
        updater = TaskUpdater(event_queue, task.id, task.contextId)
        try:
            config = {"configurable": {"thread_id": task.contextId}}
            async for item in self.agent_graph.astream(query, config):
                match item.task_status:
                    case "working":
                        await updater.update_status(
                            TaskState.working,
                            new_agent_text_message(
                                item.content,
                                task.contextId,
                                task.id,
                            ),
                        )
                    case "input_required":
                        await updater.update_status(
                            TaskState.input_required,
                            new_agent_text_message(
                                item.content,
                                task.contextId,
                                task.id,
                            ),
                            final=True,
                        )
                        break
                    case "completed":
                        await updater.add_artifact(
                            [Part(root=TextPart(text=item.content))],
                        )
                        await updater.complete()
                        break
                    case "error":
                        raise ServerError(error=InternalError(message=item.content))
                    case _:
                        logger.warning(f"Unknown task status: {item.task_status}")
        except Exception as e:
            logger.error(f'An error occurred while streaming the response: {e}')
            raise ServerError(error=InternalError()) from e

    def _request_ok(self, context: RequestContext) -> bool:
        return True

    @override
    async def cancel(
        self, request: RequestContext, event_queue: EventQueue
    ) -> Task | None:
        raise ServerError(error=UnsupportedOperationError())

class AgentApplication:
    """Agent Application based on `Starlette`.

    Attributes:
        agent_card (AgentCard): The agent card containing metadata about the agent.
        agent_graph (AgentGraph): The agent graph that defines the agent's behavior and capabilities.
    
    Example:
    ```python
        import httpx
        import json
        import uvicorn
        from a2a.types import AgentCard
        from br_rapp_sdk.agents import AgentApplication

        with open('./agent.json', 'r') as file:
            agent_data = json.load(file)
            agent_card = AgentCard.model_validate(agent_data)
            logger.info(f'Agent Card loaded: {agent_card}')
        
        url = httpx.URL(agent_card.url)
        graph = MyAgentGraph()
        agent = AgentApplication(
            agent_card=agent_card,
            agent_graph=graph,
        )

        uvicorn.run(agent.build(), host=url.host, port=url.port)
    ```
    """

    def __init__(
        self,
        agent_card: AgentCard,
        agent_graph: AgentGraph
    ):
        """
        Initialize the AgentApplication with an agent card and agent graph.
        Args:
            agent_card (AgentCard): The agent card.
            agent_graph (AgentGraph): The agent graph implementing the agent's logic.
        """
        self._agent_executor = MinimalAgentExecutor(agent_graph)
        self.agent_card = agent_card

        self._httpx_client = httpx.AsyncClient()
        self._request_handler = DefaultRequestHandler(
            agent_executor=self._agent_executor,
            task_store=InMemoryTaskStore(),
            push_notifier=InMemoryPushNotifier(self._httpx_client),
        )
        self._server = A2AStarletteApplication(
            agent_card=self.agent_card,
            http_handler=self._request_handler
        )

    @property
    def agent_graph(self) -> AgentGraph:
        """Get the agent graph."""
        return self._agent_executor.agent_graph
    
    def build(self) -> Starlette:
        """Build the A2A Starlette application.
        
        Returns:
            Starlette: The built Starlette application.
        """
        return self._server.build()