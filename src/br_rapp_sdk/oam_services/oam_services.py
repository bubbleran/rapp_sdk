from .network import OAMNetworkService
from .terminal import OAMTerminalService


class OAMServices:
    """This class provides methods to interact with the OAM Services API in BubbleRAN environment.

    It includes services for managing networks and terminals.
    """
    def __init__(self, kubeconfig_path: str = None, namespace: str = "trirematics"):
        """
        Initialize the OAMservices client by loading the Kubernetes configuration and setting up defaults.

        Parameters:
            kubeconfig_path (Optional[str]): Path to the kubeconfig file (default: None - use the default kubeconfig).
            namespace (str): Kubernetes namespace for the OAM Services (default: "trirematics").
        """
        self._network = OAMNetworkService(kubeconfig_path, namespace)
        self._terminal = OAMTerminalService(kubeconfig_path, namespace)

    # network and terminal must become read-only properties
    @property
    def network(self) -> OAMNetworkService:
        """Get the OAM Network Service."""
        return self._network
    
    @property
    def terminal(self) -> OAMTerminalService:
        """Get the OAM Terminal Service."""
        return self._terminal