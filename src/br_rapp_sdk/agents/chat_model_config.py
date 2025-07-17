from ..common import create_logger
from pydantic import BaseModel, Field
from typing import Optional
from typing_extensions import Literal
import logging
import os

ModelProvider = Literal[
    "openai",
    "nvidia",
    "ollama",
]
"""`ModelProvider` is a type alias for the supported model providers.
The currently supported providers are:
- `openai`
- `nvidia`
- `ollama`
"""

class ChatModelClientConfig(BaseModel):
    """Configuration for the chat model client.
    
    This class is used to configure the chat model client with the necessary parameters.
    Some model providers may require specific environment variables to be set, like OPENAI_API_KEY for OpenAI.

    Args:
        model (str): The name of the model to use.
        model_provider (ModelProvider): The provider of the model (e.g., OpenAI, Meta, etc.).
        base_url (str, optional): The base URL for the model provider, required for non-OpenAI providers.
        client_name (str, optional): Name for the client logger.
        logging_level (Literal["debug", "info", "warning", "error", "critical"], optional): Logging level for the client logger.

    When a client name and logging level are provided, a logger is created to be used by the client.
    
    The class can be instantiated directly or created from environment variables using the `from_env` \
    class method (usually preferred).

    Examples:

    Direct instantiation:
    ```python
    config = ChatModelClientConfig(
        model="gpt-4o-mini",
        model_provider="openai",
        base_url="https://api.openai.com/v1",
        client_name="SampleClient",
        logging_level="debug",
    )
    ```

    From environment variables:
    ```python
    config = ChatModelClientConfig.from_env(
        client_name="SampleClient",
        logging_level="debug",
    )
    ```
    """

    class Config:
        arbitrary_types_allowed = True

    model: str
    model_provider: ModelProvider
    base_url: Optional[str] = Field(
        default=None,
        description="Base URL for the model provider. Required for non-OpenAI providers.",
    )
    logger: Optional[logging.Logger] = Field(
        default=None,
        description="Logger for the ChatModelClient.",
    )

    def __init__(
        self,
        model: str,
        model_provider: ModelProvider,
        base_url: Optional[str] = None,
        client_name: Optional[str] = None,
        logging_level: Optional[Literal["debug", "info", "warning", "error", "critical"]] = None,
    ):
        """Initialize the ChatModelClientConfig with the provided parameters.
        
        Parameters:
            model (str): The name of the model to use.
            model_provider (ModelProvider): The provider of the model (e.g., openai, nvidia, etc.).
            base_url (Optional[str]): The base URL for the model provider, required for non-OpenAI providers.
            client_name (Optional[str]): Name for the client logger.
            logging_level (Optional[Literal["debug", "info", "warning", "error", "critical"]]): Logging level for the client logger.
        """
        super().__init__(
            model=model,
            model_provider=model_provider,
            base_url=base_url,
            logger=create_logger(client_name, logging_level) if logging_level else None,
        )

    @classmethod
    def from_env(
        cls,
        client_name: Optional[str] = None,
        logging_level: Optional[Literal["debug", "info", "warning", "error", "critical"]] = None,
    ) -> "ChatModelClientConfig":
        """Create a `ChatModelClientConfig` instance from environment variables.
        
        This method reads the following environment variables:
        - `MODEL`: The model name, which can be in the format `<provider>:<model>`.
        - `MODEL_PROVIDER` (optional): The provider of the model (e.g., openai, nvidia, ollama, etc.).
        - `LOG_LEVEL` (optional): The logging level for the client logger.

        Parameters:
            client_name (Optional[str]): Name for the client logger.
            logging_level (Optional[Literal["debug", "info", "warning", "error", "critical"]]): Logging level for the client logger.
        Returns:
            An instance of `ChatModelClientConfig` configured with values from environment variables.
        Raises:
            EnvironmentError: If the required environment variables are not set or if the format is incorrect.
        """

        model = os.getenv("MODEL")
        if not model:
            raise EnvironmentError("MODEL environment variable not set.")
        
        model_provider = os.getenv("MODEL_PROVIDER")
        if not model_provider:
            model_parts = model.split(":", 1)
            if len(model_parts) == 2:
                model_provider, model_name = model_parts
            else:
                raise EnvironmentError(
                    "MODEL_PROVIDER environment variable not set. Either set it or use the format <provider>:<model> for the MODEL variable."
                )
        else:
            model_name = model

        base_url = os.getenv("BASE_URL")

        if logging_level is None:
            logging_level = os.getenv("LOG_LEVEL")
        
        return cls(
            model=model_name,
            model_provider=model_provider,
            base_url=base_url,
            client_name=client_name,
            logging_level=logging_level,
        )
