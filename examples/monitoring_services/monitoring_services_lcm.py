import time
from br_rapp_sdk import MonitoringServices
from br_rapp_sdk.monitoring_services.monitoring_types import *


if __name__ == "__main__":

    # Initialize the MonitoringServices client
    monitoring_services = MonitoringServices()

    # Get the list of monitoring job CRDs
    result = monitoring_services.list_monitorings()

    # Check if the operation was successful
    if result.status == 'success':
        monitoring_jobs = result.data.get('items', [])
        if len(monitoring_jobs) == 0:
            print("No monitoring jobs found.")
        else:
            print("Monitoring Jobs:")
            for job_id, job_obj in monitoring_jobs:
                print(f"Job ID: {job_id}")
                print(f"Job Object:\n {job_obj.yaml()}")
    else:
        print(f"Error listing monitoring jobs: {result.error}")
    
    # Define the monitoring object
    monitoring_object = MonitoringObjectInformation(
        target=TargetId("ric.oran"),
        monitoring_type_id=MonitoringTypeId("mosaic5g/monitoring-python"),
        monitoring_object=MonitoringObject(
            monitoring_statements=MonitoringStatements(
                serviceModels=[
                    ServiceModel(
                        name="MAC",
                        periodicity="10_ms",
                    ),
                    ServiceModel(
                        name="PDCP",
                        periodicity="100_ms",
                    )
                ],
                database="SQL" 
            )
        )
)
    # Print the monitoring object information in YAML format
    print("Monitoring Object Information:\n", monitoring_object.yaml())

    # Apply the monitoring job
    monitoring_name = "test-monitoring-job"
    result = monitoring_services.apply_monitoring(monitoring_name=monitoring_name, monitoring_object=monitoring_object)

    # Check if the operation was successful
    monitoring_id = None
    if result.status == 'success':
        monitoring_id = result.data.get('monitoring_id')
        print(f"Monitoring job applied successfully with ID: {monitoring_id}")
    else:
        print(f"Error applying monitoring job: {result.error}")
    
    if monitoring_id is None:
        print("Monitoring job ID is None, exiting.")
        exit(1)

    result = monitoring_services.get_monitoring(monitoring_id=monitoring_id)
    # Check if the operation was successful
    if result.status == 'success':
        monitoring_job = result.data.get('item', {})
        print(f"Monitoring job retrieved successfully:\n{monitoring_job.yaml()}")
    else:
        print(f"Error retrieving monitoring job: {result.error}")

    # Get the status of the monitoring job
    result = monitoring_services.get_monitoring_status(monitoring_id=monitoring_id)
    # Check if the operation was successful
    if result.status == 'success':
        monitoring_status = result.data.get('status')
        print(f"Monitoring job status: {monitoring_status.get('phase')}")
    else:
        print(f"Error retrieving monitoring job status: {result.error}")

    while(monitoring_status.get('phase') != "Running"):
        time.sleep(0.2)
        result = monitoring_services.get_monitoring_status(monitoring_id=monitoring_id)
        if result.status == 'success':
            monitoring_status = result.data.get('status')
        else:
            print(f"Error retrieving monitoring job status: {result.error}")
            monitoring_status = None
        print(f"Monitoring job status: {monitoring_status.get('phase')}")


    # Delete the monitoring job
    result = monitoring_services.delete_monitoring(monitoring_id=monitoring_id)
    # Check if the operation was successful
    if result.status == 'success':
        print(f"Monitoring job {monitoring_id} deleted successfully.")
    else:
        print(f"Error deleting monitoring job: {result.error}")