from br_rapp_sdk import OAMServices

if __name__ == "__main__":

    oam = OAMServices()

    # List available terminals
    list_result = oam.terminal.list_terminals()
    if list_result.status == "success":
        terminals = list_result.data.get("items", [])
        print("Available terminals:")
        for term_id, _ in terminals:
            print(f"  - {term_id}")
    else:
        print("Failed to list terminals:", list_result.error)
        terminals = []

    if not terminals:
        print("No terminals found. Exiting.")
        exit(1)

    term_id, _ = terminals[0]

    # --- Connectivity ---
    print(f"\nTesting connectivity on '{term_id}' to gateway ...")
    result = oam.terminal.test_connectivity(term_id)
    if result.status == "success":
        print(f"Connected: {result.data['connected']}")
        print("\n--- ping output ---")
        print(result.data["output"])
    else:
        print("Connectivity test failed:", result.error)

    # --- Throughput ---
    print(f"\nRunning downlink throughput test on '{term_id}' ...")
    result = oam.terminal.test_throughput(
        term_id,
        direction="dl",
        args=["--time", "10", "--interval", "1"],
    )
    if result.status == "success":
        print("\n--- iperf output ---")
        print(result.data["output"])
    else:
        print("Throughput test failed:", result.error)
