from typing import (
    Any,
    ClassVar,
    List,
    Literal,
    Optional,
    Annotated,
)
from pydantic import (
    Field,
    HttpUrl,
    IPvAnyAddress,
    validator,
    model_validator,
    StringConstraints,
)
from ..oam_services.network_types import FullModelName, FullNameTag, NameTag, SnakeModel, NetworkId

# === Base Identifier Types ===

PolicyTypeId = FullModelName
NearRtRicId = FullNameTag
PolicyId = NameTag
DynamicXappId = Annotated[
    str,
    StringConstraints(
        pattern=r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?\.[a-z0-9]([-a-z0-9]*[a-z0-9])?\.[a-z0-9]([-a-z0-9]*[a-z0-9])?$',
        min_length=5,
        max_length=127,
    ),
    Field(
        description=(
            "Three-part lowercase identifier separated by dots in the form: name.target.network. "
            "Each part must comply with DNS-1123: start and end with a letter or digit, and may contain hyphens."
        )
    )
]

class SubscriptionId(SnakeModel):
    id: str

# === Enum-like Filter ===

# TODO
class QueryFilter(SnakeModel):
    OWN: ClassVar[str] = "OWN"
    OTHERS: ClassVar[str] = "OTHERS"
    ALL: ClassVar[str] = "ALL"

# === Scope Identifier ===

class PlmnId(SnakeModel):
    """
    Represents a Public Land Mobile Network Identifier (PLMN ID),
    as defined in 3GPP TS 23.003.

    Attributes:
        mcc: Mobile Country Code (MCC), must be exactly 3 digits.
        mnc: Mobile Network Code (MNC), must be 2 or 3 digits.
    """

    mcc: Optional[str] = Field(
        default=None,
        alias="mcc",
        pattern=r"^[0-9]{3}$",
        description="Mobile Country Code (3 digits, 3GPP TS 23.003)"
    )

    mnc: Optional[str] = Field(
        default=None,
        alias="mnc",
        pattern=r"^[0-9]{2,3}$",
        description="Mobile Network Code (2 or 3 digits, 3GPP TS 23.003)"
    )


class SliceId(SnakeModel):
    """
    Represents a network slice identifier (S-NSSAI) as defined in 3GPP TS 23.003.

    Attributes:
        sst: Slice/Service Type (SST), 0–255. Applicable to 5G RAN.
        sd: Slice Differentiator (SD), exactly 6 hexadecimal characters. Required if used.
        plmn_id: Public Land Mobile Network Identifier (PLMN ID). Applicable to both 4G and 5G RAN.
    """

    sst: Optional[int] = Field(
        default=None,
        alias="sst",
        ge=0,
        le=255,
        description="Slice/Service Type (0–255, 3GPP TS 23.003), applicable to 5G RAN."
    )

    sd: Optional[str] = Field(
        default=None,
        alias="sd",
        pattern=r"^[A-Fa-f0-9]{6}$",
        description="Slice Differentiator (exactly 6 hex characters, 3GPP TS 23.003), required if used."
    )

    plmn_id: Optional[PlmnId] = Field(
        default=None,
        alias="plmnId",
        description="Public Land Mobile Network Identifier (3GPP TS 23.003), applicable to 4G and 5G RAN."
    )


class QosId(SnakeModel):
    """
    Represents a QoS Identifier used in 4G or 5G RANs.

    Exactly one of `qci` (4G) or `field_5ql` (5G) must be set.

    Attributes:
        qci: QoS Class Identifier for 4G (3GPP TS 23.203), range 1-256.
        field_5ql: 5G QoS Identifier (5QI) as per 3GPP TS 23.501, range 1-256.
    """

    qci: Optional[int] = Field(
        None,
        alias="qci",
        ge=1,
        le=256,
        description="4G QoS Class Identifier (3GPP TS 23.203)"
    )
    field_5ql: Optional[int] = Field(
        None,
        alias="5ql",
        ge=1,
        le=256,
        description="5G QoS Identifier (5QI, 3GPP TS 23.501)"
    )

    @model_validator(mode="after")
    def validate_exclusive_fields(self) -> "QosId":
        if self.qci is not None and self.field_5ql is not None:
            raise ValueError("Only one of 'qci' or '5ql' may be set.")
        if self.qci is None and self.field_5ql is None:
            raise ValueError("One of 'qci' or '5ql' must be set.")
        return self


class CId(SnakeModel):
    """
    Represents a Cell Identifier, either for 4G (E-UTRAN) or 5G (NR),
    as defined in 3GPP TS 23.003.

    Exactly one of `ec_i` (for 4G) or `nc_i` (for 5G) must be set.

    Attributes:
        ec_i: E-UTRAN Cell Identifier (28-bit integer, 0-268435455).
        nc_i: NR Cell Identifier (36-bit integer, 0-68719476735).
    """

    ec_i: Optional[int] = Field(
        None,
        alias="ecI",
        ge=0,
        le=268_435_455,
        description="E-UTRAN Cell Identifier (4G, 28 bits)"
    )
    nc_i: Optional[int] = Field(
        None,
        alias="ncI",
        ge=0,
        le=68_719_476_735,
        description="NR Cell Identifier (5G, 36 bits)"
    )

    @model_validator(mode="after")
    def validate_exclusive_fields(cls, values):
        ec_i, nc_i = values.get("ec_i"), values.get("nc_i")
        if ec_i is not None and nc_i is not None:
            raise ValueError("Only one of 'ec_i' or 'nc_i' may be set.")
        if ec_i is None and nc_i is None:
            raise ValueError("One of 'ec_i' or 'nc_i' must be set.")
        return values


class CellId(SnakeModel):
    """
    Represents a global Cell Identifier based on ECGI (for 4G) or NCGI (for 5G),
    as defined in 3GPP TS 23.003.

    Attributes:
        plmn_id: Public Land Mobile Network Identifier (PLMN ID) as per 3GPP TS 23.003.
        c_id: Cell Identifier component of the global cell identity.
    """

    plmn_id: Optional[PlmnId] = Field(
        None,
        alias="plmnId",
        description="PLMN Identifier (3GPP TS 23.003)"
    )
    c_id: Optional[CId] = Field(
        None,
        alias="cId",
        description="Cell Identifier (3GPP TS 23.003)"
    )

class GroupId(SnakeModel):
    """
    Represents a group identifier used to implicitly reference a dynamic set of UEs
    sharing a common radio resource or subscriber profile.

    Only one of the two attributes may be set, depending on the RAN type:
      - `sp_id` for 4G RAN (subscriber profile ID, 3GPP TS 36.300)
      - `rfsp_index` for 5G RAN (RF selection priority index, 3GPP TS 23.501)

    Value range for both is 1-256.
    """

    sp_id: Optional[int] = Field(
        None,
        alias="spId",
        ge=1,
        le=256,
        description="4G RAN: Subscriber Profile ID (3GPP TS 36.300)"
    )
    rfsp_index: Optional[int] = Field(
        None,
        alias="rfspIndex",
        ge=1,
        le=256,
        description="5G RAN: RF selection priority index (3GPP TS 23.501)"
    )

    @model_validator(mode="after")
    def only_one_field_must_be_set(cls, values):
        sp_id, rfsp_index = values.get("sp_id"), values.get("rfsp_index")
        if sp_id and rfsp_index:
            raise ValueError("Only one of 'sp_id' or 'rfsp_index' may be set, not both.")
        if not sp_id and not rfsp_index:
            raise ValueError("One of 'sp_id' or 'rfsp_index' must be set.")
        return values


class ScopeIdentifier(SnakeModel):
    """
    Identifies the scope in which a policy statement is applicable.

    Attributes:
        slice_id: Identifies the network slice the policy applies to.
        ue_id: Identifies a specific UE the policy applies to.
        group_id: Identifies a group of UEs to which the policy applies.
        qos_id: Identifies the QoS flow the policy applies to.
        cell_id: Identifies the cell the policy applies to.
        targets: (Optional) List of custom target entities, if applicable.
        scopes: (Optional) List of named scopes (e.g., for orchestration grouping or policy context).
    """
    
    slice_id: Optional[SliceId] = Field(None, alias="sliceid")
    ue_id: Optional[str] = Field(None, alias="ueid")
    group_id: Optional[GroupId] = Field(None, alias="groupid")
    qos_id: Optional[QosId] = Field(None, alias="qosid")
    cell_id: Optional[CellId] = Field(None, alias="cellid")
    targets: Optional[List[str]] = Field(None, alias="targets")
    scopes: Optional[List[str]] = Field(None, alias="scopes")


# === Objectives and Resource Statements ===

class ReliabilityType(SnakeModel):
    """
    Represents the reliability requirement for successful transmission of a data packet
    of a given size within a user-plane latency constraint.

    Attributes:
        packet_size: Size of the data packet in bytes.
        user_plane_latency: Maximum allowed latency in ms for delivering the packet across the radio interface.
        success_probability: Probability (0–1) that the packet is successfully delivered within the latency budget.
    """

    packet_size: Optional[int] = Field(
        None,
        alias="packetSize",
        ge=0,
        description="Packet size in bytes"
    )
    user_plane_latency: Optional[int] = Field(
        None,
        alias="userPlaneLatency",
        ge=0,
        description="Latency in ms from ingress to egress of the radio interface (3GPP TS 38.314)"
    )
    success_probability: Optional[float] = Field(
        None,
        alias="successProbability",
        ge=0.0,
        le=1.0,
        description="Probability of successful transmission (0–1)"
    )
class QosObjectives(SnakeModel):
    """
    Represents QoS (Quality of Service) objectives as defined in 3GPP TS 23.501.

    Attributes:
        gfbr: Guaranteed Flow Bit Rate (GFBR) in kbps. Ensures minimum bandwidth is available.
        mfbr: Maximum Flow Bit Rate (MFBR) in kbps. Upper limit of allowed bandwidth.
        priority_level: QoS priority level (lower value means higher priority).
        pdb: Packet Delay Budget (PDB) in milliseconds. Max tolerated delay for packet delivery.
    """
    gfbr: Optional[int] = Field(None, alias="gfbr")
    mfbr: Optional[int] = Field(None, alias="mfbr")
    priority_level: Optional[int] = Field(None, alias="priorityLevel")
    pdb: Optional[int]


class QoeObjectives(SnakeModel):
    """
    Represents QoE (Quality of Experience) objectives for media services.

    Attributes:
        qoe_score: Mean Opinion Score (MOS) between 1 and 5.
            Can represent video MOS (e.g., per ITU-T P.1203.3) or a custom-defined score.
        initial_buffering: Initial buffering time in seconds (between user action and playback start).
        re_buff_freq: Rebuffering frequency (stalling events per media duration or time window).
        stall_ratio: Ratio of total stall duration to total media length.
    """

    qoe_score: Optional[int] = Field(None, alias="qoeScore")
    initial_buffering: Optional[int] = Field(None, alias="initialBuffering")
    re_buff_freq: Optional[int] = Field(None, alias="reBuffFreq")
    stall_ratio: Optional[int] = Field(None, alias="stallRatio")


class UeLevelObjectives(SnakeModel):
    """
    Represents UE-level performance targets or RAN optimization constraints.

    Attributes:
        ul_throughput: Average uplink RAN UE throughput in kbps (3GPP TS 28.552).
        dl_throughput: Average downlink RAN UE throughput in kbps (3GPP TS 28.552).
        ul_packet_delay: Uplink packet delay in milliseconds (typically 0-1 ms) (3GPP TS 38.314, 28.552).
        dl_packet_delay: Downlink packet delay in milliseconds (typically 0-1 ms) (3GPP TS 38.314, 28.552).
        ul_pdcp_sdu_packet_loss_rate: Uplink PDCP SDU packet loss rate as reliability target (3GPP TS 28.552).
        dl_rlc_sdu_packet_loss_rate: Downlink RLC SDU packet loss rate as reliability target (3GPP TS 38.314).
        dl_reliability: Downlink reliability as performance target (3GPP TS 28.552).
        ul_reliability: Uplink reliability as performance target (3GPP TS 28.552).
    """

    ul_throughput: Optional[int] = Field(None, alias="ulThroughput")
    dl_throughput: Optional[int] = Field(None, alias="dlThroughput")
    ul_packet_delay: Optional[int] = Field(None, alias="ulPacketDelay")
    dl_packet_delay: Optional[int] = Field(None, alias="dlPacketDelay")
    ul_pdcp_sdu_packet_loss_rate: Optional[int] = Field(None, alias="ulPdcpSduPacketLossRate")
    dl_rlc_sdu_packet_loss_rate: Optional[int] = Field(None, alias="dlRlcSduPacketLossRate")
    dl_reliability: Optional[ReliabilityType] = Field(None, alias="dlReliability")
    ul_reliability: Optional[ReliabilityType] = Field(None, alias="ulReliability")


class SliceSlaObjectives(SnakeModel):
    """
    Represents the Slice Service Level Agreement (SLA) objectives for a network slice.

    Attributes:
        max_number_of_ues: Maximum number of RRC-connected UEs supported concurrently by the slice (see NG.116 §3.4.17).
        max_number_of_pdu_sessions: Maximum number of PDU sessions supported concurrently by the slice (NG.116 §3.4.16).
        gua_dl_thpt_per_slice: Guaranteed downlink throughput in kbps for the entire slice (NG.116 §3.4.5).
        max_dl_thpt_per_slice: Maximum supported downlink throughput in kbps for all UEs in the slice (NG.116 §3.4.5).
        max_dl_thpt_per_ue: Maximum supported downlink throughput in kbps per UE (NG.116 §3.4.6).
        gua_ul_thpt_per_slice: Guaranteed uplink throughput in kbps for the entire slice (NG.116 §3.4.31).
        max_ul_thpt_per_slice: Maximum supported uplink throughput in kbps for all UEs in the slice (NG.116 §3.4.31).
        max_ul_thpt_per_ue: Maximum supported uplink throughput in kbps per UE (NG.116 §3.4.32).
        max_dl_packet_delay_per_ue: Maximum downlink packet delay in milliseconds.
        max_ul_packet_delay_per_ue: Maximum uplink packet delay in milliseconds.
        max_dl_pdcp_sdu_packet_loss_rate_per_ue: Max DL PDCP SDU packet loss rate (0-1 range).
        max_ul_rlc_sdu_packet_loss_rate_per_ue: Max UL RLC SDU packet loss rate (0-1 range).
        min_dl_reliability_per_ue: Minimum downlink reliability requirement.
        min_ul_reliability_per_ue: Minimum uplink reliability requirement.
        max_dl_jitter_per_ue: Maximum downlink jitter in milliseconds.
        max_ul_jitter_per_ue: Maximum uplink jitter in milliseconds.
        dl_slice_priority: Downlink slice priority (1 = highest).
        ul_slice_priority: Uplink slice priority (1 = highest).
        slice_enforce: Custom slice enforcement policy (FlexRIC-specific).
    """

    max_number_of_ues: Optional[int] = Field(None, alias="maxNumberOfUes")
    max_number_of_pdu_sessions: Optional[int] = Field(None, alias="maxNumberOfPduSessions")
    gua_dl_thpt_per_slice: Optional[int] = Field(None, alias="guaDlThptPerSlice")
    max_dl_thpt_per_slice: Optional[int] = Field(None, alias="maxDlThptPerSlice")
    max_dl_thpt_per_ue: Optional[int] = Field(None, alias="maxDlThptPerUe")
    gua_ul_thpt_per_slice: Optional[int] = Field(None, alias="guaUlThptPerSlice")
    max_ul_thpt_per_slice: Optional[int] = Field(None, alias="maxUlThptPerSlice")
    max_ul_thpt_per_ue: Optional[int] = Field(None, alias="maxUlThptPerUe")
    max_dl_packet_delay_per_ue: Optional[int] = Field(None, alias="maxDlPacketDelayPerUe")
    max_ul_packet_delay_per_ue: Optional[int] = Field(None, alias="maxUlPacketDelayPerUe")
    max_dl_pdcp_sdu_packet_loss_rate_per_ue: Optional[int] = Field(None, alias="maxDlPdcpSduPacketLossRatePerUe")
    max_ul_rlc_sdu_packet_loss_rate_per_ue: Optional[int] = Field(None, alias="maxUlRlcSduPacketLossRatePerUe")
    min_dl_reliability_per_ue: Optional[ReliabilityType] = Field(None, alias="minDlReliabilityPerUe")
    min_ul_reliability_per_ue: Optional[ReliabilityType] = Field(None, alias="minUlReliabilityPerUe")
    max_dl_jitter_per_ue: Optional[int] = Field(None, alias="maxDlJitterPerUe")
    max_ul_jitter_per_ue: Optional[int] = Field(None, alias="maxUlJitterPerUe")
    dl_slice_priority: Optional[int] = Field(None, alias="dlSlicePriority")
    ul_slice_priority: Optional[int] = Field(None, alias="ulSlicePriority")
    slice_enforce: Optional[dict] = Field(None, alias="sliceEnforce")


class LbObjectives(SnakeModel):
    """
    Represents load balancing objectives related to PRB (Physical Resource Block) usage.

    Attributes:
        target_prb_usg (Optional[int]): 
            The target PRB usage in percent. 
            The denominator is the total number of PRBs in the cell, and the numerator is the number of PRBs 
            specified by `prb_usg_type`. Value range: 0-100 [%].

        prb_usg_type (Optional[int]): 
            Specifies the PRB usage type used in the calculation of `target_prb_usg`. 
            
            Valid values (from 3GPP TS 28.552):
            
              - 1: Mean DL PRB used for data traffic (5.1.1.2.5)
              - 2: Mean UL PRB used for data traffic (5.1.1.2.7)
              - 3: Peak DL PRB used for data traffic (5.1.1.2.9)
              - 4: Peak UL PRB used for data traffic (5.1.1.2.10)
              - 5: Mean DL PRB used for data traffic per S-NSSAI (5.1.1.2.5)
              - 6: Mean UL PRB used for data traffic per S-NSSAI (5.1.1.2.7)
              - 7: Peak DL PRB used for data traffic per S-NSSAI (5.1.1.2.9)
              - 8: Peak UL PRB used for data traffic per S-NSSAI (5.1.1.2.10)

            Applicability:
              - If only `cellId` is included in the scope: valid values are 1-4.
              - If both `cellId` and `sliceId` are included in the scope: valid values are 5-8.
    """

    target_prb_usg: Optional[int] = Field(
        None,
        alias="targetPrbUsg",
        description="The target PRB usage in percent. Value range: 0-100 [%]."
    )
    prb_usg_type: Optional[int] = Field(
        None,
        alias="prbUsgType",
        description="Specifies the PRB usage type used in the calculation of targetPrbUsg."
    )

class PolicyObjectives(SnakeModel):
    """
    Represents the policy objectives defining various objectives based on A1TD spec.
    Attributes:
        qos_objectives (Optional[QosObjectives]): Objectives related to Quality of Service.
        qoe_objectives (Optional[QoeObjectives]): Objectives related to Quality of Experience.
        ue_level_objectives (Optional[UeLevelObjectives]): Objectives at the User Equipment level.
        slice_sla_objectives (Optional[SliceSlaObjectives]): Objectives related to Slice Service Level Agreements.
        lb_objectives (Optional[LbObjectives]): Objectives related to Load Balancing.
    """
    qos_objectives: Optional[QosObjectives] = Field(
        None, 
        alias="qosObjectives"
    )
    qoe_objectives: Optional[QoeObjectives] = Field(
        None, 
        alias="qoeObjectives"
    )
    ue_level_objectives: Optional[UeLevelObjectives] = Field(
        None, 
        alias="ueLevelObjectives"
    )
    slice_sla_objectives: Optional[SliceSlaObjectives] = Field(
        None, 
        alias="sliceSlaObjectives"
    )
    lb_objectives: Optional[LbObjectives] = Field(
        None, 
        alias="lbObjectives"
    )


# === Resources and Top Level ===

class PolicyResources(SnakeModel):
    """
    Represents the policy resources defining various resources based on A1TD spec.
    Attributes:
        tsp_resources (Optional[dict]): Resources related to Traffic Steering Policies.
        slice_sla_resources (Optional[dict]): Resources related to Slice Service Level Agreements.
        lb_resources (Optional[dict]): Resources related to Load Balancing.
    """
    tsp_resources: Optional[dict] = Field(
        None, 
        alias="tspResources"
    )
    slice_sla_resources: Optional[dict] = Field(
        None, 
        alias="sliceSlaResources"
    )
    lb_resources: Optional[dict] = Field(
        None, 
        alias="lbResources"
    )


class PolicyStatements(SnakeModel):
    """
    Represents the policy statements defining objectives and resources based on A1TD spec.

    Attributes:
        policy_objectives (PolicyObjectives): A statement for policy objectives expresses the goal for the policy.
        policy_resources (PolicyResources): A statement for policy resources expresses the conditions for resource usage for the policy.
    """
    policy_objectives: Optional[PolicyObjectives] = Field(
        None, 
        alias="policyObjectives",
        description="The objectives of the policy based on A1TD spec."
    )
    policy_resources: Optional[PolicyResources] = Field(
        None,
        alias="policyResources",
        description="The resources associated with the policy based on A1TD spec."
    )


class PolicyObject(SnakeModel):
    """
    Represents a policy object containing scope and policy statements based on A1TD spec.
    A PolicyObject contains a scope identifier and at least one policy statement (e.g., one or more policy objective statements and/or one or more policy resource statements)

    Attributes:
        scope_identifier (ScopeIdentifier): The scope of the policy; Identifier of what the statements in the policy applies to (UE, group of UEs, slice, QoS flow, network resource or combinations thereof).
        policy_statements (PolicyStatements): The statements defining the policy objectives and resources.
    """
    scope_identifier: ScopeIdentifier = Field(
        ..., 
        alias="scopeIdentifier",
        description="The scope of the policy based on A1TD spec."
    )
    policy_statements: PolicyStatements = Field(
        ..., 
        alias="policyStatements",
        description="The statements defining the policy objectives and resources based on A1TD spec."
    )



# === API Types ===

class Endpoint(SnakeModel):
    api_path: str = Field(..., alias="apiPath")
    element_name: str = Field(..., alias="elementName")
    host: str
    ip: IPvAnyAddress
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"]
    port: int
    scheme: Literal["http", "https"]
    service: str

    #TODO: It is better to use host instead of ip in the full_url
    @property
    def full_url(self) -> HttpUrl:
        """Constructs the full URL from scheme, host, port, and apiPath."""
        return HttpUrl(f"{self.scheme}://{self.ip}:{self.port}{self.api_path}")

    @validator("port")
    def port_range(cls, v):
        if not (1 <= v <= 65535):
            raise ValueError("Port must be between 1 and 65535")
        return v
    

class PolicyFeedbackDestination(Endpoint):
    """
    Represents the endpoint for policy feedback.
    Inherits from Endpoint and includes additional fields specific to policy feedback.

    Attributes:
        api_path (str): The API path for the feedback endpoint.
        element_name (str): The name of the element for the feedback endpoint.
        host (str): The host for the feedback endpoint.
        ip (IPvAnyAddress): The IP address for the feedback endpoint.
        method (Literal["GET", "POST", "PUT", "DELETE", "PATCH"]): The HTTP method for the feedback endpoint.
        port (int): The port for the feedback endpoint.
        scheme (Literal["http", "https"]): The scheme for the feedback endpoint.
        service (str): The service name for the feedback endpoint.
    """
    pass

class PolicyTypeInformation(SnakeModel):
    """
    Represents the information of a policy type, including its ID and Near Real-Time RIC ID.

    Attributes:
        policy_type_id (PolicyTypeId): Identifier for the policy type.
        near_rt_ric_id (NearRtRicId): Identifier for the Near Real-Time RIC.
    """
    policy_type_id: PolicyTypeId = Field(
        ..., 
        alias="policyTypeId"
    )
    near_rt_ric_id: NearRtRicId = Field(
        ..., 
        alias="nearRtRicId"
    )


class PolicyInformation(SnakeModel):
    """
    Represents the information of a policy, including its ID and Near Real-Time RIC ID.

    Attributes:
        policy_id (PolicyId): Identifier for the policy.
        near_rt_ric_id (NearRtRicId): Identifier for the Near Real-Time RIC.
    """

    policy_id: PolicyId = Field(
        ...,
        alias="policyId"
    )
    near_rt_ric_id: NearRtRicId = Field(
        ..., 
        alias="nearRtRicId"
    )


class PolicyTypeObject(SnakeModel):
    # TODO: Define this based on A1TD spec content if available
    name: dict

class PolicyObjectInformation(SnakeModel):
    """
    Represents the information of a policy object based on R1 A1-Related Services, including its target, type, and the actual policy object.

    Attributes:
        near_rt_ric_id (NearRtRicId): Identifier for the Near Real-Time RIC that is to be used for the policy deployment. format: <ric-name>.<network-name>
        policy_type_id (PolicyTypeId): Identifier for the policy type that is to be used for the policy deployment. format: <model-name>/<deployment-mode>
        policy_object (PolicyObject): Policy Object is a JSON representation of an A1 policy; the A1 policies are specified in A1TD.
    """
    near_rt_ric_id: NearRtRicId = Field(
        ...,
        alias="nearRtRicId",
        description="Identifier for the Near Real-Time RIC as a target. format: <ric-name>.<network-name>"
    )
    policy_type_id: PolicyTypeId = Field(
        ...,
        alias="policyTypeId",
        description="Identifier for the policy type. format: <model-name>/<deployment-mode>"
    )
    policy_object: PolicyObject = Field(
        ...,
        alias="policyObject",
        description="The actual policy object containing scope and statements."
    )


class PolicyStatusSubscription(SnakeModel):
    subscription_scope: QueryFilter = Field(..., alias="subscriptionScope")
    notification_destination: Endpoint = Field(..., alias="notificationDestination")
    policy_id_list: Optional[List[PolicyId]] = Field(None, alias="policyIdList")
    policy_type_id_list: Optional[List[PolicyTypeId]] = Field(None, alias="policyTypeIdList")
    near_rt_ric_id_list: Optional[List[NearRtRicId]] = Field(None, alias="nearRtRicIdList")
