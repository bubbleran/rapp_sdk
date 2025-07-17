from typing import (
    Any,
    Dict,
    List,
    Literal,
    Optional,
    Self,
    Union,
    Annotated,
)
from pydantic import BaseModel, Field, ConfigDict, field_validator, StringConstraints
import yaml

# This model is used to ensure that the field names are in snake_case
# and to provide a consistent way to handle the model's configuration.
# The `model_dump` method is overridden to exclude None and empty values by default.
class SnakeModel(BaseModel):
    model_config = ConfigDict(validate_by_name=True)

    def yaml(self) -> str:
        return yaml.dump(self.model_dump(), sort_keys=False)

    def load_yaml(self, yaml_str: str) -> None:
        data = yaml.safe_load(yaml_str)
        self.__dict__.update(data)

    def model_dump(self, *args: Any, **kwargs: Any) -> dict:
        kwargs.setdefault("exclude_none", True)
        raw = super().model_dump(*args, **kwargs)
        return self._exclude_empty(raw)

    def _exclude_empty(self, data: Any) -> Any:
        if isinstance(data, dict):
            return {k: self._exclude_empty(v) for k, v in data.items()
                    if v not in (None, {}, [], ())}
        elif isinstance(data, list):
            return [self._exclude_empty(v) for v in data
                    if v not in (None, {}, [], ())]
        return data


NetworkPart = Literal["access", "core", "edge"]

DeploymentType = Literal["quectel", "external", "l2-sim", "rf-sim", "backhaul"]
Stack = Literal["4g-sa", "4g-nsa", "5g-sa", "5g-nsa", "4g-5g"]
NetworkMode = Literal["IPv4", "IPv6", "IPv4v6", "Ethernet", "Unstructured"]
ServiceType = Literal["eMBB", "URLLC", "mMTC", "MIoT"]
ReadinessMethod = Literal["ping"]
ReadinessTarget = Literal["gateway", "google-ip", "google-dns", "kubernetes"]


# Identity and security placeholders
#TODO: add more specific types for these fields
NameTag = Annotated[
    str,
    StringConstraints(
        pattern=r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?$',
        min_length=1,
        max_length=63,
    )
]

FullNameTag = Annotated[
    str,
    StringConstraints(
        pattern=r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?\.[a-z0-9]([-a-z0-9]*[a-z0-9])?$',
        min_length=3,
        max_length=127,
    )
]

FullModelName = Annotated[
    str,
    StringConstraints(
        pattern=r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?/([a-z0-9]([-a-z0-9]*[a-z0-9])?)$',
        min_length=3,
        max_length=127,
    )
]

NetworkId = NameTag
IMSI = str
OperatorParameterConcealed = str
AuthenticationKey = str
SequenceNumber = str
LinuxInterfaceName = str
SD = int

AccessNetworkId = FullNameTag
CoreNetworkId = FullNameTag
EdgeNetworkId = FullNameTag

class SliceDesc(SnakeModel):
    plmn: str
    dnn: NameTag
    network_mode: NetworkMode = Field(..., alias="network-mode")
    service_type: ServiceType = Field(..., alias="service-type")
    differentiator: Union[int, str]
    ipv4_range: Optional[str] = Field(None, alias="ipv4-range")
    ipv6_range: Optional[str] = Field(None, alias="ipv6-range")

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
            "urllc": "URLLC",
            "mmtc": "mMTC",
            "miot": "MIoT",
        }
        v_str = str(v).lower()
        normalized = mapping.get(v_str, None)
        if not normalized:
            raise ValueError(f"Invalid service-type: {v_str}")
        return normalized
    
#TODO: 
class Scheduling(SnakeModel):
    # Define actual structure if needed
    pass

#TODO: NOT TESTED
class SliceFilters(SnakeModel):
    ids: Optional[List[int]] = None
    plmn: Optional[List[str]] = None
    dnn: Optional[List[NameTag]] = None
    service_type: Optional[List[str]] = Field(None, alias="service-type")


class NetworkDesc(SnakeModel):
    name: NameTag
    stack: Stack
    model: FullModelName
    scopes: Optional[List[NameTag]] = Field(default_factory=lambda: ["default"])
    profiles: Optional[List[str]] = None
    scheduling: Optional[Scheduling] = None
    labels: Optional[Dict[str, str]] = None
    annotations: Optional[Dict[str, str]] = None
    filters: Optional[SliceFilters] = None
    post_configuration: Optional[Dict[str, str]] = Field(None, alias="post-configuration")

# Access
class TDDConfig(SnakeModel):
    period: str
    dl_slots: int = Field(..., alias="dl-slots")
    dl_symbols: int = Field(..., alias="dl-symbols")
    ul_slots: int = Field(..., alias="ul-slots")
    ul_symbols: int = Field(..., alias="ul-symbols")


class Cell(SnakeModel):
    band: str
    arfcn: int
    bandwidth: str
    subcarrier_spacing: str = Field(..., alias="subcarrier-spacing")
    tdd_config: Optional[TDDConfig] = Field(None, alias="tdd-config")


class AccessRadio(SnakeModel):
    device: str


class AccessIdentity(SnakeModel):
    an_id: Optional[int] = Field(None, alias="an-id")
    tracking_area: Optional[int] = Field(None, alias="tracking-area")


class AccessNetworkSpec(NetworkDesc):
    radio: AccessRadio
    identity: Optional[AccessIdentity] = None
    cells: List[Cell]
    core_networks: List[FullNameTag] = Field(..., alias="core-networks")
    controller: Optional[FullNameTag] = None


# Core
class CoreIdentity(SnakeModel):
    region: Optional[int]
    cn_group: Optional[int] = Field(None, alias="cn-group")
    cn_id: Optional[int] = Field(None, alias="cn-id")


class CoreNetworkSpec(NetworkDesc):
    identity: Optional[CoreIdentity] = None
    controller: Optional[FullNameTag] = None


# Edge
class EdgeNetworkSpec(NetworkDesc):
    pass


# DNS
class DNSRecord(SnakeModel):
    default: Optional[str] = None
    secondary: Optional[str] = None


class DNSList(SnakeModel):
    ipv4: Optional[DNSRecord] = None


# Full Spec
class NetworkSpec(SnakeModel):
    slices: List[SliceDesc]
    access: Optional[List[AccessNetworkSpec]] = None
    core: Optional[List[CoreNetworkSpec]] = None
    edge: Optional[List[EdgeNetworkSpec]] = None
    dns: Optional[DNSList] = None

