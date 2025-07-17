import json
from langchain_core.messages import ToolCall as LangchainToolCall
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
from typing_extensions import Self

class ToolCall(BaseModel):
    """Tool call model.

    This model represents a tool call with its name, arguments, and an optional unique identifier.
    The class provides useful methods to convert from a Langchain ToolCall and to dump the model to a dictionary or JSON string:

    - `from_langchain_tool_call`: Converts a Langchain ToolCall to this model.
    - `model_dump`: Dumps the model to a dictionary.
    - `model_dump_json`: Dumps the model to a JSON string.
    """
    
    name: str = Field(..., description="Name of the tool to call")
    arguments: Dict[str, Any] = Field(..., description="Arguments for the tool call")
    id: Optional[str] = Field(None, description="Unique identifier for the tool call")

    @classmethod
    def from_langchain_tool_call(cls, tool_call: LangchainToolCall) -> Self:
        """Convert a Langchain ToolCall to the custom ToolCall model.
        
        Args:
            tool_call (LangchainToolCall): The Langchain ToolCall instance to convert.
        
        Returns:
            ToolCall: An instance of the custom ToolCall model.
        """
        return cls(
            name=tool_call["name"],
            arguments=tool_call["args"],
            id=None if tool_call["id"] is None else tool_call["id"],
        )
    
    def model_dump(self) -> Dict[str, Any]:
        """Dump the model to a dictionary.
        
        Returns:
            Dict[str, Any]: A dictionary representation of the model.
        """
        return {
            "name": self.name,
            "arguments": self.arguments,
            "id": self.id,
        }

    def model_dump_json(self) -> str:
        """Dump the model to a JSON string.
        
        Returns:
            str: A JSON string representation of the model.
        """
        return json.dumps(self.model_dump(), indent=4)