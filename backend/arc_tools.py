from web3 import Web3
from dotenv import load_dotenv
import os

load_dotenv()

ARC_RPC_URL = os.getenv("ARC_RPC_URL", "https://rpc.testnet.arc.network")
WALLET_PRIVATE_KEY = os.getenv("WALLET_PRIVATE_KEY", "")

# ARC Testnet USDC contract address
USDC_ADDRESS = "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238"

# Minimal ERC20 ABI for balance + transfer
ERC20_ABI = [
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"name": "recipient", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
]

w3 = Web3(Web3.HTTPProvider(ARC_RPC_URL))


def get_wallet_address() -> str:
    """Derive wallet address from private key."""
    if not WALLET_PRIVATE_KEY:
        return "No wallet configured"
    account = w3.eth.account.from_key(WALLET_PRIVATE_KEY)
    return account.address


def check_balance(address: str = None) -> dict:
    """Check USDC balance of a wallet address on ARC Testnet."""
    try:
        if not address:
            address = get_wallet_address()
        if address == "No wallet configured":
            return {"error": "No wallet private key configured in .env"}

        checksummed = Web3.to_checksum_address(address)
        usdc = w3.eth.contract(
            address=Web3.to_checksum_address(USDC_ADDRESS), abi=ERC20_ABI
        )
        raw_balance = usdc.functions.balanceOf(checksummed).call()
        decimals = usdc.functions.decimals().call()
        balance = raw_balance / (10**decimals)

        # Also get native gas (USDC on ARC)
        native_wei = w3.eth.get_balance(checksummed)
        native_usdc = w3.from_wei(native_wei, "ether")

        return {
            "address": address,
            "usdc_balance": f"{balance:.6f} USDC",
            "native_gas_balance": f"{float(native_usdc):.6f} USDC",
            "network": "Arc Testnet",
            "chain_id": 5042002,
        }
    except Exception as e:
        return {"error": str(e)}


def send_usdc(to_address: str, amount: float) -> dict:
    """Send USDC to an address on ARC Testnet."""
    try:
        if not WALLET_PRIVATE_KEY:
            return {"error": "No wallet private key configured in .env"}

        account = w3.eth.account.from_key(WALLET_PRIVATE_KEY)
        usdc = w3.eth.contract(
            address=Web3.to_checksum_address(USDC_ADDRESS), abi=ERC20_ABI
        )
        decimals = usdc.functions.decimals().call()
        amount_raw = int(amount * (10**decimals))

        nonce = w3.eth.get_transaction_count(account.address)
        gas_price = w3.eth.gas_price

        txn = usdc.functions.transfer(
            Web3.to_checksum_address(to_address), amount_raw
        ).build_transaction(
            {
                "chainId": 5042002,
                "gas": 100000,
                "gasPrice": gas_price,
                "nonce": nonce,
            }
        )

        signed = w3.eth.account.sign_transaction(txn, WALLET_PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)

        return {
            "status": "success" if receipt.status == 1 else "failed",
            "tx_hash": tx_hash.hex(),
            "from": account.address,
            "to": to_address,
            "amount": f"{amount} USDC",
            "explorer_url": f"https://testnet.arcscan.app/tx/{tx_hash.hex()}",
        }
    except Exception as e:
        return {"error": str(e)}


def estimate_gas_fee() -> dict:
    """Estimate current gas fee on ARC Testnet."""
    try:
        gas_price_wei = w3.eth.gas_price
        gas_price_gwei = w3.from_wei(gas_price_wei, "gwei")

        # Typical transfer uses ~65000 gas
        estimated_transfer_fee = float(gas_price_gwei) * 65000 / 1e9
        estimated_contract_fee = float(gas_price_gwei) * 100000 / 1e9

        return {
            "gas_price_gwei": float(gas_price_gwei),
            "estimated_transfer_fee": f"{estimated_transfer_fee:.8f} USDC",
            "estimated_contract_interaction": f"{estimated_contract_fee:.8f} USDC",
            "note": "ARC uses USDC as gas token — fees are very low",
            "network": "Arc Testnet",
        }
    except Exception as e:
        return {"error": str(e)}


def get_transaction_info(tx_hash: str) -> dict:
    """Get details of a transaction by hash."""
    try:
        tx = w3.eth.get_transaction(tx_hash)
        receipt = w3.eth.get_transaction_receipt(tx_hash)

        return {
            "tx_hash": tx_hash,
            "status": "success" if receipt.status == 1 else "failed",
            "from": tx["from"],
            "to": tx["to"],
            "block_number": receipt.blockNumber,
            "gas_used": receipt.gasUsed,
            "explorer_url": f"https://testnet.arcscan.app/tx/{tx_hash}",
        }
    except Exception as e:
        return {"error": str(e)}


def get_network_status() -> dict:
    """Check ARC Testnet connection and latest block."""
    try:
        connected = w3.is_connected()
        if not connected:
            return {"error": "Cannot connect to ARC Testnet RPC"}

        latest_block = w3.eth.block_number
        chain_id = w3.eth.chain_id

        return {
            "connected": connected,
            "network": "Arc Testnet",
            "chain_id": chain_id,
            "latest_block": latest_block,
            "rpc_url": ARC_RPC_URL,
            "explorer": "https://testnet.arcscan.app",
            "faucet": "https://faucet.circle.com",
        }
    except Exception as e:
        return {"error": str(e)}