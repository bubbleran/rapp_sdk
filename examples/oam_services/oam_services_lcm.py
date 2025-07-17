from br_rapp_sdk import OAMServices
from br_rapp_sdk.oam_services.network_types import *
from br_rapp_sdk.oam_services.terminal_types import *

if __name__ == "__main__":

    # Initialize the OAMServices client
    oam_services = OAMServices()

    # Get the list of terminals
    result = oam_services.terminal.list_terminals()
    
    if result.status == "success":
        terminals = result.data.get("items", [])
        if len(terminals) == 0:
            print("No terminals found.")
        else:
            for term_id, terminal_spec in terminals:
                print(f"Terminal ID: {term_id}")
                print(f"Terminal Spec: {terminal_spec.yaml()}")
    else:
        print("Failed to retrieve terminals: ", result.error)
        terminals = []

    # Get the list of terminals
    result = oam_services.network.list_networks()
    
    # Print the networks
    if result.status == "success":
        networks = result.data.get("items", [])
        if len(networks) == 0:
            print("No networks found.")
        else:
            print("Networks:")
            for net_id, net_spec in networks:
                print(f"Network Name: {net_id}")
                print(f"Network Spec: {net_spec.yaml()}")
    else:
        print("Failed to retrieve networks: ", result.error)
        networks = []

    # Change the terminal
    new_term_id = None
    if len(terminals) > 0:
        _, first_term_spec = terminals[0]
        first_term_spec.identity.imsi = IMSI("001010000000001")
        result = oam_services.terminal.apply_terminal(
            terminal_name="ue2",
            terminal_spec=first_term_spec
        )
        if result.status == "success":
            new_term_id = result.data.get('terminal_id')
            print("Terminal applied successfully: ", new_term_id)
        else:
            print("Failed to apply terminal: ", result.error)

    # Retrieve the new terminal
    if new_term_id is not None:
        found_term = oam_services.terminal.get_terminal(terminal_id=new_term_id)
        if found_term.status == "success":
            found_term_spec = found_term.data.get('item')
            print("Found Terminal Spec: ", found_term_spec.yaml())
        else:
            print("Failed to retrieve terminal: ", found_term.error)


    # Delete Terminal
    if new_term_id is not None:
        result = oam_services.terminal.delete_terminal(new_term_id)
        if result.status == "success":
            print("Terminal deleted successfully.")
        else:
            print("Failed to delete terminal: ", result.error)

    # List core, access, and edge networks
    cores_result = oam_services.network.list_networks(part="core")
    if cores_result.status == "success":
        print("Core Networks: ", cores_result.data.get("items", []))
    else:
        print("Failed to retrieve core networks: ", cores_result.error)

    accesses_result = oam_services.network.list_networks(part="access")
    if accesses_result.status == "success":
        print("Access Networks: ", accesses_result.data.get("items", []))
    else:
        print("Failed to retrieve access networks: ", accesses_result.error)

    edges_result = oam_services.network.list_networks(part="edge")
    if edges_result.status == "success":
        print("Edge Networks: ", edges_result.data.get("items", []))
    else:
        print("Failed to retrieve edge networks: ", edges_result.error)

    # Change the network
    print("Changing the network...")
    if len(networks) > 0:
        first_net_id, first_net_spec = networks[0]
        if len(first_net_spec.edge) > 0:
            edge = first_net_spec.edge[0]
            edge.name = "newric"
            edge.annotations = {"ric": "ric"}
            result = oam_services.network.apply_network(
                network_name=first_net_id,
                network_spec=first_net_spec
            )
            if result.status == "success":
                new_net_id = result.data.get('network_id')
                print("Network applied successfully: ", new_net_id)
            else:
                print("Failed to apply network: ", result.error)
        else:
            print("No edge networks available to change.")        
    else:
        print("No networks available to change.")