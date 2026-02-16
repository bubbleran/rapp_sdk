"""
Refer to the API reference in the Developer Guide of BubbleRAN Open Documentation
for detailed information about these types.
"""
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
    """ 
    SliceDesc describes an End-to-End (E2E) 3GPP slice.
    
    Attributes:
    plmn: The PLMN of the slice composed of the concatenation of the MNC and MCC in five digits.
    dnn: The DNN (Data Network Name) of the slice, equivalent to APN (Access Point Name) in the context of LTE.
    network_mode: The NetworkMode associated with this 3GPP E2E slice.
    service_type: The ServiceType of the slice, which could be defined in the string format of the standard or the integer format. The valid string values are "eMBB", "URLLC", "MIoT", "V2X", "HMTC", and "HDLLC".
    differentiator: The Differentiator ID of the slice.
	        This value is preferred to be in hexadecimal format, but could be any numerical non-negative value.
	        The value 0x000000 is reserved for the default slice and 0xFFFFFF for the no slice selection according to the 3GPP specifications.
    ipv4_range: The IPv4Range of addresses for this 3GPP E2E slice. If the NetworkMode is IPv4 or IPv4v6, this field is mandatory.
    ipv6_range: The IPv6Range of addresses for this 3GPP E2E slice. If the NetworkMode is IPv6 or IPv4v6, this field is mandatory.
    """
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
    """
    SliceFilters are helpers to filter slices for a network.
    
    Attributes:
    ids: Optional list of slice IDs to filter.
    plmn: Optional list of PLMN IDs to filter.
    dnn: Optional list of DNNs to filter.
    service_type: SST filtering for the slices.
    """
    ids: Optional[List[int]] = None
    plmn: Optional[List[str]] = None
    dnn: Optional[List[NameTag]] = None
    service_type: Optional[List[str]] = Field(None, alias="service-type")


class NetworkDesc(SnakeModel):
    """ 
    NetworkDesc is the description of a network in the most general sense, either AccessNetwork, CoreNetwork, or EdgeNetwork.
    
    Attributes:
    name: Name of the network section.
    stack: Stack of the network to be deployed.
	    The value mappings are as the followings:
	    4g-sa    Standalone LTE, 4G
	    4g-nsa   Non-Standalone LTE, 4G
	    5g-sa    5G StandAlone, 5G-SA
	    5g-nsa   5G Non-StandAlone, 5G-NSA
	    4g-5g    Simultaneous 4G and 5G cells
    model: Composition Model used to deploy the network.
    scope: Scopes are optional logical separators.
    profiles: Profiles are arbitrary, vendor-defined options that could be disabled or enabled to add or remove features from a particular Workload.
    scheduling: Optional Scheduling Constraints for the Network's pods, based on Kubernetes logic.
    labels: Optional Labels to be associated with all the resources of this Network, useful for multi-x dimension selection, customized scheduling, or other labeling needs.
    annotations: Optional Annotations to be associated with the pods of this network, useful for scoping, custom variable updates, and environment editing.
    filters: Filters used to pick the slices assigned to this network and by default to all of its network functions.
    post_configuration: PostConfiguration are generic JSON-path key and value pairs that are used to customize the configuration after the Manager has decided on the final configuration.
    """
    
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
    """
    TDDConfigurationNR represents the TDD configuration for the NR bands.
    In 3GPP TS 38.213, two TDD patterns (pattern1 and pattern2) are allowed but in this package, we only support
    pattern1.

    Attributes:
    period: PeriodicityUs is the sub-frame periodicity in microseconds.
    dl_slots: SlotsDL is the number of downlink slots.
    dl_symbols: SymbolsSpecialDL is the number of symbols in downlink in the special slot.
    ul_slots: SlotsUL is the number of uplink slots.
    ul_symbols: SymbolsSpecialUL is the number of symbols in uplink in the special slot
    """
    period: str
    dl_slots: int = Field(..., alias="dl-slots")
    dl_symbols: int = Field(..., alias="dl-symbols")
    ul_slots: int = Field(..., alias="ul-slots")
    ul_symbols: int = Field(..., alias="ul-symbols")


class Cell(SnakeModel):
    """
    Cell structure defines an EUTRA or NR cell, with all of its parameters.
    
    Attributes:
    band: Band to be used to configure AN and its radio devices.
        It supports both LTE notation and NR notation.
        To use LTE bands, prepend the band with "b" and to use NR bands, prepend the band with "n".
        Trirematics supports both FR1 and FR2, however whether AN is able to operate with FR2 depends on the vendor.
        The Band also determines the duplex mode and valid Bandwidth values as given by standard.
        The configurations not respecting the 3GPP standard should be rejected.
        For a complete list of supported bands, see the following links:
        LTE: https://en.wikipedia.org/wiki/LTE_frequency_bands
        NR: https://en.wikipedia.org/wiki/5G_NR_frequency_bands
    bandwidth: Bandwidth of the used channel in MHz, yet for clarity "MHz" should be appended for each value.
	        Having the Bandwidth and SubcarrierSpacing defined, the Number of Resource Blocks (NRBs) is computed internally, based on FR1 or FR2.
    arfcn: Absolute Radio-Frequency Channel Number (ARFCN) uniquely defines the UL and DL frequencies that AN operates on.
	        The values should be compatible with 3GPP standard.
	        Depending on the Stack, either EARFCN or NR-ARFCN should be used.
	        The values are most likely fed to the workload as it is, but they might be translated to frequency values in the configurator plugins.
    subcarrier_spacing: SubcarrierSpacing is to define SCS and numerology. The values are defined in kHz, but for clarity the term "kHz"
	            should be appended. For different Stack and Band values, the user should only use the standard values.
	            To remain compatible with 4G LTE, this parameter is kept optional with 15kHz as default.
    tdd_config: TDDConfig is used to define the TDD configuration of the cell.
	            This configuration is only accepted if the Band is in the TDD duplex mode.
    """
    band: str
    arfcn: int
    bandwidth: str
    subcarrier_spacing: str = Field(..., alias="subcarrier-spacing")
    tdd_config: Optional[TDDConfig] = Field(None, alias="tdd-config")


class AccessRadio(SnakeModel):
    """
    AccessRadio structure is a grouping for radio-related parameters of the AccessNetwork (AN).
    
    Attributes:
        device: Device determines what type of radio devices should be configured to be used for this instance of AN.
	            When using rf-sim is used, no particular radio device is attached to AN, but it would be configured to run in
	            simulator mode.
	            The support for Amarisoft UHD N310, UHD X300, UHD X310, L2-SIM, O-RAN 7.2 are defined for forward compatibility,
	            but are not yet verified officially yet.
        Antenna: Not implemented yet.
    """
    device: str


class AccessIdentity(SnakeModel):
    """
    AccessIdentity determines the identity of AN, specifically, the AN-ID and TAC.
    By the standard the NR Cell Identity (NCI) could be of 36 bits, composed of between 22 and 32 bits of gNB Identity
    and the rest for the Cell Identity.
    This variety is not respected in here, but only fixed 8 bits for Cell Identity is allowed.
    Thus, the AccessNetworkID field could only have 28 bits and supports maximum 256 cells per gNB.
    This should be large enough for most implementations and use cases.
    The same applies to LTE, whereas by the standard the eNB-ID could be either 20 or 28 bits.
    Picking 28 bits seems to be a reasonable unifier.
    Thus, the E-UTRAN Cell Global Identity (ECGI) composed of 28 bits eNB-ID and 8 bits for the Cell Identity.
    | gNB ID (fixed to 28 bits)        | gNB Cell ID (fixed to 8 bits) |
    | 0000000000000000000000000000     | 00000000                      |
    | 0000000000000000000000000000     | 00000000                      |
    | eNB ID (fixed choice of 28 bits) | eNB Cell ID (8 bits)          |
    Both the gNB ID and the eNB ID map to AccessNetworkID field and the Cell configuration is done during configuring
    the AN.

    Attributes:
        an_id: AccessNetworkID is the unique identifier of AN, preferably in the Hexadecimal presentation.
	           The ID is supposed to be unique across the entire network.
	           Otherwise, the controllers and/or CNs would panic receiving the same ID from multiple ANs.
	           However, the naming convention of Trirematics also includes the workload name as well as the network name.
	           Per each Element defined in the Composition Model of a network, the Elements with this formula:
	           <model-name>.<network-section-name>.<network-name>
	           In this way the names are globally unique, while having semantic meaning.
	           If the AccessNetworkID is not provided, the Operator will generate a random ID within the range.
	           It is the responsibility of the Plugins provided by the vendors to generate and set the cell IDs.
        tracking_area: TrackingArea associated with AN.
	                   If the TrackingArea is not provided, the Operator will use the default value of 1.
    """
    an_id: Optional[int] = Field(None, alias="an-id")
    tracking_area: Optional[int] = Field(None, alias="tracking-area")


class AccessNetworkSpec(NetworkDesc):

    """
    AccessNetwork defines an Access Network (AN) to be used for deployment.
    
    Attributes:
        NetworkDesc fields: name, stack, model, scopes, profiles, scheduling, labels, annotations, filters, post_configuration
        radio: Radio defines the radio device section for the AN.
        identity: Identity represents the identity of the AN.
	              If not provided, then a unique identity is generated for the TAC 1.
        cells: Cells define the cells of the Access Network, regardless of the RAT.
	            The RAT is detected by the Band: if the band is in the LTE band list, then the RAT is LTE, otherwise it is NR.
	            Having multiple cells is necessary for supporting NSA, hand over, and carrier aggregation deployments.
	            The cell IDs are determined by the order of the cells in the list.
        core_networks: The list of CoreNetworks that this instance of AN should connect to.
	                   Should at least contain one entry.
	                   The format should look like the following:
	                   <network-section-name>.<network-name>
        controller: The Controller that this AN is associated with. If empty, no controller is used.
    """
    radio: AccessRadio
    identity: Optional[AccessIdentity] = None
    cells: List[Cell]
    core_networks: List[FullNameTag] = Field(..., alias="core-networks")
    controller: Optional[FullNameTag] = None


# Core
class CoreIdentity(SnakeModel):
    """
    CoreIdentity determines the identity of CN, specifically in 5G format.
    The CN-ID is made out of the three parameters defined in this structure, and it should be unique across the entire
    network.
    Otherwise, the controllers and/or ANs would panic receiving the same ID from multiple CNs.
    The CoreIdentity definition follows 5G standards. To have a 4G network identifier one must do the translation
    according to the standard:
    | AMF Region ID (8 bits) | AMF Set ID (10 bits) | AMF ID (6 bits)  |
    | 00000000               |    00000000   00     |      000000      |
    | 00000000                    00000000 | 00            000000      |
    | MME Group ID (16 bits)               | MME Code (8 bits)         |
    
    Attributes:
    region: Region defines the region of CNs. One should manually transform 4G LTE CN-IDs to compatible 5G CN-IDs.
            Equivalent to AMF Region ID in 5G.
            Equivalent to the most-valued 8 bits of the MME GroupID.
	        If the Region is not provided, the Operator will use the default value of 1.
    cn_group: Group defines the group of CNs that are part of the same region, by the 5G standards.
              One should manually transform 4G LTE CN-IDs to compatible 5G CN-IDs.
              Equivalent to AMF Set ID in 5G.
              Equivalent to the concatenation of the least-valued 8 bits of the MME GroupID and the most-valued 2 bits of the MME Code in 4G.
              If the Group is not provided, the Operator will use the default value of 1.
    cn_id: CoreNetworkID is the unique identifier of CN within a Group and Region, preferably in the Hexadecimal presentation.
	       The naming convention of Trirematics also includes the workload name as well as the network name.
	       Per each Element defined in the Composition Model of a network, the Elements with this formula:
	       <model-name>.<network-section-name>.<network-name>
	       In this way the names are globally unique, while having semantic meaning.
	       Equivalent to AMF Pointer in 5G.
	       Equivalent to the least-valued 6 bits of the MME Code in 4G.
	       If the CoreNetworkID is not provided, the Operator will generate a random ID within the range.
    """
    region: Optional[int]
    cn_group: Optional[int] = Field(None, alias="cn-group")
    cn_id: Optional[int] = Field(None, alias="cn-id")


class CoreNetworkSpec(NetworkDesc):
    """
    CoreNetwork defines a Core Network (CN) to be used for deployment.
    
    Attributes:
        NetworkDesc fields: name, stack, model, scopes, profiles, scheduling, labels, annotations, filters, post_configuration
        Identity: Optional CoreIdentity object representing the identity of the CN. If not provided, then a unique identity is generated with default Group, Region, and TAC values.
        Controller: Optional string representing the name of the controller managing this CN. If not provided, then the CN is not associated with any controller.
    """
    identity: Optional[CoreIdentity] = None
    controller: Optional[FullNameTag] = None


# Edge
class EdgeNetworkSpec(NetworkDesc):
    """
    EdgeNetwork defines an Edge Network (EN) to be used for deployment.
    
    Attributes:
        NetworkDesc fields: name, stack, model, scopes, profiles, scheduling, labels, annotations, filters, post_configuration
    """
    pass


# DNS
class DNSRecord(SnakeModel):
    """
    DNSRecord defines a DNS record with Default and Secondary IP addresses.
    This data is passed down to all the UEs.

    Attributes:
        default: Optional string representing the default IP address for the DNS record.
        secondary: Optional string representing the secondary IP address for the DNS record.
    """
    default: Optional[str] = None
    secondary: Optional[str] = None


class DNSList(SnakeModel):
    """
    DNSList defines IPv4 and IPv6 DNS records.
    
    Attributes:
        ipv4: Optional DNSRecord object describing the IPv4 DNS records for the UEs in the network.
        ipv6: Optional DNSRecord object describing the IPv6 DNS records for the UEs in the network.
    """
    ipv4: Optional[DNSRecord] = None
    ipv6: Optional[DNSRecord] = None


# Full Spec
class NetworkSpec(SnakeModel):
    """
    NetworkSpec defines the desired state of Network.

    Attributes:
        slices: List of SliceDesc objects describing the slices in the network.
        access: Optional list of AccessNetworkSpec objects describing the access networks.
        core: Optional list of CoreNetworkSpec objects describing the core networks.
        edge: Optional list of EdgeNetworkSpec objects describing the edge networks.
        dns: Optional DNSList object describing the DNS records for the UEs in the network.
    """
    slices: List[SliceDesc]
    
    access: Optional[List[AccessNetworkSpec]] = None
    core: Optional[List[CoreNetworkSpec]] = None
    edge: Optional[List[EdgeNetworkSpec]] = None
    dns: Optional[DNSList] = None

