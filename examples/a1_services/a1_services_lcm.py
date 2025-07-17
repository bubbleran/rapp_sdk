import time
# import yaml
from br_rapp_sdk import A1Services
from br_rapp_sdk.a1_services.a1_policy_types import *


if __name__ == "__main__":
    # Initialize the A1Services client
    a1_services = A1Services()

    # Get the list of Near-RT RICs
    result = a1_services.get_rics()
    # Check if the operation was successful
    if result.status == 'success':
        near_rt_ric_ids = result.data.get('items', [])
        if len(near_rt_ric_ids) == 0:
            print("No Near-RT RICs found.")
        else:
            print("Near-RT RICs:")
            for ric_id in near_rt_ric_ids:
                print(f"RIC ID: {ric_id}")

    # Get the list of policy job CRDs
    result = a1_services.list_policies()

    # Check if the operation was successful
    if result.status == 'success':
        policies = result.data.get('items', [])
        if len(policies) == 0:
            print("No policies found.")
        else:
            print("Policies:")
            for policy_id, policy_obj in policies:
                print(f"Policy ID: {policy_id}")
                print(f"Policy Object:\n {policy_obj.yaml()}")
    else:
        print(f"Error listing policies: {result.error}")


    policy_info = PolicyObjectInformation(
        near_rt_ric_id =NearRtRicId("ric.oran"),
        policy_type_id=PolicyTypeId("bubbleran/sla"),
        policy_object=PolicyObject(
            scope_identifier=ScopeIdentifier(
                slice_id=SliceId(
                    sst=1,
                    sd="000001",
                    plmn_id=PlmnId(
                        mcc="001",
                        mnc="01"
                    )
                ),
            ),
            policy_statements=PolicyStatements(
                policy_objectives=PolicyObjectives(
                    slice_sla_objectives=SliceSlaObjectives(
                        gua_dl_thpt_per_slice=60000,
                        max_dl_thpt_per_slice=60000
                    )
                )
            )
        )
    )

    # Print the policy information in YAML format
    print("Policy Object Information: \n", policy_info.yaml())

    # Apply the policy
    policy_name= "testsdk"
    result = a1_services.apply_policy(policy_name = policy_name, policy_object = policy_info)
    # Check if the operation was successful
    policy_id = None
    if result.status == 'success':
        policy_id = result.data.get('policy_id')
        print(f"Policy applied successfully: {policy_id}")
    else:
        print(f"Error applying policy: {result.error}")

    # Print the applied policy in YAML format
    if policy_id is  None:
        print("No policy ID returned, exiting.")
        exit(1)

    result = a1_services.get_policy(policy_id=policy_id)
    if result.status == 'success':
        applied_policy = result.data.get('item')
        print("Applied Policy Object:\n", applied_policy.yaml())


    # # Get the policy status
    result = a1_services.get_policy_status(policy_id)
    # Check if the operation was successful
    if result.status == 'success':
        policy_status = result.data.get('status')
    else:
        print(f"Error getting policy status: {result.error}")
        policy_status = None

    while (policy_status.get("phase") != "Running"):
        time.sleep(0.2)
        result = a1_services.get_policy_status(policy_id)
        if result.status == 'success':
            policy_status = result.data.get('status')
        else:
            print(f"Error getting policy status: {result.error}")
            policy_status = None
        print("Policy Status:", policy_status.get("phase"))
    
    # # Get the policy feedback url
    dest = None
    result = a1_services.get_policy_feedback_api_urls(policy_id)
    # Check if the operation was successful
    if result.status == 'success':
        policy_feedback_url = result.data.get('items', [])
        for xapp_id, urls in policy_feedback_url:
            for url in urls:
                dest: PolicyFeedbackDestination = url 
                print(f"Policy Feedback URL for {xapp_id}: {dest.full_url}")
            
    else:
        print(f"Error getting policy feedback URL: {result.error}")
        policy_feedback_url = None

    # # # Get the policy feedback  
    if policy_feedback_url is None:
        print("No policy feedback URL found, exiting.")
        exit(1)     
    result = a1_services.get_policy_feedback(dest)

    # Check if the operation was successful
    if result.status == 'success':
        policy_feedback = result.data.get('item', [])
        print("Policy Feedback:", policy_feedback)
    else:
        print(f"Error getting policy feedback: {result.error}")
        policy_feedback = None
        
    # # # Delete the policy
    result = a1_services.delete_policy(policy_id)
    # Check if the operation was successful
    if result.status == 'success':
        print(f"Policy {policy_id} deleted successfully.")
    else:
        print(f"Error deleting policy: {result.error}")