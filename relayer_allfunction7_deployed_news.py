from web3 import Web3
from eth_account import Account

# =========================================================
# CONFIG
# =========================================================
RPC_URL = "https://optimism-mainnet.infura.io/v3/a5afabd83b0c4f39a887ca9472bade51"
CHAIN_ID = 10  # Optimism
PRIVATE_KEY = "1f30a133bcda1193bbefb237d4c2dcd5b9856a30c14fe439e46ec52b9e86b8f2"

# Connect account and Web3
w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)
SENDER = account.address
print(f"Using owner account: {SENDER}")

# =========================================================
# CONTRACT
# =========================================================
CONTRACT_ADDRESS = Web3.to_checksum_address("0xe0fb171F4288dEa7Cd7B9C55471C15652b614Acd")

ABI = [
    # ================= CORE TOKEN / USD LOGIC =================

    {
        "name": "oracleSwapETHToUSD",
        "type": "function",
        "stateMutability": "payable",
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "ref", "type": "string"}
        ],
        "outputs": []
    },
    {
        "name": "mint",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "account", "type": "address"},
            {"name": "amount", "type": "uint256"},
            {"name": "ref", "type": "string"}
        ],
        "outputs": []
    },
    {
        "name": "transferWithRefAndUSD",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "amount", "type": "uint256"},
            {"name": "ref", "type": "string"}
        ],
        "outputs": []
    },
    {
        "name": "marketCap",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"type": "uint256"}]
    },
    {
        "name": "circulatingMarketCap",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"type": "uint256"}]
    },
    {
        "name": "balanceOfUSD",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "account", "type": "address"}],
        "outputs": [{"type": "uint256"}]
    },
    {
        "name": "setUsdPrice",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [{"name": "newPrice", "type": "uint256"}],
        "outputs": []
    },

    # ================= RELAYER / BROADCAST =================

    {
        "name": "createBroadcast",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "user", "type": "address"},
            {"name": "action", "type": "string"},
            {"name": "amount", "type": "uint256"},
            {"name": "destinationChain", "type": "string"},
            {"name": "destinationAddress", "type": "string"},
            {"name": "ref", "type": "string"}
        ],
        "outputs": [{"name": "broadcastId", "type": "uint256"}]
    },
    {
        "name": "executeBroadcast",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "broadcastId", "type": "uint256"}
        ],
        "outputs": []
    },

    # ================= EVENTS ================

{
    "anonymous": False,
    "name": "Broadcast",
    "type": "event",
    "inputs": [
        {"indexed": False, "name": "broadcastId", "type": "uint256"},
        {"indexed": False, "name": "user", "type": "address"},
        {"indexed": False, "name": "action", "type": "string"},
        {"indexed": False, "name": "amount", "type": "uint256"},
        {"indexed": False, "name": "destinationChain", "type": "string"},
        {"indexed": False, "name": "destinationAddress", "type": "string"},
        {"indexed": False, "name": "ref", "type": "string"},
        {"indexed": False, "name": "timestamp", "type": "uint256"}
    ]
}

]

contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)

# =========================================================
# HELPERS
# =========================================================
def get_nonce():
    return w3.eth.get_transaction_count(SENDER, "pending")


def sign_and_send(tx):
    signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_hash.hex(), receipt


def print_usd_balance(account):
    """
    Calls the updated balanceOfUSD which calculates
    USD value = token balance * oracle price
    """
    try:
        balance = contract.functions.balanceOfUSD(account).call()
        print(f"USD balance of {account}: {balance / 1_000_000:.6f} USD")
        return balance
    except Exception:
        print("⚠️ balanceOfUSD function missing in contract")
        return None

# =========================================================
# MAIN ACTIONS
# =========================================================
def swap_eth_to_usd():
    eth_amount = float(input("ETH amount to swap → USD: "))
    ref = input("Reference (string): ")

    print("Checking USD balance BEFORE swap...")
    before = print_usd_balance(SENDER)

    tx = contract.functions.oracleSwapETHToUSD(SENDER, ref).build_transaction({
        "from": SENDER,
        "value": w3.to_wei(eth_amount, "ether"),
        "nonce": get_nonce(),
        "gas": 500_000,
        "gasPrice": w3.eth.gas_price,
        "chainId": CHAIN_ID
    })

    tx_hash, receipt = sign_and_send(tx)
    print(f"TX sent: {tx_hash}")

    print("Checking USD balance AFTER swap...")
    after = print_usd_balance(SENDER)
    if before is not None and after is not None:
        print(f"✅ USD change: {(after - before) / 1_000_000:.6f} USD")


def mint_usd():
    human_amount = float(input("USD amount to mint (ex: 0.05): "))
    ref = input("Reference (string): ")
    amount = int(human_amount * 1_000_000)

    print("Checking USD balance BEFORE mint...")
    before = print_usd_balance(SENDER)

    tx = contract.functions.mint(SENDER, amount, ref).build_transaction({
        "from": SENDER,
        "nonce": get_nonce(),
        "gas": 500_000,
        "gasPrice": w3.eth.gas_price,
        "chainId": CHAIN_ID
    })

    tx_hash, receipt = sign_and_send(tx)
    print(f"TX sent: {tx_hash}")

    print("Checking USD balance AFTER mint...")
    after = print_usd_balance(SENDER)
    if before is not None and after is not None:
        print(f"✅ USD change: {(after - before) / 1_000_000:.6f} USD")


def transfer_usd():
    human_amount = float(input("USD amount to transfer: "))
    amount = int(human_amount * 1_000_000)
    ref = input("Reference (string): ")

    print("Checking USD balance BEFORE transfer...")
    before = print_usd_balance(SENDER)

    tx = contract.functions.transferWithRefAndUSD(SENDER, amount, ref).build_transaction({
        "from": SENDER,
        "nonce": get_nonce(),
        "gas": 500_000,
        "gasPrice": w3.eth.gas_price,
        "chainId": CHAIN_ID
    })

    tx_hash, receipt = sign_and_send(tx)
    print(f"TX sent: {tx_hash}")

    print("Checking USD balance AFTER transfer...")
    after = print_usd_balance(SENDER)
    if before is not None and after is not None:
        print(f"✅ USD change: {(after - before) / 1_000_000:.6f} USD")


def show_market_caps():
    mc = contract.functions.marketCap().call()
    cmc = contract.functions.circulatingMarketCap().call()
    print(f"Market Cap: {mc / 1_000_000:.6f} USD")
    print(f"Circulating Market Cap: {cmc / 1_000_000:.6f} USD")


def set_usd_price():
    """
    Update the internal USD price (6 decimals)
    Example: 1.00 USD = 1000000
    Also prints USD balance change for the sender account
    """
    human_price = float(input("New USD price (ex: 1.05): "))
    new_price = int(human_price * 1_000_000)

    # Print USD balance BEFORE price change
    print("Checking USD balance BEFORE price update...")
    before = print_usd_balance(SENDER)

    tx = contract.functions.setUsdPrice(new_price).build_transaction({
        "from": SENDER,
        "nonce": get_nonce(),
        "gas": 200_000,
        "gasPrice": w3.eth.gas_price,
        "chainId": CHAIN_ID
    })

    tx_hash, receipt = sign_and_send(tx)
    print(f"✅ USD price updated to {human_price:.6f}")
    print(f"TX: {tx_hash}")

    # Print USD balance AFTER price change
    print("Checking USD balance AFTER price update...")
    after = print_usd_balance(SENDER)
    if before is not None and after is not None:
        print(f"✅ USD change due to price update: {(after - before) / 1_000_000:.6f} USD")

def create_broadcast(user, action, amount, destination_chain, destination_address, ref):
    tx = contract.functions.createBroadcast(
        user,
        action,
        amount,
        destination_chain,
        destination_address,
        ref
    ).build_transaction({
        "from": SENDER,
        "nonce": get_nonce(),
        "gas": 400_000,
        "gasPrice": w3.eth.gas_price,
        "chainId": CHAIN_ID
    })

    tx_hash, receipt = sign_and_send(tx)

    broadcast_id = None
    for log in receipt.logs:
        try:
            decoded = contract.events.Broadcast().process_log(log)
            broadcast_id = decoded["args"]["broadcastId"]
        except Exception:
            pass

    print(f"📡 Broadcast created | TX: {tx_hash} | ID: {broadcast_id}")
    return broadcast_id


def execute_broadcast(broadcast_id):
    tx = contract.functions.executeBroadcast(
        broadcast_id
    ).build_transaction({
        "from": SENDER,
        "nonce": get_nonce(),
        "gas": 200_000,
        "gasPrice": w3.eth.gas_price,
        "chainId": CHAIN_ID
    })

    tx_hash, receipt = sign_and_send(tx)
    print(f"✅ Broadcast {broadcast_id} executed | TX: {tx_hash}")

def bridge_op_to_arb():
    user = SENDER
    action = "BURN_OP_MINT_ARB"
    amount = 2_000_000_000 * 10**6  # sUSDC, 6 decimals
    destination_chain = "ARBITRUM"
    destination_address = SENDER
    ref = "OP→ARB BRIDGE"

    broadcast_id = create_broadcast(
        user,
        action,
        amount,
        destination_chain,
        destination_address,
        ref
    )

    if broadcast_id is not None:
        execute_broadcast(broadcast_id)



# =========================================================
# MAIN MENU
# =========================================================
def main():
    MENU = """
1) Swap ETH → USD
2) Mint USD
3) Transfer USD
4) Market Caps
5) Set USD Price (OWNER)
6) Bridge OP → ARB (Broadcast + Execute)
0) Exit
"""
    while True:
        print(MENU)
        choice = input("Select: ")

        if choice == "1":
            swap_eth_to_usd()
        elif choice == "2":
            mint_usd()
        elif choice == "3":
            transfer_usd()
        elif choice == "4":
            show_market_caps()
        elif choice == "5":
            set_usd_price()
        elif choice == "6":
            bridge_op_to_arb()
        elif choice == "0":
            break


if __name__ == "__main__":
    main()


