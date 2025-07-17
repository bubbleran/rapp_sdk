from kubernetes import client, config
import requests
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
    ODIN_MONITORINGJOB_KIND,
    ODIN_MONITORINGJOB_PLURAL,
)
from .monitoring_types import *
from typing import List

class MonitoringServices:
    """This class provides methods to interact with the monitoring services API in BubbleRAN environment.
    
    MonitoringServices allows you to create, list, and delete monitoring jobs in the BubbleRAN environment.
    
    Attributes:
        kubeconfig_path (Optional[str]): Path to the kubeconfig file.
        namespace (str): Kubernetes namespace for Monitoring jobs.
    
    Example:
    ```python
    from br_rapp_sdk import MonitoringServices
    from br_rapp_sdk.monitoring_services.monitoring_types import MonitoringJob, MonitoringJobSpec

    # Initialize the MonitoringServices client
    monitoring_services = MonitoringServices("/path/to/kubeconfig")

    # list all monitorings
    result = monitoring_services.list_monitorings()
    if result.status == 'success':
        for monitoring_id, monitoring_obj in result.data.get("items", []):
            print(f"Monitoring ID: {monitoring_id}, Object: {monitoring_obj}")
    else:
        print(f"Error listing monitorings: {result.error}")
    # Get a specific monitoring job
    monitoring_id = MonitoringId("example-monitoring")
    result = monitoring_services.get_monitoring(monitoring_id)
    if result.status == 'success':
        monitoring_obj = result.data.get("item")
        print(f"Monitoring Job: {monitoring_obj}")
    else:
        print(f"Error retrieving monitoring job: {result.error}")
    ```
    """

    def __init__(self, kubeconfig_path: str = None, namespace: str = "trirematics"):
        """Initializes the MonitoringServices client.

        Parameters:
            kubeconfig_path (str): Path to the kubeconfig file. If None, uses the default kubeconfig.
            namespace (str): Kubernetes namespace for Monitoring jobs. Default is "trirematics".
        
        Raises:
            RuntimeError: If kubeconfig cannot be loaded or if there are issues with the API.
        """
        load_kubeconfig(kubeconfig_path)
        
        self.kubeconfig_path = kubeconfig_path
        self.namespace = namespace

        self._api = client.CustomObjectsApi()
        self._group = ODIN_GROUP
        self._version = ODIN_VERSION
        self._plural = ODIN_MONITORINGJOB_PLURAL
        self._kind = ODIN_MONITORINGJOB_KIND

    
    def list_monitorings(
        self,
        monitoring_id: Optional[MonitoringId] = None,
    ) -> KubectlOperationResult:
        """This method lists all Monitorings in the Monitoring Services API.

        Parameters:
            monitoring_id (Optional[MonitoringId]): ID of the monitoring job to filter by. If None, lists all jobs.

        Returns:
            KubectlOperationResult: An object representing the result of the operation, containing a list of MonitoringId and MonitoringObjectInformation tuples if successful, or an error message if not.
        
        Example:
        ```python
        from br_rapp_sdk import MonitoringServices
        monitoring_services = MonitoringServices()
        result = monitoring_services.list_monitorings()
        if result.status == 'success':
            for monitoring_id, monitoring_obj in result.data:
                print(f"Monitoring ID: {monitoring_id}")
        else:
            print(f"Error listing monitorings: {result.error}")
        ```
        """

        monitorings = []

        list_monitoring_result = list_cr(
            kube_api_instance=self._api,
            group=self._group,
            version=self._version,
            plural=self._plural,
            namespace=self.namespace,
        )

        if list_monitoring_result.status == "success":
            items = list_monitoring_result.data.get("items", [])
            if monitoring_id:
                items = [
                    item for item in items if 
                    item["metadata"]["name"] == monitoring_id
                ]
            
            for item in items:
                monitoring_id = MonitoringId(item.get("metadata", {}).get("name"))
                monitoring_obj = MonitoringObjectInformation(**item.get("spec", {}))
                monitorings.append((monitoring_id, monitoring_obj))
            list_monitoring_result.data["items"] = monitorings

        return list_monitoring_result


    def get_monitoring(
        self,
        monitoring_id: MonitoringId,
    ) -> KubectlOperationResult:
        """This method retrieves a specific Monitoring job by its ID.

        Parameters:
            monitoring_id (MonitoringId): ID of the monitoring job to retrieve.

        Returns:
            KubectlOperationResult: An object representing the result of the operation, containing the MonitoringObjectInformation if successful, or an error message if not.
        
        Example:
        ```python
        from br_rapp_sdk import MonitoringServices
        from br_rapp_sdk.monitoring_services.monitoring_types import MonitoringId
        monitoring_services = MonitoringServices()
        result = monitoring_services.get_monitoring(MonitoringId("example-monitoring"))
        if result.status == 'success':
            monitoring_obj = result.data.get('item')
            print(f"Monitoring Job: {monitoring_obj}")
        else:
            print(f"Error retrieving monitoring job: {result.error}")
        ```
        """

        get_monitoring_result = get_cr(
            kube_api_instance=self._api,
            group=self._group,
            version=self._version,
            plural=self._plural,
            namespace=self.namespace,
            name=monitoring_id,
        )
        if get_monitoring_result.status == "success":
            item = get_monitoring_result.data.get("item", {})
            monitoring_obj = MonitoringObjectInformation(**item.get("spec", {}))
            get_monitoring_result.data["item"] = monitoring_obj
        return get_monitoring_result
    
    def apply_monitoring(
        self,
        monitoring_name: str,
        monitoring_object: MonitoringObjectInformation,
    ) -> KubectlOperationResult:
        """This method applies a Monitoring job to the Monitoring Services API.

        Parameters:
            monitoring_object (MonitoringObjectInformation): The Monitoring job object to apply. It should contain the necessary specifications for the monitoring job.

        Returns:
            KubectlOperationResult: An object representing the result of the operation, containing the applied MonitoringId if successful, or an error message if not.
        
        Example:
        ```python
        from br_rapp_sdk import MonitoringServices
        from br_rapp_sdk.monitoring_services.monitoring_types import MonitoringObjectInformation, MonitoringTypeId, TargetId, MonitoringObject  
        monitoring_services = MonitoringServices()
        monitoring_job = MonitoringObjectInformation(
            target=TargetId("ric-name.network-name"),
            monitoring_type_id =MonitoringTypeId(name="cm/example"),
            monitoring_object = MonitoringObject( ... )
        )
        monitoring_name = "example-monitoring"
        result = monitoring_services.apply_monitoring(monitoring_name, monitoring_job)
        if result.status == 'success':
            print(f"Monitoring Job applied successfully: {result.data.get('monitoring_id')}")
        else:
            print(f"Error applying monitoring job: {result.error}")
        ```
        """
        body = {
            "apiVersion": f"{self._group}/{self._version}",
            "kind": self._kind,
            "metadata": {
                "name": monitoring_name,
                "namespace": self.namespace
            },
            "spec": monitoring_object.model_dump(exclude_none=True, by_alias=True)
        }

        apply_monitoring_result = apply_cr(
            kube_api_instance=self._api,
            group=self._group,
            version=self._version,
            plural=self._plural,
            namespace=self.namespace,
            body=body
        )
        if apply_monitoring_result.status == "success":
            monitoring_id = MonitoringId(apply_monitoring_result.data.get("metadata", {}).get("name"))
            apply_monitoring_result.data["monitoring_id"] = monitoring_id
        return apply_monitoring_result
    
    def delete_monitoring(
        self,
        monitoring_id: MonitoringId,
    ) -> KubectlOperationResult:
        """This method deletes a specific Monitoring job by its ID.

        Parameters:
            monitoring_id (MonitoringId): ID of the monitoring job to delete.

        Returns:
            KubectlOperationResult: An object representing the result of the operation, containing a success message if successful, or an error message if not.
        
        Example:
        ```python
        from br_rapp_sdk import MonitoringServices
        from br_rapp_sdk.monitoring_services.monitoring_types import MonitoringId
        monitoring_services = MonitoringServices()
        result = monitoring_services.delete_monitoring(MonitoringId("example-monitoring"))
        if result.status == 'success':
            print("Monitoring Job deleted successfully.")
        else:
            print(f"Error deleting monitoring job: {result.error}")
        ```
        """

        delete_monitoring_result = delete_cr(
            kube_api_instance=self._api,
            group=self._group,
            version=self._version,
            plural=self._plural,
            namespace=self.namespace,
            name=monitoring_id,
        )
        if delete_monitoring_result.status == "success":
            delete_monitoring_result.data = {'monitoring_id': monitoring_id}
       
        return delete_monitoring_result
    
    def get_monitoring_status(
        self,
        monitoring_id: MonitoringId,
    ) -> KubectlOperationResult:
        """This method retrieves the status of a specific Monitoring job by its ID.

        Parameters:
            monitoring_id (MonitoringId): ID of the monitoring job to retrieve the status for.

        Returns:
            KubectlOperationResult: An object representing the result of the operation, containing the monitoring status if successful, or an error message if not.
        
        Example:
        ```python
        from br_rapp_sdk import MonitoringServices
        from br_rapp_sdk.monitoring_services.monitoring_types import MonitoringId
        monitoring_services = MonitoringServices()
        result = monitoring_services.get_monitoring_status(MonitoringId("example-monitoring"))
        if result.status == 'success':
            print(f"Monitoring Job Status: {result.data.get('status')}")
        else:
            print(f"Error retrieving monitoring job status: {result.error}")
        ```
        """
        get_status_result = get_cr(
            kube_api_instance=self._api,
            group=self._group,
            version=self._version,
            plural=self._plural,
            namespace=self.namespace,
            name=monitoring_id
        )

        if get_status_result.status == "success":
            item = get_status_result.data.get("item", {})
            get_status_result.data["status"] = item.get("status", {})
        
        return get_status_result

