from typing import (
    Any,
    Dict,
    List,
    Literal,
    Optional,
)

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
)

import yaml
from ..oam_services.network_types import FullModelName, FullNameTag, NameTag, SnakeModel
from ..a1_services.a1_policy_types import *


# === Enum-like Filter ===
DeliveryEndpointType = Literal["sql", "victoriametrics"]


# === Base Identifier Types ===
MonitoringTypeId = FullModelName
TargetId = FullNameTag
MonitoringId = NameTag


class ServiceModel(BaseModel):
    """
    Represents a service model to be monitored within an O-RAN monitoring deployment.
    Attributes:
        name: The type of service model to monitor. Must be one of the following:
              "KPM", "MAC", "RLC", "PDCP", "GTP", "SLICE", or "TC".
        periodicity: The monitoring interval, specified in milliseconds. Supported values include:
                     "1", "2", "5", "10", "100", "500", and "1000".
        metrics: An optional list of metric names to monitor for the selected service model.
                 If omitted, all available metrics may be monitored by default.
    """
    name: Literal["KPM", "MAC", "RLC", "PDCP", "GTP", "SLICE", "TC"]
    periodicity: Literal["1", "2", "5", "10", "100", "500", "1000"]
    metrics: Optional[List[str]] = Field(default_factory=list)


class SqlDatabase(BaseModel):
    """
    Represents the configuration for SQL database storage in monitoring.

    Attributes:
        db_name: Optional name of the SQL database to use for storing monitoring data.
    """
    db_name: Optional[str] = Field(
        None, alias="dbName", description="Name of the SQL database for monitoring data storage."
    )

class VictoriaMetricsDatabase(BaseModel):
    """
    Represents the configuration for Victoria Metrics database storage in monitoring.

    Attributes:
        scenario: Optional scenario name for Victoria Metrics database configuration.
    """
    scenario: Optional[str] = Field(
        None, description="Scenario name for Victoria Metrics database configuration."
    )
    

class DatabaseType(BaseModel):
    """
    Represents the database configuration for monitoring data storage.

    Attributes:
        sql_database: Optional configuration for SQL database storage.
        victoria_metrics: Optional configuration for Victoria Metrics database storage.
    """
    sql_database: Optional[SqlDatabase] = Field(
        None, alias="sqlDatabase", description="Configuration for SQL database storage."
    )
    victoria_metrics: Optional[VictoriaMetricsDatabase] = Field(
        None, alias="victoriaMetrics", description="Configuration for Victoria Metrics database storage."
    )

class MonitoringStatements(BaseModel):
    """
    Represents the monitoring statements that define the parameters for monitoring.

    Attributes:
        service_models (List[ServiceModel]): List of service models to be monitored.
        database (Optional[DatabaseType]): The type of database to use for storing monitoring data. 
        environment_variables (Optional[Dict[str, str]]): Key-value pairs of environment variables to set in the monitoring container.
            Keys are written in standard lowercase YAML/JSON style but will be converted to 
            uppercase with underscores when injected into the container's environment.
        extra_config_annotation (Optional[Dict[str, str]]): Extra annotations for configuration.
        profiles (Optional[List[str]]): Active profiles in the monitoring deployment.
    """
    service_models: Optional[List[ServiceModel]] = Field(
        default_factory=list,
        alias="serviceModels",
        description="List of service models to be monitored.",
    )
    database: Optional[DatabaseType] = Field(
        None, alias="database", description="The type of database to use for storing monitoring data."
    )
    
    environment_variables: Optional[Dict[str, str]] = Field(
        default_factory=dict,
        alias="environmentVariables",
        description="Environment variables for the monitoring deployment.",
    )
    extra_config_annotation: Optional[Dict[str, str]] = Field(
        default_factory=dict, 
        alias="extraConfigAnnotation",
        description="Extra annotations for configuration.",
    )
    profiles: Optional[List[str]] = Field(
        default_factory=list
    )


#TODO: scope_identifier shouldn't be optional, but it is for now to avoid breaking changes.
class MonitoringObject(SnakeModel):
    """
    Represents a monitoring object containing scope and monitoring statements.
    
    Attributes:
        scope_identifier: The identifier for the scope of the monitoring.
        monitoring_statements: The statements that define the monitoring parameters.
    """

    scope_identifier: Optional[ScopeIdentifier] = Field(
        None,
        alias="scopeIdentifier",
        description="The identifier for the scope of the monitoring.",
    )
    monitoring_statements: MonitoringStatements = Field(
        ...,
        alias="monitoringStatements",
        description="The statements that define the monitoring parameters.",
    )

class MonitoringObjectInformation(SnakeModel):
    """
    Represents the information of a monitoring object, including its target, type, and the actual monitoring object.


    Attributes:
        monitoring_id: The unique identifier of the monitoring.
        monitoring_type_id: The type of the monitoring.
    """
    taget: TargetId = Field(
        ...,
        alias="target",
        description="The target identifier for the monitoring object.",
    )
    monitoring_type_id: MonitoringTypeId = Field(
        ...,
        alias="monitoringTypeId",
        description="The type identifier of the monitoring object.",
    )

    monitoring_object: MonitoringObject = Field(
        ...,
        alias="monitoringObject",
        description="The actual monitoring object containing the monitoring details.",
    )


class DeliveryEndpoint(BaseModel):
    """
    Represents the endpoint where collected monitoring data is delivered.
    Mirrors the Go struct DeliveryEndpointStatus.

    Attributes:
        name: Element name.
        namespace: Element namespace.
        type: Endpoint type. Only "sql" supported for now.
        uri: Connection string/URL (e.g., postgres://..., mysql://..., sqlite:///...).
    """
    name: str = Field(
        ..., 
        description="Element name."
    )
    namespace: str = Field(
        ..., description="Element namespace."
    )
    type: DeliveryEndpointType = Field(
        ..., description='Type of endpoint. Only "sql" supported.'
    )
    uri: Endpoint = Field(
        ..., description="Connection endpoint."
    )