from kubernetes import client, config
from ..common import (
    load_kubeconfig,
    get_cr,
    list_cr,
    apply_cr,
    delete_cr,
    KubectlOperationResult,
)
from .common import (
    ATHENA_GROUP,
    ATHENA_VERSION,
    ATHENA_TERMINAL_KIND,
    ATHENA_TERMINAL_PLURAL,
)
from typing import List, Tuple
from .terminal_types import *

class OAMTerminalService:
    """This class provides methods to interact with the OAM Services Terminal-related API in BubbleRAN environment.

    It allows you to list, get, apply, and delete terminals in the Kubernetes cluster.

    Attributes:
        kubeconfig_path (str): Path to the kubeconfig file for Kubernetes API access.
        namespace (str): Kubernetes namespace where the Terminal CRs are located.
    
    Examples:
    ```python
    from br_rapp_sdk.oam_services.terminal import OAMTerminalService

    terminal_service = OAMTerminalService()
    terminal_spec = TerminalSpec(
        # Fill in the required fields for the terminal specification
    )
    result = terminal_service.apply_terminal("my-new-terminal", terminal_spec)
    if result.status == 'success':
        print("Terminal applied successfully: ", result.data.get('terminal_id'))
    else:
        print("Failed to apply terminal: ", result.error)
    ```
    """

    def __init__(
        self,
        kubeconfig_path: str = None,
        namespace: str = "trirematics"
    ):
        """Initialize the Terminal client by loading the Kubernetes configuration and setting up defaults.
        
        Parameters:
            kubeconfig_path (Optional[str]): Path to the kubeconfig file (default: None - use the default kubeconfig).
            namespace (str): Kubernetes namespace for the Terminal CRs (default: "trirematics").
        
        Raises:
            RuntimeError: If the kubeconfig cannot be loaded.
        """
        load_kubeconfig(kubeconfig_path)
        
        self.kubeconfig_path = kubeconfig_path
        self.namespace = namespace

        self._api = client.CustomObjectsApi()
        self._group = ATHENA_GROUP
        self._version = ATHENA_VERSION
        self._kind = ATHENA_TERMINAL_KIND
        self._plural = ATHENA_TERMINAL_PLURAL

    def list_terminals(
        self,
    ) -> KubectlOperationResult:
        """Get the list of terminals.

        Returns:
            KubectlOperationResult: An object representing the result of the operation, containing a list of TermId and TerminalSpec tuples if successful, or an error message if not.

        Examples:
        ```python
        from br_rapp_sdk.oam_services.terminal import OAMTerminalService

        terminal_service = OAMTerminalService()
        result = terminal_service.list_terminals()
        # Check if the operation was successful
        if result.status == 'success':
            for term_id, spec in result.data.get('items'):
                # Use term_id and spec as needed
                print(f"Terminal ID: {term_id}, Spec: {spec}")
        else:
            print("Failed to retrieve terminals: ", result.error)
        ```
        """
        terminals = []

        list_terminal_result = list_cr(
            kube_api_instance=self._api,
            group=self._group,
            version=self._version,
            plural=self._plural,
            namespace=self.namespace
        )
        if list_terminal_result.status == 'success':
            items = list_terminal_result.data.get('items', [])
            for item in items:
                term_id = TermId(item.get('metadata', {}).get('name'))
                terminal_spec = TerminalSpec(**item.get('spec', {}))
                terminals.append((term_id, terminal_spec))
            list_terminal_result.data['items'] = terminals

        return list_terminal_result

    def get_terminal(
        self,
        terminal_id: TermId
    ) -> KubectlOperationResult:
        """Get a terminal by its ID.

        Parameters:
            terminal_id (TermId): The ID of the terminal to retrieve.

        Returns:
            KubectlOperationResult: An object representing the result of the operation, containing the TerminalSpec if successful, or an error message if not.

        Examples:
        ```python
        from br_rapp_sdk.oam_services.terminal import OAMTerminalService

        terminal_service = OAMTerminalService()
        term_id = TermId("sample-terminal")
        result = terminal_service.get_terminal(term_id)
        # Check if the operation was successful
        if result.status == 'success':
            # Use the terminal_spec as needed
            terminal_spec = result.data.get('item')
        else:
            print("Failed to retrieve terminal: ", result.error)
        ```
        """
        get_network_result = get_cr(
            kube_api_instance=self._api,
            group=self._group,
            version=self._version,
            plural=self._plural,
            namespace=self.namespace,
            name=terminal_id
        )
        if get_network_result.status == 'success':
            network_spec = TerminalSpec(**get_network_result.data.get('item', {}).get('spec', {}))
            get_network_result.data = { 'item': network_spec }
        return get_network_result


    def apply_terminal(
        self,
        terminal_name: str,
        terminal_spec: TerminalSpec
    ) -> KubectlOperationResult:
        """Apply the terminal to the OAM Services API.

        Parameters:
            terminal_name (str): The name of the terminal.
            terminal_spec (TerminalSpec): The terminal specification to apply.

        Returns:
            KubectlOperationResult: The result of the operation, containing the terminal ID if successful, or an error message if not.

        Examples:
        ```python
        from br_rapp_sdk.oam_services.terminal import OAMTerminalService

        terminal_service = OAMTerminalService()
        terminal_spec = TerminalSpec(
            # Fill in the required fields for the terminal spec
        )
        result = terminal_service.apply_terminal("my-new-terminal", terminal_spec)
        if result.status == 'success':
            # Use the terminal_id as needed
            terminal_id = result.data.get('terminal_id')
            print("Terminal applied successfully:", terminal_id)
        else:
            print("Failed to apply terminal:", result.error)
        ```
        """
        body = {
            "apiVersion": f"{self._group}/{self._version}",
            "kind": self._kind,
            "metadata": {
                "name": terminal_name,
                "namespace": self.namespace
            },
            "spec": terminal_spec.model_dump(exclude_none=True, by_alias=True)
        }
        apply_result = apply_cr(
            kube_api_instance=self._api,
            group=self._group,
            version=self._version,
            plural=self._plural,
            namespace=self.namespace,
            body=body
        )
        if apply_result.status == 'success':
            terminal_id = TermId(terminal_name)
            apply_result.data = { 'terminal_id': terminal_id }
        return apply_result
        

    def delete_terminal(
        self,
        terminal_id: TermId
    ) -> KubectlOperationResult:
        """Delete the terminal from the OAM Services API.

        Parameters:
            terminal_id (TermId): The ID of the terminal to delete.

        Returns:
            KubectlOperationResult: The result of the delete operation, containing an empty data dictionary if successful, or an error message if not.
        
        Examples:
        ```python
        from br_rapp_sdk.oam_services.terminal import OAMTerminalService

        terminal_service = OAMTerminalService()
        terminal_id = TermId("sample-terminal")
        result = terminal_service.delete_terminal(terminal_id)
        if result.status == 'success':
            print("Terminal deleted successfully.")
        else:
            print("Failed to delete terminal:", result.error)
        ```
        """
        delete_result = delete_cr(
            kube_api_instance=self._api,
            group=self._group,
            version=self._version,
            plural=self._plural,
            namespace=self.namespace,
            name=terminal_id
        )
        if delete_result.status == 'success':
            delete_result.data = {}
        return delete_result
