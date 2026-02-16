from br_rapp_sdk import OAMServices
from br_rapp_sdk.oam_services.network_types import *
from br_rapp_sdk.oam_services.terminal_types import *

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
        
    # Print the current cell configuration
    print("Spectrum Config before change:")
    print("  band:", net_spec.access[0].cells[0].band)
    print("  arfcn:", net_spec.access[0].cells[0].arfcn)
    print("  bandwidth:", net_spec.access[0].cells[0].bandwidth)
    print("  subcarrier-spacing:", net_spec.access[0].cells[0].subcarrier_spacing)

    # Change the spectrum configuration
    net_spec.access[0].cells[0].band = "n41"
    net_spec.access[0].cells[0].arfcn = 504990
    net_spec.access[0].cells[0].bandwidth = "20MHz"
    net_spec.access[0].cells[0].subcarrier_spacing = "30kHz"

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
        print("\nSpectrum Config after change:")
        print("  band:", updated_net_spec.access[0].cells[0].band)
        print("  arfcn:", updated_net_spec.access[0].cells[0].arfcn)
        print("  bandwidth:", updated_net_spec.access[0].cells[0].bandwidth)
        print("  subcarrier-spacing:", updated_net_spec.access[0].cells[0].subcarrier_spacing)
    else:
        print("Failed to retrieve updated network: ", result.error)

    # =============== Terminal Configuration ===============
    result = oam_services.terminal.list_terminals()
    if result.status == "success":
        terminals = result.data.get("items", [])
        if terminals:
            terminal_id = terminals[0][0]  # Get the first terminal's ID
            print(f"\nFound terminal: {terminal_id}")
        else:
            print("No terminals found.")
            exit(1)
    else:
        print("Failed to list terminals: ", result.error)
        exit(1)

    # Get the terminal configuration
    result = oam_services.terminal.get_terminal(terminal_id=terminal_id)
    if result.status == "success":
        terminal_spec = result.data.get("item")
        print("\nTerminal Config before change:")
        print(f"  bands: {terminal_spec.radio.bands[0]}")
    else:
        print("Failed to retrieve terminal: ", result.error)
        exit(1)

    # Modify the terminal band to match network band
    terminal_spec.radio.bands = [net_spec.access[0].cells[0].band]

    # Apply the updated terminal specification
    result = oam_services.terminal.apply_terminal(
        terminal_name=str(terminal_id),
        terminal_spec=terminal_spec
    )
    if result.status == 'success':
        new_terminal_id = result.data.get('terminal_id')
        print(f"Terminal applied successfully: {new_terminal_id}")
    else:
        print(f"Error applying terminal: {result.error}")

    # Retrieve the updated terminal to verify the change
    result = oam_services.terminal.get_terminal(terminal_id=terminal_id)
    if result.status == "success":
        updated_terminal_spec = result.data.get('item')
        print("\nTerminal Config after change:")
        print(f"  bands: {updated_terminal_spec.radio.bands[0]}")
    else:
        print("Failed to retrieve updated terminal: ", result.error)