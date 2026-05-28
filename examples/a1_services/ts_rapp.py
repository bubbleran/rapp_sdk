from br_rapp_sdk import A1Services
from br_rapp_sdk.a1_services.a1_policy_types import *


if __name__ == "__main__":

    # Initialize the A1Services client
    a1_services = A1Services()

    # Build PolicyObjectInformation
    policyinfo = PolicyObjectInformation(
        near_rt_ric_id=NearRtRicId("flexric.handover"),
        policy_type_id=PolicyTypeId("bubbleran/ts"),
        policy_object=PolicyObject(
            # ScopeIdentifier indicates which UE or scope this policy affects
            scope_identifier=ScopeIdentifier(
                ue_id="0000000000000000"  # Example UE ID. "0000000000000000" means apply to ALL UEs; replace with a specific RAN UE ID to target a single UE
            ),
            # PolicyStatements contains the actual resources or rules to be enforced
            policy_statements=PolicyStatements(
                policy_resources=PolicyResources(
                    tsp_resources=TspResources(
                        tsp_resources=[
                            TspResource(
                                preference=PreferenceType.PREFER,
                                cell_id_list=[
                                    CellId(c_id=CId(nc_i=50))
                                ]
                            )
                        ]
                    )
                )
            )
        )
    )

    # Print the policy object in YAML format for inspection before applying
    print("Policy Object Information: \n", policyinfo.yaml())

    # Apply the policy via the SDK
    policy_name = "handover1"
    result = a1_services.apply_policy(policy_name=policy_name, policy_object=policyinfo)

    # Check the result of the operation
    if result.status == 'success':
        policy_id = result.data.get('policy_id')
        print(f"Policy applied successfully: {policy_id}")
    else:
        print(f"Error applying policy: {result.error}")