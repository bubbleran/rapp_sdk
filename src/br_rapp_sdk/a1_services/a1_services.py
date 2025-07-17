from kubernetes import client, config
import requests
from .a1_policy_types import *
from ..oam_services.oam_services import OAMServices
from ..common import (
    load_kubeconfig,
    get_cr,
    list_cr,
    apply_cr,
    delete_cr,
    KubectlOperationResult,
)
from .common import (
    ODIN_GROUP,
    ODIN_VERSION,
    ODIN_POLICYJOB_KIND,
    ODIN_POLICYJOB_PLURAL,
)
class A1Services:
    """ This class provides methods to interact with the A1 Services API in BubbleRAN environment.

    A1Services is a client for managing A1 policies in the BubbleRAN environment.
    
    Attributes:
        kubeconfig_path (Optional[str]): Path to the kubeconfig file.
        namespace (str): Kubernetes namespace for A1 policy jobs.

    Examples :
        ```python
        from br_rapp_sdk import A1Services
        from br_rapp_sdk.a1_services.a1_policy_types import PolicyObjectInformation, PolicyId
        a1_services = A1Services()
        # List all policies
        result = a1_services.list_policies()
        if result.status == "success":
            for policy_id, policy_info in result.data:
                print(f"Policy ID: {policy_id}, Info: {policy_info}")
        else:
            print(f"Error: {result.error}")
        # Get a specific policy
        policy_id = PolicyId("example-policy")
        result = a1_services.get_policy(policy_id)
        if result.status == "success":
            policy_info = result.data.get('item')
            print(f"Policy Info: {policy_info}")
        else:
            print(f"Error: {result.error}")
        ```
    """

    def __init__(
        self,
        kubeconfig_path: Optional[str] = None,
        namespace: str = "trirematics"
    ):
        """
        Initialize the A1Services client by loading the Kubernetes configuration and setting up defaults.

        Parameters:
            kubeconfig_path (Optional[str]): Path to the kubeconfig file. If None, uses the default kubeconfig.
            namespace (str): Kubernetes namespace for A1 policy jobs. Default is "trirematics".

        Raises:
            RuntimeError: If kubeconfig cannot be loaded or if there are issues with the API.
        """
        load_kubeconfig(kubeconfig_path)

        self.kubeconfig_path = kubeconfig_path
        self.namespace = namespace

        self._api = client.CustomObjectsApi()
        self._group = ODIN_GROUP
        self._version = ODIN_VERSION
        self._plural = ODIN_POLICYJOB_PLURAL
        self._kind = ODIN_POLICYJOB_KIND

    def list_policies(
        self,
        policy_id: Optional[PolicyId] = None,
    ) -> KubectlOperationResult:
        """ This method lists all policies in the A1 Services API.

        Parameters:
            Policy_id (Optional[PolicyId]): If provided, filters policies by the given ID.
        
        Returns:
            KubectlOperationResult: An object representing the result of the operation, containing a list of PolicyId and PolicyObjectInformation tuples if successful, or an error message if not.

        Example:
        ```python
        from br_rapp_sdk import A1Services
        a1_services = A1Services()
        result = a1_services.list_policies()
        # Check if the operation was successful
        if result.status == "success":
            for policy_id, policy_info in result.data:
                print(f"Policy ID: {policy_id}, Info: {policy_info}")
        else:
            print(f"Error: {result.error}")
        ```
        """
        policies = []

        list_policy_result = list_cr(
            kube_api_instance=self._api,
            group=self._group,
            version=self._version,
            plural=self._plural,
            namespace=self.namespace
        )
        if list_policy_result.status == "success":
            items = list_policy_result.data.get("items", [])
            if policy_id:
                # Filter policies by the given PolicyId
                items = [
                        item for item in items if 
                        item["metadata"]["name"] == policy_id
                ]

            for item in items:
                policy_id = PolicyId(item.get("metadata", {}).get("name"))
                policy_obj = PolicyObjectInformation(**item.get('spec', {}))
                policies.append((policy_id, policy_obj))
            list_policy_result.data['items'] = policies

        return list_policy_result
    
    def get_policy(
            self,
            policy_id: PolicyId
        ) -> KubectlOperationResult:
        """
        Get a specific policy from the A1 Services API.

        Parameters:
            policy_id (PolicyId): The ID of the policy to retrieve.

        Returns:
            KubectlOperationResult: An object representing the result of the operation, containing the PolicyObjectInformation if successful, or an error message if not.
        
        Example:
        ```python
        from br_rapp_sdk import A1Services
        from br_rapp_sdk.a1_services.a1_policy_types import PolicyId
        a1_services = A1Services()
        policy_id = PolicyId("example-policy")
        result = a1_services.get_policy(policy_id)
        if result.status == "success":
            policy_info = result.data.get('item')
            print(f"Policy Info: {policy_info}")
        else:
            print(f"Error: {result.error}")
        ```
        """

        get_policy_result = get_cr(
            kube_api_instance=self._api,
            group=self._group,
            version=self._version,
            plural=self._plural,
            namespace=self.namespace,
            name=policy_id
        )
        if get_policy_result.status == "success":
            item = get_policy_result.data.get("item", {})
            policy_obj = PolicyObjectInformation(**item.get('spec', {}))
            get_policy_result.data = {'item': policy_obj}
        return get_policy_result
    
    def get_policy_feedback_api_urls(
        self,
        policy_id: PolicyId
    ) -> KubectlOperationResult:
        """
        Get the feedback API URLs for dynamic xApps in a specific policy.

        Parameters:
            policy_id (PolicyId): The ID of the policy to retrieve feedback URLs for.
        
        Returns:
            KubectlOperationResult: An object representing the result of the operation, containing a list of tuples with DynamicXappId and their corresponding feedback URLs if successful, or an error message if not.
        
        Example:
        ```python
        from br_rapp_sdk import A1Services
        from br_rapp_sdk.a1_services.a1_policy_types import PolicyId, DynamicXappId
        a1_services = A1Services()
        policy_id = PolicyId("example-policy")
        result = a1_services.get_policy_feedback_api_urls(policy_id)
        if result.status == "success":
            for dynamic_xapp, feedback_urls in result.data:
                print(f"Dynamic xApp: {dynamic_xapp}, Feedback URLs: {[url.ip for url in feedback_urls]}")
        else:
            print(f"Error getting policy feedback URLs: {result.error}")
        ```
        """

        get_policy_result = get_cr(
            kube_api_instance=self._api,
            group=self._group,
            version=self._version,
            plural=self._plural,
            namespace=self.namespace,
            name=policy_id
        )

        if get_policy_result.status == "success":
            item = get_policy_result.data.get("item", {})
            status = item.get("status", {})
            dyn_xapps_map = status.get("dynXAppsElementsMap", {})

            feedback_urls = []
            for dyn_xapp_key, dyn_xapp_value in dyn_xapps_map.items():
                dyn_xapp_name, dyn_xapp_target, dyn_xapps_network, dyn_xapp_namespace = dyn_xapp_key.split('.')
                dynamic_xapp = DynamicXappId(f"{dyn_xapp_name}.{dyn_xapp_target}.{dyn_xapps_network}")
                urls = [PolicyFeedbackDestination(**fb) for fb in dyn_xapp_value.get("feedbackUrls", [])]
                feedback_urls.append((dynamic_xapp, urls))

            get_policy_result.data = {'items': feedback_urls}

        return get_policy_result

    def get_policy_feedback(
        self,
        policy_feedback_dest: PolicyFeedbackDestination,
        time_out: int = 5
    ) -> KubectlOperationResult:
        """
        Get the policy feedback from a specific feedback destination.

        Parameters:
            policy_feedback (PolicyFeedbackDestination): The feedback destination containing the full URL to retrieve feedback from.
            time_out (int): The timeout for the HTTP request in seconds. Default is 5 seconds.
        
        Returns:
            KubectlOperationResult: An object representing the result of the operation, containing the feedback data if successful, or an error message if not.
        
        Example:
        ```python
        from br_rapp_sdk import A1Services
        from br_rapp_sdk.a1_services.a1_policy_types import PolicyFeedbackDestination
        a1_services = A1Services()
        policy_feedback = PolicyFeedbackDestination(...)
        result = a1_services.get_policy_feedback(policy_feedback)
        if result.status == "success":
            print(f"Policy Feedback: {result.data.get('item', {})}")
        else:
            print(f"Error getting policy feedback: {result.error}")
        ```
        """
        try:
            response = requests.get(
                url=policy_feedback_dest.full_url,
                timeout=time_out
            )
            response.raise_for_status()
            feedback_data = response.json()
            return KubectlOperationResult(status="success", operation="get", data={'item': feedback_data})
        except requests.RequestException as e:
            return KubectlOperationResult(
                status="error",
                operation="get",
                error={
                    "code": 408,
                    "message": str(e)
                }
            )

    def apply_policy(
        self,
        policy_name: str,
        policy_object: PolicyObjectInformation
    ) -> KubectlOperationResult:
        """
        Apply a policy to the A1 Services API.

        Parameters:
            policy_name (str): The name of the policy to apply.
            policy_object (PolicyObjectInformation): The policy object containing the specifications.

        Returns:
            KubectlOperationResult: An object representing the result of the operation, containing the PolicyId if successful, or an error message if not.

        Example:
        ```python
        from br_rapp_sdk import A1Services
        from br_rapp_sdk.a1_services.a1_policy_types import PolicyObjectInformation, PolicyId, NearRtRicId, PolicyTypeId, PolicyObject, ScopeIdentifier, PolicyStatements
        a1_services = A1Services()
        policy_object = PolicyObjectInformation(
            near_rt_ric_id=NearRtRicId("ric-name.network-name"),
            policy_type_id=PolicyTypeId("cm/example"),
            policy_object=PolicyObject(
                scope_identifier=ScopeIdentifier(...),
                policy_statements=PolicyStatements(...)
            )
        )
        result = a1_services.apply_policy(policy_name="example-policy", policy_object=policy_object)
        if result.status == 'success':
            policy_id = result.data.get('policy_id')
            print(f"Policy applied successfully: {policy_id}")
        else:
            print(f"Error applying policy: {result.error}")
        ``` 
        """
        body = {
            "apiVersion": f"{self._group}/{self._version}",
            "kind": self._kind,
            "metadata": {
                "name": policy_name,
                "namespace": self.namespace
            },
            "spec": policy_object.model_dump(exclude_none=True, by_alias=True)
        }

        apply_result = apply_cr(
            kube_api_instance=self._api,
            group=self._group,
            version=self._version,
            plural=self._plural,
            namespace=self.namespace,
            body=body
        )

        if apply_result.status == "success":
            policy_id = PolicyId(apply_result.data.get("metadata", {}).get("name"))
            apply_result.data = {'policy_id': policy_id}

        return apply_result

    def delete_policy(
        self,
        policy_id: PolicyId
    ) -> KubectlOperationResult:
        """
        Delete a policy from the A1 Services API.

        Parameters:
            policy_id (PolicyId): The ID of the policy to delete.
        
        Returns:
            KubectlOperationResult: An object representing the result of the operation, indicating success or failure.
        
        Example:
        ```python
        from br_rapp_sdk import A1Services
        from br_rapp_sdk.a1_services.a1_policy_types import PolicyId
        a1_services = A1Services()
        policy_id = PolicyId("example-policy")
        result = a1_services.delete_policy(policy_id)
        if result.status == "success":
            print(f"Policy {policy_id} deleted successfully.")
        else:
            print(f"Error deleting policy: {result.error}")
        ```
        """

        delete_result = delete_cr(
            kube_api_instance=self._api,
            group=self._group,
            version=self._version,
            plural=self._plural,
            namespace=self.namespace,
            name=policy_id
        )

        if delete_result.status == "success":
            delete_result.data = {'policy_id': policy_id}

        return delete_result

    def get_policy_status(
        self,
        policy_id: PolicyId
    ) -> KubectlOperationResult:
        """
        Get the status of a specific policy in the A1 Services API.

        Parameters:
            policy_id (PolicyId): The ID of the policy to check.

        Returns:
            KubectlOperationResult: An object representing the result of the operation, containing the policy status if successful, or an error message if not.
        
        Example:
        ```python
        from br_rapp_sdk import A1Services
        from br_rapp_sdk.a1_services.a1_policy_types import PolicyId
        a1_services = A1Services()
        policy_id = PolicyId("example-policy")
        result = a1_services.get_policy_status(policy_id)
        if result.status == "success":
            print(f"Policy Status: {result.data.get('status')}")
        else:
            print(f"Error getting policy status: {result.error}")
        ```
        """
        
        get_policy_result = get_cr(
            kube_api_instance=self._api,
            group=self._group,
            version=self._version,
            plural=self._plural,
            namespace=self.namespace,
            name=policy_id
        )

        if get_policy_result.status == "success":
            item = get_policy_result.data.get("item", {})
            get_policy_result.data["status"] = item.get("status", {})


        return get_policy_result

    def get_rics(
        self,
        network_id: Optional[NetworkId] = None
        ) -> KubectlOperationResult:
        """
        Get the list of Near RT RICs from the OAM services.
        This method retrieves the Near RT RICs from the OAM services and returns their IDs.

        Parameters:
            Optional[NetworkId]: If provided, filters Near RT RICs by the given NetworkId.
        
        Returns:
            KubectlOperationResult: An object representing the result of the operation, containing a list of NearRtRicId if successful, or an error message if not.
        
        Example:
        ```python
        from br_rapp_sdk import A1Services
        a1_services = A1Services()
        result = a1_services.get_rics()
        if result.status == "success":
            near_rt_rics = result.data.get('items', [])
            for near_rt_ric in near_rt_rics:
                print(f"Near RT RIC ID: {near_rt_ric}")
        else:
            print(f"Error getting Near RT RICs: {result.error}")
        ```
        """
        oam_services = OAMServices(kubeconfig_path=self.kubeconfig_path, namespace=self.namespace)
        result = oam_services.network.list_networks(network_id=network_id, part="edge")
        if result.status == "success":
            near_rt_rics = []
            items = result.data.get('items', [])

            for  element_name, element_spec in items:
                model = element_spec.model
                if model == "mosaic5g/flexric":
                    near_rt_rics.append(NearRtRicId(element_name))
            result.data['items'] = near_rt_rics
        return result