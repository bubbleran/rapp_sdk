"""
Refer to the API reference in the Developer Guide of BubbleRAN Open Documentation
for detailed information about these types.
"""
from typing import Optional, List, Dict, Any, Literal, Union, Annotated
from pydantic import Field, IPvAnyAddress, field_validator, model_validator, StringConstraints
from .network_types import (
    AuthenticationKey,
    FullModelName,
    FullNameTag,
    IMSI,
    LinuxInterfaceName,
    MIMOLayers,
    NameTag,
    OperatorParameterConcealed,
    SD,
    Scheduling,
    SequenceNumber,
    SnakeModel,
    SST,
)

DeploymentType = Literal["quectel", "external", "l2-sim", "rf-sim", "zmq", "trx-ip", "backhaul"]
Stack = Literal["4g-sa", "4g-nsa", "5g-sa", "5g-nsa", "4g-5g"]
NetworkMode = Literal["IPv4", "IPv6", "IPv4v6", "Ethernet", "Unstructured"]
ReadinessMethod = Literal["ping"]
ReadinessTarget = Literal["gateway", "google-ip", "google-dns", "kubernetes"]
TermRadioDevice = Literal[
    "rf-sim",
    "l2-sim",
    "zmq",
    "uhd-b200",
    "uhd-n300",
    "uhd-n310",
    "uhd-x300",
    "uhd-x310",
    "amr-sdr50",
    "amr-sdr100",
    "trx-ip",
]
ChannelModel = Literal["AWGN", "Rayleigh1", "Rayleigh8", "Rice1", "Rice8", "TDL_A", "TDL_B", "TDL_C", "TDL_D", "TDL_E"]
USRPSource = Literal["internal", "external", "gpsdo"]
PacketFilterDirection = Literal["downlink", "uplink", "bidirectional"]
PIN = Annotated[str, StringConstraints(pattern=r'^(([0-9]{4})|NULL)$')]
QFI = Annotated[int, Field(ge=0, le=63)]
FiveQI = Annotated[int, Field(ge=0, le=255)]


# Athena's mutating webhook stores network-mode in uppercase (IPV4), so map both forms back to the SDK values.
def _normalize_network_mode(v):
    mapping = {
        "ipv4": "IPv4",
        "ipv6": "IPv6",
        "ipv4v6": "IPv4v6",
        "ethernet": "Ethernet",
        "unstructured": "Unstructured",
    }
    v_str = str(v).lower()
    normalized = mapping.get(v_str, None)
    if not normalized:
        raise ValueError(f"Invalid network-mode: {v_str}")
    return normalized


class ResDevice(SnakeModel):
    name: str
    units: Union[int, str]


class ContainerDefinition(SnakeModel):
    image: str
    command: Optional[List[str]] = None
    devices: Optional[List[ResDevice]] = None
    env: Optional[Dict[str, str]] = None

TermId = NameTag

class TermDesc(SnakeModel):
    vendor: NameTag
    stack: Stack
    model: FullModelName
    scheduling: Optional[Scheduling] = None
    post_configuration: Optional[Dict[str, str]] = Field(default_factory=dict, alias="post-configuration")
    profiles: Optional[List[str]] = None


class TermIdentity(SnakeModel):
    imsi: IMSI
    pin: Optional[PIN] = None
    opc: OperatorParameterConcealed
    key: AuthenticationKey
    sqn: Optional[SequenceNumber] = None
    # Deprecated: use TerminalSpec.ue_count, which applies to every multi-UE deployment mode.
    amr_ue_count: Optional[int] = Field(None, ge=1, alias="amr-ue-count")


class TermSlice(SnakeModel):
    """Single-slice shorthand of a Terminal: one slice with one PDU session and the default QoS flow."""
    dnn: NameTag
    network_mode: NetworkMode = Field(..., alias="network-mode")
    service_type: SST = Field(..., alias="service-type")
    differentiator: SD

    @field_validator("network_mode", mode="before")
    def normalize_network_mode(cls, v):
        return _normalize_network_mode(v)


class TermIMS(SnakeModel):
    tel: str


class BitRate(SnakeModel):
    """Bit rate in bits per second."""
    downlink: int = Field(..., ge=0)
    uplink: int = Field(..., ge=0)


class ARP(SnakeModel):
    """
    Allocation and Retention Priority (ARP) of a QoS flow.

    Attributes:
    priority_level: Priority Level of the flow, the lowest value being the highest priority.
    preemption_capability: True maps to MAY_PREEMPT, False to NOT_PREEMPT.
    preemption_vulnerability: True maps to PREEMPTABLE, False to NOT_PREEMPTABLE.
    """
    priority_level: int = Field(..., ge=1, le=15, alias="priority-level")
    preemption_capability: bool = Field(..., alias="preemption-capability")
    preemption_vulnerability: bool = Field(..., alias="preemption-vulnerability")


class TermPacketFilter(SnakeModel):
    """
    SDF filter in the IPFilterRule syntax of 3GPP TS 29.212.

    Attributes:
    direction: Direction of the traffic the filter applies to.
    description: The filter, for example "permit out udp from any to 10.45.0.0/16 5000-5010".
    """
    direction: PacketFilterDirection
    description: Annotated[str, StringConstraints(min_length=1)]


class TermQoSFlow(SnakeModel):
    """
    QoS flow of a PDU session.

    Attributes:
    qfi: QoS Flow Identifier of the flow.
    five_qi: 5QI of the flow.
    arp: ARP of the flow. Falls back to the CN injector default.
    gbr: GBR of the flow, only for GBR 5QIs.
    mbr: MBR of the flow, only for GBR 5QIs.
    packet_filters: Filters selecting the traffic of a non-default flow.
    """
    qfi: QFI
    five_qi: FiveQI = Field(..., alias="5qi")
    arp: Optional[ARP] = None
    gbr: Optional[BitRate] = None
    mbr: Optional[BitRate] = None
    packet_filters: Optional[List[TermPacketFilter]] = Field(None, alias="packet-filters")


class TermPDUSession(SnakeModel):
    """
    DNN subscription of a slice, and the PDU session the UE opens on it.

    Attributes:
    dnn: DNN of the session.
    network_mode: Session type. Defaults to IPv4.
    ambr: AMBR of the session. Falls back to the CN injector default.
    flows: QoS flows of the session. The first one is the default flow and cannot have packet filters.
           When absent, a single default flow with 5QI 9 is used.
    establish: Whether the UE opens this session at attach, or only subscribes to it in the CN.
               Defaults to true for the first session of the first slice, and false for the others.
    """
    dnn: NameTag
    network_mode: Optional[NetworkMode] = Field(None, alias="network-mode")
    ambr: Optional[BitRate] = None
    flows: Optional[List[TermQoSFlow]] = None
    establish: Optional[bool] = None

    @field_validator("network_mode", mode="before")
    def normalize_network_mode(cls, v):
        return None if v is None else _normalize_network_mode(v)

    @model_validator(mode="after")
    def check_default_flow(self):
        if self.flows and self.flows[0].packet_filters:
            raise ValueError("the first (default) flow cannot have packet filters")
        return self


class TermSubscribedSlice(SnakeModel):
    """
    S-NSSAI subscribed by the UE, with its PDU sessions.

    Attributes:
    service_type: SST of the slice.
    differentiator: SD of the slice. Defaults to 0.
    pdu_sessions: PDU sessions of the slice. The first one is the default session of the slice.
    """
    service_type: SST = Field(..., alias="service-type")
    differentiator: Optional[SD] = None
    pdu_sessions: List[TermPDUSession] = Field(..., min_length=1, alias="pdu-sessions")


class TermUE(SnakeModel):
    """
    Overrides the Terminal defaults for a range of UEs, starting at index.
    A field set here replaces the default for every UE of the range, a field not set keeps the default.

    Attributes:
    index: Index of the first UE of the range, 0-based.
           When absent, the range starts right after the previous entry, or at 0 for the first entry.
    count: Number of consecutive UEs covered by this entry. Defaults to 1.
    imsi: IMSI of the first UE of the range, the others use consecutive IMSIs.
    key, opc, sqn, pin: Replace the Identity fields for the range.
    slices: Replace the default slices for the range. They are not merged with the defaults.
    ims: Replaces the IMS information for the range.
    """
    index: Optional[int] = Field(None, ge=0)
    count: Optional[int] = Field(None, ge=1)
    imsi: Optional[IMSI] = None
    key: Optional[AuthenticationKey] = None
    opc: Optional[OperatorParameterConcealed] = None
    sqn: Optional[SequenceNumber] = None
    pin: Optional[PIN] = None
    slices: Optional[List[TermSubscribedSlice]] = Field(None, min_length=1)
    ims: Optional[TermIMS] = None


class TermRFSim(SnakeModel):
    """
    RF simulator options of a Terminal. Only valid with the rf-sim device.

    Attributes:
    channel_model: Enables the rfsim channel model with this model. When absent, no channel model is applied.
    save_iq: Records the IQ samples into the logs directory.
    """
    channel_model: Optional[ChannelModel] = Field(None, alias="channel-model")
    save_iq: Optional[bool] = Field(None, alias="save-iq")


class TermZMQ(SnakeModel):
    """ZeroMQ options of a Terminal. Only valid with the zmq device. The ports follow the formation, so there are no settings."""
    pass


class TermUSRP(SnakeModel):
    """
    Options of a Terminal running on a USRP. Only valid with the uhd-* devices.

    Attributes:
    serial: Pins a specific USRP. When absent, any free device of the requested type is allocated.
    clock_source: Clock source of the USRP. Defaults to internal.
    time_source: Time source of the USRP. Defaults to internal.
    three_quarter_sampling: Enables the three-quarter sampling rate. Defaults to true.
    fo_compensation: Enables the UE frequency offset compensation. Defaults to true.
    """
    serial: Optional[str] = None
    clock_source: Optional[USRPSource] = Field(None, alias="clock-source")
    time_source: Optional[USRPSource] = Field(None, alias="time-source")
    three_quarter_sampling: Optional[bool] = Field(None, alias="three-quarter-sampling")
    fo_compensation: Optional[bool] = Field(None, alias="fo-compensation")


class TermRadio(SnakeModel):
    device: Optional[TermRadioDevice] = None
    rf_sim: Optional[TermRFSim] = Field(None, alias="rf-sim")
    zmq: Optional[TermZMQ] = None
    usrp: Optional[TermUSRP] = None
    formation: Optional[MIMOLayers] = None
    rx_gain: Optional[str] = Field(None, alias="rx-gain")
    tx_gain: Optional[str] = Field(None, alias="tx-gain")
    bands: List[str]

    @model_validator(mode="after")
    def check_device_options(self):
        if self.rf_sim is not None and self.device not in (None, "rf-sim"):
            raise ValueError("radio.rf-sim requires radio.device rf-sim")
        if self.zmq is not None and self.device != "zmq":
            raise ValueError("radio.zmq requires radio.device zmq")
        if self.usrp is not None and not (self.device or "").startswith("uhd-"):
            raise ValueError("radio.usrp requires a uhd-* radio.device")
        return self


class ReadinessCheck(SnakeModel):
    method: ReadinessMethod
    target: Optional[ReadinessTarget] = None
    ip: Optional[IPvAnyAddress] = None
    interface_name: Optional[LinuxInterfaceName] = Field(None, alias="interface-name")


class TerminalSpec(TermDesc):
    """
    TerminalSpec defines the desired state of Terminal.

    Attributes:
    slice: Single-slice shorthand. Mutually exclusive with slices; one of the two is required.
    slices: Subscribed slices of every UE, with their PDU sessions and QoS flows. The first slice is the default one.
    ue_count: Number of UEs run by this Terminal. UE i uses identity.imsi + i and shares every other identity field.
              When absent, it is 1, or the highest index covered by ue_list plus one.
    ue_list: Overrides of the identity, slices or IMS of selected UEs. Entries cover disjoint index ranges.
    """
    applications: Optional[Dict[str, ContainerDefinition]] = None
    slice: Optional[TermSlice] = None
    slices: Optional[List[TermSubscribedSlice]] = Field(None, min_length=1)
    ue_count: Optional[int] = Field(None, ge=1, alias="ue-count")
    ue_list: Optional[List[TermUE]] = Field(None, alias="ue-list")
    target_cores: List[FullNameTag] = Field(..., alias="target-cores")
    preferred_access: Optional[FullNameTag] = Field(None, alias="preferred-access")
    identity: TermIdentity
    ims: Optional[TermIMS] = None
    radio: TermRadio
    readiness_check: Optional[ReadinessCheck] = Field(None, alias="readiness-check")

    @model_validator(mode="after")
    def check_slice_or_slices(self):
        if (self.slice is None) == (self.slices is None):
            raise ValueError("exactly one of slice or slices is required")
        return self


class TermUEStatus(SnakeModel):
    """
    Observed state of one UE of a Terminal.

    Attributes:
    index: Index of the UE within the Terminal, 0-based.
    imsi: IMSI of the UE.
    interface: Tunnel interface of the UE inside the Terminal Pod.
    ips: IPs of the established PDU sessions, keyed by DNN.
    registered: Whether the UE is registered to the CN.
    reachable: Whether the readiness target answers a ping sent from the tunnel interface of the UE.
    """
    index: int
    imsi: IMSI
    interface: Optional[str] = None
    ips: Optional[Dict[str, str]] = None
    registered: bool = False
    reachable: bool = False


class TerminalStatus(SnakeModel):
    connected_cores: Optional[Dict[FullNameTag, bool]] = Field(default_factory=dict, alias="connected-cores")
    element: Optional[str] = None
    element_status: bool = Field(default=False, alias="element-status")
    conditions: Optional[List[Dict[str, Any]]] = None
    ue_count: Optional[int] = Field(None, alias="ue-count")
    ready_ues: Optional[int] = Field(None, alias="ready-ues")
    ues: Optional[List[TermUEStatus]] = None
