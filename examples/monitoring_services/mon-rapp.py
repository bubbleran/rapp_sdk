from br_rapp_sdk import MonitoringServices
from br_rapp_sdk.monitoring_services.monitoring_types import *
import time

if __name__ == "__main__":

    # Initialize the A1Services
    a1_services = MonitoringServices()

    # Define the monitoring information for MAC layer
    mac_monitoring_info = MonitoringObjectInformation(
        target="ric.oran",
        monitoringTypeId="mosaic5g/monitoring-python",
        monitoringObject=MonitoringObject(
            monitoringStatements=MonitoringStatements(
                serviceModels=[
                    ServiceModel(name="MAC", periodicity="10_ms")
                ],
                database="SQL"
            )
        )
    )

    # Define the monitoring information for RLC layer
    rlc_monitoring_info = MonitoringObjectInformation(
        target="ric.oran",
        monitoringTypeId="mosaic5g/monitoring-python",
        monitoringObject=MonitoringObject(
            monitoringStatements=MonitoringStatements(
                serviceModels=[
                    ServiceModel(name="RLC", periodicity="100_ms")
                ],
                database="SQL"
            )
        )
    )

    # Print the monitoring information in YAML format
    print("MAC Monitoring Object Information: \n", mac_monitoring_info.yaml())
    print("RLC Monitoring Object Information: \n", rlc_monitoring_info.yaml())

    # Apply the MAC monitoring object
    mac_monitoring_name = "mac-monitoring"
    mac_result = a1_services.apply_monitoring(
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
    rlc_result = a1_services.apply_monitoring(
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
        mac_status = a1_services.get_monitoring_status(monitoring_id=mac_monitoring_id)
        rlc_status = a1_services.get_monitoring_status(monitoring_id=rlc_monitoring_id)

        mac_phase = mac_status.data.get('status', {}).get('phase') if mac_status.status == 'success' else 'error'
        rlc_phase = rlc_status.data.get('status', {}).get('phase') if rlc_status.status == 'success' else 'error'

        print(f"MAC status: {mac_phase}")
        print(f"RLC status: {rlc_phase}")
        
        if mac_phase and rlc_phase:
            print("Both MAC and RLC Monitoring Objects are Running.")
            break

        time.sleep(3)


