from br_rapp_sdk import OAMServices
from br_rapp_sdk.oam_services.network_types import *

if __name__ == "__main__":

    # Initialize the OAMServices client
    oam_services = OAMServices()

    # Get the list of networks
    net_id = NetworkId("oran")
    result = oam_services.network.get_network(network_id=net_id)
    if result.status == "success":
        net_spec = result.data.get("item", [])
    else:
        print("Failed to retrieve networks: ", result.error)
        exit(1)
        
    # Print the current TDD configuration
    print("TDD Config before change:", net_spec.access[0].cells[0].tdd_config)

    # Change the TDD configuration
    new_tdd_config = TDDConfig(
        period="5ms",
        dl_slots=6,
        dl_symbols=6,
        ul_slots=3,
        ul_symbols=4
    )
    net_spec.access[0].cells[0].tdd_config = new_tdd_config

    # Apply the updated network specification
    result = oam_services.network.apply_network(
        network_name=net_id,
        network_spec=net_spec
    )
    if result.status == 'success':
        network_id = result.data.get('network_id')
        print(f"Access applied successfully: {network_id}")
    else:
        print(f"Error applying access: {result.error}")
    
    # Retrieve the updated network to verify the change
    result = oam_services.network.get_network(network_id=net_id)
    if result.status == "success":
        updated_net_spec = result.data.get('item')
        print("TDD Config after change:", updated_net_spec.access[0].cells[0].tdd_config)
    else:
        print("Failed to retrieve updated network: ", result.error)