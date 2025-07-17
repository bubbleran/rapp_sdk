from .chat_model_config import ChatModelClientConfig
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain.chat_models.base import BaseChatModel
from langchain_core.tools import BaseTool
from langchain.chat_models import init_chat_model
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Mapping,
    Optional,
    Sequence,
)

class ChatModelClient:
    """Client that facilitates interaction with a chat model.

    This client can be used to send user instructions to the chat model and receive responses.
    It supports both single and batch invocations, and can handle tool calls if tools are provided.
    Args:
        chat_model_config (ChatModelClientConfig, optional):
            Configuration for the chat model client.
        system_instructions (str):
            System instructions to be used in the chat model.
        tools (Sequence[Dict[str, Any] | type | Callable | BaseTool | None], optional):
            LangChain-defined tools to be used by the chat model.

    Examples:
    ```python
    config = ChatModelClientConfig.from_env(
        client_name="SampleClient",
        logging_level="debug",
    )
    client = ChatModelClient(
        chat_model_config=config,
        system_instructions="You always reply in pirate language.",
    )
    response = client.invoke(HumanMessage("What is the weather like today?"))
    ```
    """

    def __init__(
        self,
        chat_model_config: ChatModelClientConfig | None = None,
        system_instructions: str = "You are a helpful assistant.",
        tools: Sequence[Dict[str, Any] | type | Callable | BaseTool | None] = None,
    ):
        """Initialize the ChatModelClient with the given configuration, system instructions, and tools.

        Args:
            chat_model_config (ChatModelClientConfig, optional):
                Configuration for the chat model client. If None, it will be loaded from environment variables.
            system_instructions (str):
                System instructions to be used by the chat model.
            tools (Sequence[Dict[str, Any] | type | Callable | BaseTool | None], optional):
                LangChain-defined tools to be used by the chat model.
        Raises:
            EnvironmentError: If the chat model configuration is not provided and cannot be loaded from environment variables.
        """
        self.config = ChatModelClientConfig.from_env() if chat_model_config is None else chat_model_config
        self.system_instructions = SystemMessage(system_instructions)
        self.tools = tools

        self._chat_model = init_chat_model(
            model=self.config.model,
            model_provider=self.config.model_provider,
            base_url=self.config.base_url,
        )
        self._log(f"model {self.config.model_provider}:{self.config.model} initialized{' with tools' if self.tools else ''}", "info")
        if self.tools:
            self._chat_model = self._chat_model.bind_tools(self.tools)
        

    def get_chat_model(self) -> BaseChatModel:
        """Get the chat model instance.
        
        Returns:
            BaseChatModel: The chat model instance configured with the provided model and tools.
        """
        return self._chat_model
    
    @classmethod
    def _validate_input_type(
        cls,
        input: HumanMessage | List[ToolMessage],
    ):
        """Validate the input for the invoke and stream method."""
        if isinstance(input, HumanMessage):
            return True
        if isinstance(input, list) and all(isinstance(msg, ToolMessage) for msg in input):
            return True
        return False
    
    def _build_messages_list(
        self,
        input: HumanMessage | List[ToolMessage],
        history: Optional[List[BaseMessage]] = None,
    ) -> List[BaseMessage]:
        """Build the messages list for the chat model.
        
        The system instructions are always included as the first message.
        If `history` is provided, it is prepended to the messages list.
        If the `input` is a `HumanMessage`, it is appended to the messages list.
        If the `input` is a list of `ToolMessage`, they are appended to the messages list.

        Returns:
            List[BaseMessage]: The list of messages to be sent to the chat model.
        """
        messages = [self.system_instructions]
        if history:
            messages += history
        if isinstance(input, HumanMessage):
            messages.append(input)
        else:
            messages += input
        return messages
    
    def _update_history(
        self,
        history: List[BaseMessage],
        input: HumanMessage | List[ToolMessage],
        response: AIMessage,
    ) -> None:
        """Update the history **in-place** with the input and response.
        
        If the input is a HumanMessage, it is appended directly.
        If the input is a list of ToolMessages, they are appended to the history.
        The response is always appended to the history.
        """
        if isinstance(input, HumanMessage):
            history.append(input)
        else:
            history += input
        history.append(response)

    def invoke(
        self,
        input: HumanMessage | List[ToolMessage],
        history: Optional[List[BaseMessage]] = None,
    ) -> AIMessage:
        """Invoke the chat model with user instructions or tool call results.

        If the `history` is provided, it will be prepended to the input message.
        This method modifies the `history` in-place to include the input and output messages.
        
        Parameters:
            input (HumanMessage | List[ToolMessage]): The user input or tool call results to process.
            history (Optional[List[BaseMessage]]): Optional history of messages.
        
        Returns:
            AIMessage: The response from the chat model.
        Raises:
            ValueError: If the input type is invalid or if the response from the chat model is not an `AIMessage`.
        """
        assert self._validate_input_type(input), f"Invalid input type: {type(input)}. Expected HumanMessage or List[ToolMessage]."

        # Build the messages for the chat model
        messages = self._build_messages_list(input, history)
        # self._log(f"User query: {input}", "debug")

        # Invoke the chat model and extract the response
        response = self._chat_model.invoke(messages)
        if not isinstance(response, AIMessage):
            raise ValueError(f"Expected AIMessage after invocation of chat model, got {type(response)}")
        # self._log(f"Assistant response: {response}", "debug")

        # Update the history
        if history is not None:
            self._update_history(history, input, response)
        
        # Return the response
        return response

    # TODO: test this function
    # def stream(
    #     self,
    #     input: HumanMessage | List[ToolMessage],
    #     history: Optional[List[BaseMessage]] = None,
    # ) -> Iterator[AIMessageChunk]:
    #     """Stream the chat model with user instructions or tool call results.
        
    #     Parameters:
    #         input (HumanMessage | List[ToolMessage]): The user input or tool call results to process.
    #         history (Optional[List[BaseMessage]]): Optional history of messages to prepend to the input.
    #             If provided, it will be modified in-place to include the input and output messages.
    #     Yields:
    #         AIMessageChunk: Chunks of the response from the chat model as they are generated.
    #     Raises:
    #         ValueError: If the input type is invalid or if the response chunk is not an AIMessageChunk.
    #     """
    #     assert self._validate_input_type(input), f"Invalid input type: {type(input)}. Expected HumanMessage or List[ToolMessage]."

    #     # Build the messages for the chat model
    #     messages = self._build_messages_list(input, history)
    #     self._log(f"User query: {input}", "debug")

    #     # Stream the chat model and yield response chunks
    #     all_content = ""
    #     all_tool_calls = []

    #     for chunk in self._chat_model.stream(messages):
    #         if not isinstance(chunk, AIMessageChunk):
    #             raise ValueError(f"Expected AIMessageChunk during streaming, got {type(chunk)}")
    #         self._log(f"Assistant response chunk: {chunk}", "debug")
    #         yield chunk
    #         all_content += chunk.content if hasattr(chunk, "content") else str(chunk)
    #         all_tool_calls.extend(chunk.tool_calls)
        
    #     # Update the history with the complete response
    #     if history is not None:
    #        # Create a final AIMessage with all content and tool calls
    #         final_response = AIMessage(
    #             content=all_content,
    #             additional_kwargs={
    #                 "tool_calls": all_tool_calls,
    #             }
    #         )
    #         self._update_history(history, input, final_response)
    
    def batch(
        self,
        inputs: List[HumanMessage],
        history: Optional[List[BaseMessage]] = None,
    ) -> List[AIMessage]:
        """Batch process multiple human messages in batch.

        If the `history` is provided, it will be prepended to each input message.
        This method does NOT modify the `history` in-place.
        
        Parameters:
            inputs (List[HumanMessage]): List of user inputs to process.
            history (Optional[List[BaseMessage]]): Optional history of messages.

        Returns:
            List[AIMessage]: List of responses from the chat model for each input.
        Raises:
            ValueError: If the input type is invalid or if the response from the chat model is not an AIMessage.
        """
        if not all([self._validate_input_type(input) for input in inputs]):
            raise ValueError(f"Invalid input type in batch: {[type(input) for input in inputs]}. Expected HumanMessage.")
        full_history = [self.system_instructions] + history if history else [self.system_instructions]
        messages = [
            full_history + [input]
            for input in inputs
        ]
        responses = self._chat_model.batch(messages)
        if not all(isinstance(response, AIMessage) for response in responses):
            raise ValueError("Expected all responses to be AIMessage instances after batch invocation of chat model.")
        return responses

    def _log(
        self,
        message: str,
        level: Literal["info", "debug", "warning", "error", "critical"],
        exc_info: bool = None,
        extra: Mapping[str, object] | None = None
    ) -> None:
        """
        Log a message using the logger in the ChatModelConfig
        """
        if not self.config.logger:
            return
        
        logger = self.config.logger
        if level == "info":
            logger.info(message, extra=extra, exc_info=exc_info)
        elif level == "debug":
            logger.debug(message, extra=extra, exc_info=exc_info)
        elif level == "warning":
            logger.warning(message, extra=extra, exc_info=exc_info)
        elif level == "error":
            logger.error(message, extra=extra, exc_info=exc_info)
        elif level == "critical":
            logger.critical(message, extra=extra, exc_info=exc_info)
        else:
            raise ValueError(f"Invalid log level: {level}")