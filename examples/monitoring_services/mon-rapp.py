from br_rapp_sdk import MonitoringServices
from br_rapp_sdk.monitoring_services.monitoring_types import *
import time

if __name__ == "__main__":

    # Initialize the A1Services
    monitoring_services = MonitoringServices()

    # Define the monitoring information for MAC layer
    mac_monitoring_info = MonitoringObjectInformation(
        target="ric.oran",
        monitoringTypeId="mosaic5g/monitoring-c",
        monitoringObject=MonitoringObject(
            monitoringStatements=MonitoringStatements(
                serviceModels=[
                    ServiceModel(name="MAC", periodicity="1000")
                ],
                database=DatabaseType(
                    victoriaMetrics=VictoriaMetricsDatabase(scenario="test_mac_scenario")
                )
            )
        )
    )

    # Define the monitoring information for RLC layer
    rlc_monitoring_info = MonitoringObjectInformation(
        target="ric.oran",
        monitoringTypeId="mosaic5g/monitoring-c",
        monitoringObject=MonitoringObject(
            monitoringStatements=MonitoringStatements(
                serviceModels=[
                    ServiceModel(name="RLC", periodicity="1000")
                ],
                database=DatabaseType(
                    victoriaMetrics=VictoriaMetricsDatabase(scenario="test_rlc_scenario"),
                )
            )
        )
    )

    # Print the monitoring information in YAML format
    print("MAC Monitoring Object Information: \n", mac_monitoring_info.yaml())
    print("RLC Monitoring Object Information: \n", rlc_monitoring_info.yaml())

    # Apply the MAC monitoring object
    mac_monitoring_name = "mac-monitoring"
    mac_result = monitoring_services.apply_monitoring(
        monitoring_name=mac_monitoring_name,
        monitoring_object=mac_monitoring_info
    )
    # Check if the MAC monitoring object was applied successfully
    if mac_result.status == 'success':
        mac_monitoring_id = mac_result.data.get('monitoring_id')
        print(f"MAC Monitoring Object applied successfully: {mac_monitoring_id}")
    else:
        print(f"Error applying MAC Monitoring Object: {mac_result.error}")
        exit(1)
    
    # Apply the RLC monitoring object
    rlc_monitoring_name = "rlc-monitoring"
    rlc_result = monitoring_services.apply_monitoring(
        monitoring_name=rlc_monitoring_name,
        monitoring_object=rlc_monitoring_info
    )
    # Check if the RLC monitoring object was applied successfully
    if rlc_result.status == 'success':
        rlc_monitoring_id = rlc_result.data.get('monitoring_id')
        print(f"RLC Monitoring Object applied successfully: {rlc_monitoring_id}")
    else:
        print(f"Error applying RLC Monitoring Object: {rlc_result.error}")
        exit(1)

    # Wait until both monitoring objects are "Running"
    while True:
        mac_status = monitoring_services.get_monitoring_status(monitoring_id=mac_monitoring_id)
        rlc_status = monitoring_services.get_monitoring_status(monitoring_id=rlc_monitoring_id)

        mac_phase = mac_status.data.get('status', {}).get('phase') if mac_status.status == 'success' else 'error'
        rlc_phase = rlc_status.data.get('status', {}).get('phase') if rlc_status.status == 'success' else 'error'

        print(f"MAC status: {mac_phase}")
        print(f"RLC status: {rlc_phase}")
                
        if mac_phase == "Running" and rlc_phase == "Running":
            print("Both MAC and RLC Monitoring Objects are Running.")
            break

        time.sleep(3)