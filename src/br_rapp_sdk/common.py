from kubernetes.client.exceptions import ApiException
from kubernetes import client, config
from pydantic import BaseModel, model_validator
from typing import Dict, Literal, Optional, Self
import json
import logging

class KubectlError(BaseModel):
    """A Pydantic model to represent an error that occurred during a kubectl operation.
    
    Attributes:
        code (int): The HTTP status code of the error.
        message (str): A message describing the error.
        details (dict): Optional details about the error, if applicable.
    """
    code: int
    message: str
    details: Dict = {}

class KubectlOperationResult(BaseModel):
    """A Pydantic model to represent the result of a kubectl operation.
    
    Attributes:
        status (Literal['success', 'error']): The status of the operation, either 'success' or 'error'.
        operation (Literal['apply', 'create', 'update', 'delete', 'get', 'list']): The type of operation performed.
        data (Dict): Optional data returned from the operation, if applicable. Usually contains custom resource data.
        error (KubectlError | None): An error object if the operation failed, otherwise None.
    """
    status: Literal['success', 'error']
    operation: Literal['apply', 'create', 'update', 'delete', 'get', 'list']
    data: Dict = {}
    error: KubectlError | None = None

    @model_validator(mode='after')
    def validate_error(self) -> Self:
        """
        Validate the error field after the model is initialized.
        
        If the status is 'error', ensure that the error field is populated.
        """
        if self.status == 'error' and not self.error:
            raise ValueError("If status is 'error', the error field must be populated.")
        if self.status == 'success' and self.error:
            raise ValueError("If status is 'success', the error field must be None.")
        return self


def apply_cr(
    kube_api_instance: client.CustomObjectsApi,
    group: str,
    version: str,
    plural: str,
    namespace: str,
    body: Dict,
) -> KubectlOperationResult:
    """Apply (create or update) a Custom Resource (CR) to the Kubernetes cluster.

    Parameters:
        kube_api_instance (CustomObjectsApi): The Kubernetes API client
        group (str): The API group of the CR
        version (str): The API version of the CR
        plural (str): The plural name of the CR
        namespace (str): The namespace of the CR
        body (dict): The body of the CR
    
    Returns:
        KubectlOperationResult: An object representing the result of the operation.
    """
    # Check if the body contains the required fields
    error_msg = ""
    if 'metadata' not in body:
        error_msg = "The body must contain a 'metadata' field with the CR name and namespace."
    elif 'name' not in body['metadata']:
        error_msg = "The 'metadata' field must contain a 'name' field with the CR name."
    elif 'namespace' not in body['metadata']:
        error_msg = "The 'metadata' field must contain a 'namespace' field with the CR namespace."

    if error_msg:
        return KubectlOperationResult(
            status='error',
            operation='apply',
            data={},
            error=KubectlError(
                code=400,
                message=error_msg,
                details={}
            )
        )
    
    # Try to update the CR first
    # If it does not exist, it will raise a 404 error which we will catch and handle by creating the CR.

    try:
        current_cr = kube_api_instance.get_namespaced_custom_object(
            group=group,
            version=version,
            namespace=namespace,
            plural=plural,
            name=body['metadata']['name']
        )

        # Update the resourceVersion in the body to match the current state
        body['metadata']['resourceVersion'] = current_cr['metadata']['resourceVersion']

        kube_api_instance.replace_namespaced_custom_object(
            group=group,
            version=version,
            namespace=namespace,
            plural=plural,
            name=body['metadata']['name'],
            body=body
        )

        return KubectlOperationResult(
            status='success',
            operation='update',
            data=body,
            error=None
        )
    except ApiException as e:
        if e.status == 404:
            # remove resourceVersion if it exists in the body
            if 'metadata' in body and 'resourceVersion' in body['metadata']:
                del body['metadata']['resourceVersion']
            try:
                kube_api_instance.create_namespaced_custom_object(
                    group=group,
                    version=version,
                    namespace=namespace,
                    plural=plural,
                    body=body
                )
                return KubectlOperationResult(
                    status='success',
                    operation='create',
                    data=body,
                    error=None
                )
            except ApiException as e:
                try:
                    parsed_details = json.loads(e.body) if e.body else {}
                except json.JSONDecodeError:
                    parsed_details = {"raw": e.body}

                return KubectlOperationResult(
                    status='error',
                    operation='create',
                    data={},
                    error=KubectlError(
                        code=e.status,
                        message=str(e),
                        details=parsed_details
                    )
                )
        else:
            return KubectlOperationResult(
                status='error',
                operation='update',
                data={},
                error=KubectlError(
                    code=e.status,
                    message=str(e),
                    details=e.body if e.body else {}
                )
            )

def delete_cr(
    kube_api_instance: client.CustomObjectsApi,
    group: str,
    version: str,
    plural: str,
    namespace: str,
    name: str,
    body: Dict = {},
) -> KubectlOperationResult:
    """Delete a Custom Resource (CR) from the Kubernetes cluster.

    Parameters:
        kube_api_instance (CustomObjectsApi): The Kubernetes API client
        group (str): The API group of the CR
        version (str): The API version of the CR
        plural (str): The plural name of the CR
        namespace (str): The namespace of the CR
        name (str): The name of the CR
        body (dict): The body of the CR (default: {}) - You can specify options like propagationPolicy here if needed

    Returns:
        KubectlOperationResult: An object representing the result of the operation.
    """

    try:
        response = kube_api_instance.delete_namespaced_custom_object(
            group=group,
            version=version,
            namespace=namespace,
            plural=plural,
            name=name,
            body=body,
        )
        return KubectlOperationResult(
            status='success',
            operation='delete',
            data=response,
            error=None
        )
    except ApiException as e:
        return KubectlOperationResult(
            status='error',
            operation='delete',
            data={},
            error=KubectlError(
                code=e.status,
                message=str(e),
                details=e.body if e.body else {}
            )
        )

def get_cr(
    kube_api_instance: client.CustomObjectsApi,
    group: str,
    version: str,
    plural: str,
    namespace: str,
    name: str,
) -> KubectlOperationResult:
    """Get a Custom Resource (CR) from the Kubernetes cluster.

    Parameters:
        kube_api_instance (CustomObjectsApi): The Kubernetes API client
        group (str): The API group of the CR
        version (str): The API version of the CR
        plural (str): The plural name of the CR
        namespace (str): The namespace of the CR
        name (str): The name of the CR

    Returns:
        KubectlOperationResult: An object representing the result of the operation.
    """

    try:
        response = kube_api_instance.get_namespaced_custom_object(
            group=group,
            version=version,
            namespace=namespace,
            plural=plural,
            name=name
        )
        return KubectlOperationResult(
            status='success',
            operation='get',
            data={'item': response},
            error=None
        )
    except ApiException as e:
        if e.status == 404:
            return None
        else:
            raise e

def list_cr(
    kube_api_instance: client.CustomObjectsApi,
    group: str,
    version: str,
    plural: str,
    namespace: str,
) -> KubectlOperationResult:
    """List Custom Resources (CRs) from the Kubernetes cluster.

    Parameters:
        kube_api_instance (CustomObjectsApi): The Kubernetes API client
        group (str): The API group of the CR
        version (str): The API version of the CR
        plural (str): The plural name of the CR
        namespace (str): The namespace of the CR

    Returns:
        KubectlOperationResult: An object representing the result of the operation.
    """

    try:
        # Attempt to list the CDs
        response = kube_api_instance.list_namespaced_custom_object(
            group=group,
            version=version,
            namespace=namespace,
            plural=plural
        )
        return KubectlOperationResult(
            status='success',
            operation='list',
            data={'items': response.get('items', [])},
            error=None
        )
    except ApiException as e:
        return KubectlOperationResult(
            status='error',
            operation='list',
            data={},
            error=KubectlError(
                code=e.status,
                message=str(e),
                details=e.body if e.body else {}
            )
        )

def create_logger(
    name: str,
    level: Literal["debug", "info", "warning", "error", "critical"] = "info",
) -> logging.Logger:
    """Create a logger for the ChatModelClient."""
    
    if level == "debug":
        logging_level = logging.DEBUG
    elif level == "info":
        logging_level = logging.INFO
    elif level == "warning":
        logging_level = logging.WARNING
    elif level == "error":
        logging_level = logging.ERROR
    elif level == "critical":
        logging_level = logging.CRITICAL
    else:
        raise ValueError("Invalid logging level. Choose from: debug, info, warning, error, critical.")
    

    logger = logging.getLogger(name)
    logger.setLevel(logging_level)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s "
    )
    # clean next 2 lines
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def load_kubeconfig(
    kubeconfig_path: Optional[str] = None,
) -> None:
    """Load the kubeconfig file for Kubernetes API access.
    First, it tries to load the kubeconfig from the specified path or default location.
    If that fails, it attempts to load the in-cluster configuration.
    """
    try:
        if kubeconfig_path is None:
            config.load_kube_config()
        else:
            config.load_kube_config(config_file=kubeconfig_path)
    except config.ConfigException as e:
        try:
            config.load_incluster_config()
        except config.ConfigException as ee:
            error_msg = (
                "Failed to load kubeconfig. "
                "Ensure you have a valid kubeconfig file or are running inside a Kubernetes cluster."
            )
            raise RuntimeError(error_msg) from ee
    except Exception as e:
        error_msg = f"Unexpected error while loading kubeconfig: {str(e)}"
        raise RuntimeError(error_msg) from e