from typing import Optional, List, Dict, Any, Literal
from pydantic import Field, IPvAnyAddress, field_validator
from .network_types import (
    AuthenticationKey,
    Cell,
    FullModelName,
    FullNameTag,
    IMSI,
    LinuxInterfaceName,
    NameTag,
    OperatorParameterConcealed,
    SD,
    Scheduling,
    SequenceNumber,
    SnakeModel,
)

DeploymentType = Literal["quectel", "external", "l2-sim", "rf-sim", "backhaul"]
Stack = Literal["4g-sa", "4g-nsa", "5g-sa", "5g-nsa", "4g-5g"]
NetworkMode = Literal["IPv4", "IPv6", "IPv4v6", "Ethernet", "Unstructured"]
SST = Literal["eMBB", "URLLC", "mMTC"]
ReadinessMethod = Literal["ping"]
ReadinessTarget = Literal["gateway", "google-ip", "google-dns", "kubernetes"]


class ContainerDefinition(SnakeModel):
    # Define your container structure here
    image: str

TermId = NameTag
    
class TermDesc(SnakeModel):
    vendor: NameTag
    stack: Stack
    model: FullModelName
    scheduling: Optional[Scheduling] = None
    post_configuration: Optional[Dict[str, str]] = Field(default_factory=dict, alias="post-configuration")


class TermIdentity(SnakeModel):
    imsi: IMSI
    pin: Optional[str] = None
    opc: OperatorParameterConcealed
    key: AuthenticationKey
    sqn: Optional[SequenceNumber] = None


class TermSlice(SnakeModel):
    dnn: NameTag
    network_mode: NetworkMode = Field(..., alias="network-mode")
    service_type: SST = Field(..., alias="service-type")
    differentiator: SD

    # TODO: Why Athena response IPV4 instead of IPv4?
    @field_validator("network_mode", mode="before")
    def normalize_network_mode(cls, v):
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
    
    @field_validator("service_type", mode="before")
    def normalize_service_type(cls, v):
        mapping = {
            "embb": "eMBB",
            "urllc": "uRLLC",
            "mmtc": "mMTC",
        }
        v_str = str(v).lower()
        normalized = mapping.get(v_str, None)
        if not normalized:
            raise ValueError(f"Invalid service-type: {v_str}")
        return normalized


class TermIMS(SnakeModel):
    tel: str


class TermRadio(SnakeModel):
    bands: List[str]
    access: Optional[FullNameTag] = None
    cells: Optional[List[Cell]] = None


class ReadinessCheck(SnakeModel):
    method: ReadinessMethod
    target: Optional[ReadinessTarget] = None
    ip: Optional[IPvAnyAddress] = None
    interface_name: Optional[LinuxInterfaceName] = Field(None, alias="interface-name")


class TerminalSpec(TermDesc):
    applications: Optional[Dict[str, ContainerDefinition]] = None
    slice: TermSlice
    target_cores: List[FullNameTag] = Field(..., alias="target-cores")
    preferred_access: Optional[FullNameTag] = Field(None, alias="preferred-access")
    identity: TermIdentity
    ims: Optional[TermIMS] = None
    radio: TermRadio
    readiness_check: Optional[ReadinessCheck] = Field(None, alias="readiness-check")


class TerminalStatus(SnakeModel):
    connected_cores: Optional[Dict[FullNameTag, bool]] = Field(default_factory=dict, alias="connected-cores")
    element: Optional[str] = None
    element_status: bool = Field(default=False, alias="element-status")
