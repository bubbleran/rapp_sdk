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
    ATHENA_NETWORK_KIND,
    ATHENA_NETWORK_PLURAL,
)
from .network_types import *
from typing import Optional, Union

class OAMNetworkService:
    """This class provides methods to interact with the OAM Services Network-related API in BubbleRAN environment.

    It allows you to manage networks, including creating, retrieving, updating, and deleting network configurations.

    Attributes:
        kubeconfig_path (Optional[str]): Path to the kubeconfig file for Kubernetes API access.
        namespace (str): The Kubernetes namespace where the network CRs are located (default: "trirematics").
    
    Examples:
    ```python
    from br_rapp_sdk.oam_services.network import OAMNetworkService

    network_service = OAMNetworkService()
    network_spec = NetworkSpec(
        # Fill in the required fields for the network specification
    )
    result = network_service.apply_network("my-new-network", network_spec)
    if result.status == 'success':
        print("Network applied successfully: ", result.data.get('network_id'))
    else:
        print("Failed to apply network: ", result.error)
    ```
    """

    def __init__(
        self,
        kubeconfig_path: Optional[str] = None,
        namespace: str = "trirematics"
    ):
        """Initialize the Network client by loading the Kubernetes configuration and setting up defaults.
        
        Parameters:
            kubeconfig_path (Optional[str]): Path to the kubeconfig file (default: None - use the default kubeconfig).
            namespace (str): Kubernetes namespace for the Network CRs (default: "trirematics").
        
        Raises:
            RuntimeError: If the kubeconfig cannot be loaded.
        """
        load_kubeconfig(kubeconfig_path)

        self.kubeconfig_path = kubeconfig_path
        self.namespace = namespace

        self._api = client.CustomObjectsApi()
        self._group = ATHENA_GROUP
        self._version = ATHENA_VERSION
        self._kind = ATHENA_NETWORK_KIND
        self._plural = ATHENA_NETWORK_PLURAL
    
    def _get_parts_from_item(
        self,
        item: dict,
        part: Optional[NetworkPart] = None
    ) -> list:
        """Extracts the specified part from a network item.

        Parameters:
            item (dict): The network from which to extract the part.
            part (Optional[NetworkPart]): The part to extract ('access', 'core', 'edge', or None for full spec).

        Returns:
            list: A list of extracted parts or an empty list if the part is not found.
        """
        result = []
        net_id = NetworkId(item.get('metadata', {}).get('name', ''))
        match part:
            case 'access':
                access_items = item.get('spec', {}).get('access', [])
                for access_item in access_items:
                    access_id = AccessNetworkId(f"{access_item.get('name')}.{net_id}")
                    access_spec = AccessNetworkSpec(**access_item)
                    result.append((access_id, access_spec))
            case 'core':
                core_items = item.get('spec', {}).get('core', [])
                for core_item in core_items:
                    core_id = CoreNetworkId(f"{core_item.get('name')}.{net_id}")
                    core_spec = CoreNetworkSpec(**core_item)
                    result.append((core_id, core_spec))
            case 'edge':
                edge_items = item.get('spec', {}).get('edge', [])
                for edge_item in edge_items:
                    edge_id = EdgeNetworkId(f"{edge_item.get('name')}.{net_id}")
                    edge_spec = EdgeNetworkSpec(**edge_item)
                    result.append((edge_id, edge_spec))
            case None:
                network_spec = NetworkSpec(**item.get('spec', {}))
                result.append((net_id, network_spec))
            case _:
                pass
        return result

    def list_networks(
        self,
        network_id: Optional[NetworkId] = None,
        part: Optional[NetworkPart] = None
    ) -> KubectlOperationResult:
        """Get the list of networks.

        Parameters:
            network_id (Optional[NetworkId]): The ID of the network to filter by (default: None - list all networks).
                Useful in combination with the `part` parameter to list specific parts of a network.
            part (Optional[NetworkPart]): The part of the network to list ('access', 'core', 'edge', or None for full spec) (default: None).

        Returns:
            KubectlOperationResult: An object representing the result of the operation, containing a list of NetworkId and NetworkSpec tuples if successful, or an error message if not.
        
        Examples:
        Listing all networks:

        ```python
        from br_rapp_sdk.oam_services.network import OAMNetworkService

        network_service = OAMNetworkService()
        result = network_service.list_networks()
        # Check if the operation was successful
        if result.status == 'success':
            for net_id, spec in result.data.get('items'):
                # Use net_id and spec as needed
                print(f"Network ID: {net_id}, Spec: {spec}")
        else:
            print("Failed to retrieve networks: ", result.error)
        ```

        Listing the core part of the `mynet` network:

        ```python
        from br_rapp_sdk.oam_services.network import OAMNetworkService
        from br_rapp_sdk.oam_services.network_types import NetworkId

        network_service = OAMNetworkService()
        network_id = NetworkId("mynet")
        result = network_service.list_networks(network_id=network_id, part='core')
        # Check if the operation was successful
        if result.status == 'success':
            for core_id, core_spec in result.data.get('items'):
                # Use core_id and core_spec as needed
                print(f"Core Network ID: {core_id}, Spec: {core_spec}")
        else:
            print("Failed to retrieve network core: ", result.error)
        ```
        """
        networks = []

        list_network_result = list_cr(
            kube_api_instance=self._api,
            group=self._group,
            version=self._version,
            plural=self._plural,
            namespace=self.namespace
        )
        if list_network_result.status == 'success':
            items = list_network_result.data.get('items', [])
            if network_id:
                items = [
                        item for item in items if 
                        item["metadata"]["name"] == network_id
                ]
            for item in items:
                networks.extend(self._get_parts_from_item(item, part))
            list_network_result.data['items'] = networks
        
        return list_network_result

    def get_network(
        self,
        network_id: NetworkId
    ) -> KubectlOperationResult:
        """Get a specific network by its ID.

        Parameters:
            network_id (NetworkId): The ID of the network to retrieve.
        
        Returns:
            KubectlOperationResult: An object representing the result of the operation, containing the NetworkSpec if successful, or an error message if not.
        
        Examples:
        ```python
        from br_rapp_sdk.oam_services.network import OAMNetworkService

        network_service = OAMNetworkService()
        network_id = NetworkId("sample-network")
        result = network_service.get_network(network_id)
        # Check if the operation was successful
        if result.status == 'success':
            # Use the network_spec as needed
            network_spec = result.data.get('item')
        else:
            print("Failed to retrieve network: ", result.error)
        ```
        """
        get_network_result = get_cr(
            kube_api_instance=self._api,
            group=self._group,
            version=self._version,
            plural=self._plural,
            namespace=self.namespace,
            name=network_id
        )
        if get_network_result.status == 'success':
            network_spec = NetworkSpec(**get_network_result.data.get('item', {}).get('spec', {}))
            get_network_result.data = { 'item': network_spec }
        return get_network_result

    def apply_network(
        self,
        network_name: str,
        network_spec: NetworkSpec
    ) -> KubectlOperationResult:
        """Apply the network to OAM services API.

        Parameters:
            network_name (str): The name of the network.
            network_spec (NetworkSpec): The network specification to apply.
        
        Returns:
            KubectlOperationResult: The result of the apply operation, containing the NetworkId if successful, or an error message if not.

        Examples:
        ```python
        from br_rapp_sdk.oam_services.network import OAMNetworkService

        network_service = OAMNetworkService()
        network_spec = NetworkSpec(
            slices=[...],  # Fill in the required fields for the network spec
            access=[...],  # AccessNetworkSpec instances
            core=[...],    # CoreNetworkSpec instances
            edge=[...]     # EdgeNetworkSpec instances
        )
        result = network_service.apply_network("my-new-network", network_spec)
        if result.status == 'success':
            # Use the network_id as needed
            network_id = result.data.get('network_id')
            print("Network applied successfully:", network_id)
        else:
            print("Failed to apply network:", result.error)
        ```
        """
        body = {
            "apiVersion": f"{self._group}/{self._version}",
            "kind": self._kind,
            "metadata": {
                "name": network_name,
                "namespace": self.namespace
            },
            "spec": network_spec.model_dump(exclude_none=True, by_alias=True)
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
            network_id = NetworkId(network_name)
            apply_result.data = { 'network_id': network_id }
        return apply_result

    def delete_network(
        self,
        network_id: NetworkId
    ) -> KubectlOperationResult:
        """Delete the network from the OAM Services API.

        Parameters:
            network_id (NetworkId): The ID of the network to delete.

        Returns:
            KubectlOperationResult: The result of the delete operation, containing an empty data dictionary if successful, or an error message if not.
        
        Examples:
        ```python
        from br_rapp_sdk.oam_services.network import OAMNetworkService

        network_service = OAMNetworkService()
        network_id = NetworkId("sample-network")
        result = network_service.delete_network(network_id)
        if result.status == 'success':
            print("Network deleted successfully.")
        else:
            print("Failed to delete network:", result.error)
        ```
        """
        delete_result = delete_cr(
            kube_api_instance=self._api,
            group=self._group,
            version=self._version,
            plural=self._plural,
            namespace=self.namespace,
            name=network_id
        )
        if delete_result.status == 'success':
            delete_result.data = {}
        return delete_result