from br_rapp_sdk import MonitoringServices
from br_rapp_sdk.monitoring_services.monitoring_types import *
import time

if __name__ == "__main__":

    # Initialize the A1Services
    monitoring_services = MonitoringServices()

    # Define the monitoring information for MAC layer
    mac_monitoring_info = MonitoringObjectInformation(
        target="ric.oran",
        monitoringTypeId="mosaic5g/monitoring-c-mysql",
        monitoringObject=MonitoringObject(
            monitoringStatements=MonitoringStatements(
                serviceModels=[
                    ServiceModel(name="MAC", periodicity="1000")
                ],
                database=DatabaseType(
                    sqlDatabase = SqlDatabase(dbName="test_mac_db")
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
    
    time.sleep(5)
    # Fetch the delivery endpoint for MAC monitoring from the sql database
    mac_endpoint = monitoring_services.get_delivery_endpoint(monitoring_id=mac_monitoring_id)
    if mac_endpoint.status == 'success':
        print(f"MAC Delivery Endpoint: {mac_endpoint.data.get('endpoint')}")
    else:
        print(f"Error fetching MAC delivery endpoint: {mac_endpoint.error}")
        exit(1)
    
    sql_query = """
    SELECT tstamp, pusch_snr, pucch_snr 
    FROM MAC_UE 
    ORDER BY tstamp DESC 
    LIMIT 10;
    """
    
    # Fetch data from the MAC monitoring endpoint
    mac_data_result = monitoring_services.fetch_data_from_endpoint(
        endpoint=mac_endpoint.data.get("endpoint", {}),
        query=sql_query
    )
    if mac_data_result.status == 'success':
        mac_data = mac_data_result.data.get("data", [])
        print("Fetched MAC Data:")
        for row in mac_data:
            print(row)
    else:
        print(f"Error fetching MAC data: {mac_data_result.error}")
        exit(1)
    
    # Fetch the delivery endpoint for RLC monitoring from the victoria metrics database
    rlc_endpoint = monitoring_services.get_delivery_endpoint(monitoring_id=rlc_monitoring_id)
    if rlc_endpoint.status == 'success':
        print(f"RLC Delivery Endpoint: {rlc_endpoint.data.get('endpoint')}")
    else:
        print(f"Error fetching RLC delivery endpoint: {rlc_endpoint.error}")
        exit(1)
        
    vm_query = """{sm="rlc"}"""
    # Fetch data from the RLC monitoring endpoint
    rlc_data_result = monitoring_services.fetch_data_from_endpoint(
        endpoint=rlc_endpoint.data.get("endpoint", {}),
        query=vm_query
    )
    if rlc_data_result.status == 'success':
        rlc_data = rlc_data_result.data.get("data", [])
        print("Fetched RLC Data:")
        print(rlc_data)
    else:
        print(f"Error fetching RLC data: {rlc_data_result.error}")
        exit(1)
