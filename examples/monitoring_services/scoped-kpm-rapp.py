from br_rapp_sdk import MonitoringServices
from br_rapp_sdk.monitoring_services.monitoring_types import *

if __name__ == "__main__":
    
    # Initialize the monitoring services
    monitoring_services = MonitoringServices()

    # Define the monitoring object information
    monitoring_object_info = MonitoringObjectInformation(
        target=TargetId("ric.oran"),
        monitoring_type_id=MonitoringTypeId("bubbleran/mon"),
        monitoring_object=MonitoringObject(
            scope_identifier=ScopeIdentifier(
                slice_id=SliceId(
                    sst=1,
                    sd="000001"
                )
            ),
            monitoring_statements=MonitoringStatements(
                serviceModels=[
                    ServiceModel(
                        name="KPM",
                        periodicity="1000"
                    )
                ],
                database=DatabaseType(
                    victoriaMetrics=VictoriaMetricsDatabase(scenario="slice1_scenario")
                )
            )
        )
    )
    
    # Print the monitoring object information in YAML format
    print("Monitoring Object Information: \n", monitoring_object_info.yaml())
    
    # Apply the monitoring job
    monitoring_name = "kpm-monitoring-job"
    result = monitoring_services.apply_monitoring(monitoring_name=monitoring_name, monitoring_object=monitoring_object_info)
    
    # Check if the operation was successful
    if result.status == 'success':
        monitoring_id = result.data.get('monitoring_id')
        print(f"Monitoring job applied successfully: {monitoring_id}")
    else:
        print(f"Error applying monitoring job: {result.error}")
    
