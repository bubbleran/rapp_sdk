from kubernetes import client, config
import ipaddress
import re
from ..common import (
    load_kubeconfig,
    get_cr,
    list_cr,
    apply_cr,
    delete_cr,
    exec_in_deployment,
    KubectlError,
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
        

    def test_throughput(
        self,
        terminal_id: TermId,
        direction: Literal["dl", "ul"] = "dl",
        destination: str = "gateway",
        args: List[str] = [],
    ) -> KubectlOperationResult:
        """Run an iperf throughput test from the terminal.

        Parameters:
            terminal_id (TermId): The name of the terminal (e.g. ``"ue02"``).
            direction (Literal["dl", "ul"]): ``"dl"`` adds ``--reverse`` so the server
                sends toward the UE; ``"ul"`` sends from the UE toward the server.
            destination (str): Target IP address or ``"gateway"`` to resolve the
                gateway automatically as the first host of the PDU-session subnet.
            args (List[str]): Extra iperf flags appended after ``--client <ip>``,
                e.g. ``["--time", "30", "--interval", "1", "--bandwidth", "10M"]``.

        Returns:
            KubectlOperationResult: On success, ``data`` contains:

            - ``output`` — raw iperf output string

        Examples:
        ```python
        from br_rapp_sdk import OAMServices

        oam = OAMServices()
        result = oam.terminal.test_throughput("ue02", args=["--time", "10", "--interval", "1"])
        if result.status == "success":
            print(result.data["output"])
        else:
            print("Error:", result.error)
        ```
        """
        try:
            t_idx = next(i for i, a in enumerate(args) if a in ("-t", "--time"))
            exec_timeout = int(args[t_idx + 1]) + 30
        except (StopIteration, (IndexError, ValueError)):
            exec_timeout = 90

        get_result = get_cr(
            kube_api_instance=self._api,
            group=self._group,
            version=self._version,
            plural=self._plural,
            namespace=self.namespace,
            name=terminal_id,
        )
        if get_result.status != 'success':
            return get_result

        raw = get_result.data.get('item', {})
        element = raw.get('status', {}).get('element')
        if not element:
            return KubectlOperationResult(
                status='error', operation='exec',
                error=KubectlError(code=400, message=f"Terminal '{terminal_id}' has no element assigned. Is it connected?"),
            )

        interface = raw.get('spec', {}).get('readiness-check', {}).get('interface-name')
        if not interface:
            return KubectlOperationResult(
                status='error', operation='exec',
                error=KubectlError(code=400, message=f"Terminal '{terminal_id}' has no readiness-check interface-name configured."),
            )

        ip_result = exec_in_deployment(
            namespace=self.namespace,
            deployment_name=element,
            command=["ip", "address", "show", interface],
        )
        if ip_result.status != 'success':
            return ip_result

        ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+/\d+)', ip_result.data.get('output', ''))
        if not ip_match:
            return KubectlOperationResult(
                status='error', operation='exec',
                error=KubectlError(code=500, message=f"Could not find an IPv4 address on interface '{interface}'."),
            )

        iface_addr = ipaddress.IPv4Interface(ip_match.group(1))
        bind_ip = str(iface_addr.ip)
        dest_ip = str(iface_addr.network.network_address + 1) if destination == "gateway" else destination

        iperf_cmd = ["iperf", "--bind", bind_ip, "--enhanced", "--client", dest_ip]
        if direction == "dl":
            iperf_cmd.append("--reverse")
        iperf_cmd.extend(args)

        iperf_result = exec_in_deployment(
            namespace=self.namespace,
            deployment_name=element,
            command=iperf_cmd,
            timeout=exec_timeout,
        )
        return iperf_result

    def test_connectivity(
        self,
        terminal_id: TermId,
        destination: str = "gateway",
        args: List[str] = [],
    ) -> KubectlOperationResult:
        """Test connectivity from the terminal by pinging the destination.

        Parameters:
            terminal_id (TermId): The name of the terminal (e.g. ``"ue02"``).
            destination (str): Target IP address or ``"gateway"`` to auto-resolve
                from the PDU-session subnet.
            args (List[str]): Extra ping flags, e.g. ``["-c", "4", "-W", "2"]``.
                Defaults to ``["-c", "3"]`` if ``"-c"`` is not provided.

        Returns:
            KubectlOperationResult: On success, ``data`` contains:

            - ``output`` — raw ping output string
            - ``connected`` — ``True`` if at least one packet was received, ``False`` otherwise

        Examples:
        ```python
        from br_rapp_sdk import OAMServices

        oam = OAMServices()
        result = oam.terminal.test_connectivity("ue02")
        if result.status == "success":
            print("Connected:", result.data["connected"])
            print(result.data["output"])
        else:
            print("Error:", result.error)
        ```
        """
        try:
            count = int(args[args.index("-c") + 1])
        except (ValueError, IndexError):
            count = 3
            args = ["-c", "3"] + args
        exec_timeout = count + 10

        get_result = get_cr(
            kube_api_instance=self._api,
            group=self._group,
            version=self._version,
            plural=self._plural,
            namespace=self.namespace,
            name=terminal_id,
        )
        if get_result.status != 'success':
            return get_result

        raw = get_result.data.get('item', {})
        element = raw.get('status', {}).get('element')
        if not element:
            return KubectlOperationResult(
                status='error', operation='exec',
                error=KubectlError(code=400, message=f"Terminal '{terminal_id}' has no element assigned. Is it connected?"),
            )

        interface = raw.get('spec', {}).get('readiness-check', {}).get('interface-name')
        if not interface:
            return KubectlOperationResult(
                status='error', operation='exec',
                error=KubectlError(code=400, message=f"Terminal '{terminal_id}' has no readiness-check interface-name configured."),
            )

        if destination == "gateway":
            ip_result = exec_in_deployment(
                namespace=self.namespace,
                deployment_name=element,
                command=["ip", "address", "show", interface],
            )
            if ip_result.status != 'success':
                return ip_result

            ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+/\d+)', ip_result.data.get('output', ''))
            if not ip_match:
                return KubectlOperationResult(
                    status='error', operation='exec',
                    error=KubectlError(code=500, message=f"Could not find an IPv4 address on interface '{interface}'."),
                )
            dest_ip = str(ipaddress.IPv4Interface(ip_match.group(1)).network.network_address + 1)
        else:
            dest_ip = destination

        ping_cmd = ["ping", "-I", interface] + args + [dest_ip]

        ping_result = exec_in_deployment(
            namespace=self.namespace,
            deployment_name=element,
            command=ping_cmd,
            timeout=exec_timeout,
        )
        if ping_result.status == 'success':
            output = ping_result.data.get('output', '')
            loss_match = re.search(r'(\d+)% packet loss', output)
            connected = loss_match is not None and int(loss_match.group(1)) < 100
            ping_result.data.update({
                'connected': connected,
            })
        return ping_result

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
