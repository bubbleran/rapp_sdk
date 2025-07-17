from br_rapp_sdk import A1Services
from br_rapp_sdk.a1_services.a1_policy_types import *


if __name__ == "__main__":

    # Initialize the A1Services
    a1_services = A1Services()

    # Define the policy information
    policy_info = PolicyObjectInformation(
        near_rt_ric_id =NearRtRicId("ric.oran"),
        policy_type_id=PolicyTypeId("bubbleran/slicing"),
        policy_object=PolicyObject(
            scope_identifier=ScopeIdentifier(
                slice_id=SliceId(
                    sst=1,
                    sd="000001"
                ),
                cell_id=CellId(
                    plmn_id=PlmnId(
                        mcc="001",
                        mnc="01"
                    )
                ),
            ),
            policy_statements=PolicyStatements(
                policy_objectives=PolicyObjectives(
                    lb_objectives=LbObjectives(
                        target_prb_usg=60,
                        prb_usg_type=7
                    )
                )
            )
        )
    )

    # Print the policy information in YAML format
    print("Policy Object Information: \n", policy_info.yaml())

    # Apply the policy
    policy_name= "slice1"
    result = a1_services.apply_policy(policy_name = policy_name, policy_object = policy_info)

    # Check if the operation was successful
    if result.status == 'success':
        policy_id = result.data.get('policy_id')
        print(f"Policy applied successfully: {policy_id}")
    else:
        print(f"Error applying policy: {result.error}")


