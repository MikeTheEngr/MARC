import os
import json
import requests
from web3 import Web3
from duckduckgo_search import DDGS
from dotenv import load_dotenv

load_dotenv()

ARC_RPC_URL = os.getenv("ARC_RPC_URL", "https://rpc.testnet.arc.network")
EXPLORER_API = "https://testnet.arcscan.app/api/v2"

# USDC contract on Arc Testnet
USDC_ADDRESS = "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238"

ERC20_ABI = [
    {"inputs": [{"name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "recipient", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "stateMutability": "view", "type": "function"},
]

w3 = Web3(Web3.HTTPProvider(ARC_RPC_URL))


# ── Balance ───────────────────────────────────────────────────
def check_balance(address: str = None) -> dict:
    """Check USDC balance of a wallet address on ARC Testnet."""
    try:
        if not address:
            return {"error": "No wallet address provided. Connect your wallet first."}
        checksummed = Web3.to_checksum_address(address)
        usdc = w3.eth.contract(address=Web3.to_checksum_address(USDC_ADDRESS), abi=ERC20_ABI)
        raw = usdc.functions.balanceOf(checksummed).call()
        decimals = usdc.functions.decimals().call()
        balance = raw / (10 ** decimals)
        native_wei = w3.eth.get_balance(checksummed)
        native = float(w3.from_wei(native_wei, "ether"))
        return {
            "address": address,
            "usdc_balance": f"{balance:.4f} USDC",
            "native_gas_balance": f"{native:.6f} USDC",
            "network": "Arc Testnet",
            "explorer": f"https://testnet.arcscan.app/address/{address}",
        }
    except Exception as e:
        return {"error": str(e)}


# ── Send ──────────────────────────────────────────────────────
def send_usdc(to_address: str, amount: float) -> dict:
    """Send USDC to an address on ARC Testnet."""
    try:
        private_key = os.getenv("WALLET_PRIVATE_KEY", "")
        if not private_key:
            return {"error": "No wallet private key configured. Add WALLET_PRIVATE_KEY to .env"}
        account = w3.eth.account.from_key(private_key)
        usdc = w3.eth.contract(address=Web3.to_checksum_address(USDC_ADDRESS), abi=ERC20_ABI)
        decimals = usdc.functions.decimals().call()
        amount_raw = int(amount * (10 ** decimals))
        nonce = w3.eth.get_transaction_count(account.address)
        txn = usdc.functions.transfer(
            Web3.to_checksum_address(to_address), amount_raw
        ).build_transaction({"chainId": 5042002, "gas": 100000, "gasPrice": w3.eth.gas_price, "nonce": nonce})
        signed = w3.eth.account.sign_transaction(txn, private_key)
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


# ── Gas ───────────────────────────────────────────────────────
def estimate_gas_fee() -> dict:
    """Estimate current gas fees on ARC Testnet."""
    try:
        gas_price_wei = w3.eth.gas_price
        gas_price_gwei = float(w3.from_wei(gas_price_wei, "gwei"))
        transfer_fee = gas_price_gwei * 65000 / 1e9
        contract_fee = gas_price_gwei * 100000 / 1e9
        return {
            "gas_price_gwei": round(gas_price_gwei, 6),
            "estimated_transfer_fee": f"{transfer_fee:.8f} USDC",
            "estimated_contract_interaction": f"{contract_fee:.8f} USDC",
            "note": "Arc uses USDC as gas token — fees are extremely low",
            "network": "Arc Testnet",
        }
    except Exception as e:
        return {"error": str(e)}


# ── Transaction info ──────────────────────────────────────────
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


# ── Transaction history ───────────────────────────────────────
def get_transaction_history(address: str = None, limit: int = 10) -> dict:
    """Get recent transactions for a wallet address."""
    try:
        if not address:
            return {"error": "No wallet address provided."}
        checksummed = Web3.to_checksum_address(address)

        # Try Blockscout-compatible explorer API
        try:
            resp = requests.get(
                f"{EXPLORER_API}/addresses/{checksummed}/transactions",
                params={"limit": limit, "sort": "desc"},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                txs = data.get("items", [])
                if txs:
                    formatted = []
                    for tx in txs[:limit]:
                        formatted.append({
                            "hash": tx.get("hash", "")[:12] + "...",
                            "from": tx.get("from", {}).get("hash", ""),
                            "to": tx.get("to", {}).get("hash", "") if tx.get("to") else "Contract creation",
                            "value": tx.get("value", "0"),
                            "status": tx.get("status", "unknown"),
                            "timestamp": tx.get("timestamp", ""),
                            "explorer": f"https://testnet.arcscan.app/tx/{tx.get('hash','')}",
                        })
                    return {"address": address, "transactions": formatted, "count": len(formatted)}
        except Exception:
            pass

        # Fallback: use RPC to get recent blocks and filter
        latest = w3.eth.block_number
        txs = []
        for block_num in range(latest, max(latest - 200, 0), -1):
            if len(txs) >= limit:
                break
            try:
                block = w3.eth.get_block(block_num, full_transactions=True)
                for tx in block.transactions:
                    if tx["from"].lower() == checksummed.lower() or (tx["to"] and tx["to"].lower() == checksummed.lower()):
                        txs.append({
                            "hash": tx["hash"].hex()[:12] + "...",
                            "from": tx["from"],
                            "to": tx["to"] or "Contract creation",
                            "block": block_num,
                            "explorer": f"https://testnet.arcscan.app/tx/{tx['hash'].hex()}",
                        })
                        if len(txs) >= limit:
                            break
            except Exception:
                continue

        if not txs:
            return {"address": address, "message": "No recent transactions found for this address on Arc Testnet.", "explorer": f"https://testnet.arcscan.app/address/{address}"}

        return {"address": address, "transactions": txs, "count": len(txs)}
    except Exception as e:
        return {"error": str(e)}


# ── Token transfers ───────────────────────────────────────────
def get_token_transfers(address: str = None) -> dict:
    """Get recent USDC token transfers for a wallet address."""
    try:
        if not address:
            return {"error": "No wallet address provided."}
        checksummed = Web3.to_checksum_address(address)

        try:
            resp = requests.get(
                f"{EXPLORER_API}/addresses/{checksummed}/token-transfers",
                params={"limit": 10, "type": "ERC-20"},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                transfers = data.get("items", [])
                if transfers:
                    formatted = []
                    for t in transfers[:10]:
                        token = t.get("token", {})
                        total = t.get("total", {})
                        decimals = int(token.get("decimals", 6))
                        raw_value = int(total.get("value", 0))
                        value = raw_value / (10 ** decimals)
                        direction = "received" if t.get("to", {}).get("hash", "").lower() == checksummed.lower() else "sent"
                        formatted.append({
                            "direction": direction,
                            "amount": f"{value:.4f} {token.get('symbol', 'USDC')}",
                            "from": t.get("from", {}).get("hash", ""),
                            "to": t.get("to", {}).get("hash", ""),
                            "tx_hash": t.get("tx_hash", "")[:12] + "...",
                            "explorer": f"https://testnet.arcscan.app/tx/{t.get('tx_hash','')}",
                        })
                    return {"address": address, "transfers": formatted, "count": len(formatted)}
        except Exception:
            pass

        return {"address": address, "message": "No USDC transfers found. Try checking the explorer directly.", "explorer": f"https://testnet.arcscan.app/address/{address}"}
    except Exception as e:
        return {"error": str(e)}


# ── Network status ────────────────────────────────────────────
def get_network_status() -> dict:
    """Check ARC Testnet connection and latest block."""
    try:
        connected = w3.is_connected()
        if not connected:
            return {"error": "Cannot connect to ARC Testnet RPC"}
        latest_block = w3.eth.block_number
        gas_price = float(w3.from_wei(w3.eth.gas_price, "gwei"))
        return {
            "connected": connected,
            "network": "Arc Testnet",
            "chain_id": w3.eth.chain_id,
            "latest_block": latest_block,
            "gas_price_gwei": round(gas_price, 6),
            "rpc_url": ARC_RPC_URL,
            "explorer": "https://testnet.arcscan.app",
            "faucet": "https://faucet.circle.com",
            "status": "operational",
        }
    except Exception as e:
        return {"error": str(e)}


# ── Crypto prices (CoinGecko free API) ───────────────────────
def get_crypto_prices(coins: str = "bitcoin,ethereum,usd-coin") -> dict:
    """Get live crypto prices from CoinGecko (free, no key needed)."""
    try:
        resp = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={
                "ids": coins,
                "vs_currencies": "usd",
                "include_24hr_change": "true",
                "include_market_cap": "true",
            },
            timeout=10,
        )
        if resp.status_code != 200:
            return {"error": f"CoinGecko API error: {resp.status_code}"}
        data = resp.json()
        result = {}
        name_map = {"bitcoin": "Bitcoin (BTC)", "ethereum": "Ethereum (ETH)", "usd-coin": "USDC"}
        for coin_id, info in data.items():
            change = info.get("usd_24h_change", 0) or 0
            result[name_map.get(coin_id, coin_id)] = {
                "price": f"${info['usd']:,.2f}",
                "24h_change": f"{change:+.2f}%",
                "market_cap": f"${info.get('usd_market_cap', 0):,.0f}",
                "trend": "📈" if change > 0 else "📉" if change < 0 else "➡️",
            }
        return {"prices": result, "source": "CoinGecko", "note": "Live market data"}
    except Exception as e:
        return {"error": str(e)}


# ── DeFi market overview ──────────────────────────────────────
def get_defi_stats() -> dict:
    """Get DeFi market overview — total TVL and top protocols."""
    try:
        # Use lightweight global TVL endpoint
        tvl_resp = requests.get("https://api.llama.fi/v2/globalTvl", timeout=8)
        total_tvl = None
        if tvl_resp.status_code == 200:
            total_tvl = tvl_resp.json()

        # Get top protocols from the simpler endpoint
        top_resp = requests.get("https://api.llama.fi/protocols", timeout=8)
        top_protocols = []
        if top_resp.status_code == 200:
            protocols = top_resp.json()
            top = sorted([p for p in protocols if p.get("tvl", 0) > 0], key=lambda x: x.get("tvl", 0), reverse=True)[:5]
            top_protocols = [{"name": p["name"], "tvl": f"${p['tvl']/1e9:.2f}B", "category": p.get("category", "")} for p in top]
            if total_tvl is None:
                total_tvl = sum(p.get("tvl", 0) for p in protocols if p.get("tvl", 0) > 0)

        if total_tvl is None:
            return {"error": "DeFi stats temporarily unavailable"}

        tvl_display = f"${float(total_tvl)/1e9:.1f}B" if isinstance(total_tvl, (int, float)) else str(total_tvl)
        return {
            "total_defi_tvl": tvl_display,
            "top_protocols": top_protocols,
            "source": "DeFi Llama",
        }
    except Exception as e:
        return {"error": f"DeFi stats unavailable: {str(e)}"}


# ── Web search (real-time knowledge) ─────────────────────────
def web_search(query: str) -> dict:
    """Search the web for real-time information. Use for news, recent events, current crypto prices not in tools, protocol updates, anything time-sensitive."""
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=4):
                results.append({
                    "title": r.get("title", ""),
                    "snippet": r.get("body", ""),
                    "url": r.get("href", ""),
                })
        if not results:
            return {"error": "No results found for that query."}
        return {"query": query, "results": results, "source": "DuckDuckGo"}
    except Exception as e:
        return {"error": f"Search failed: {str(e)}"}


# ── Bridge info ───────────────────────────────────────────────
def get_bridge_info(from_chain: str = "Ethereum Sepolia", amount: float = None) -> dict:
    """Get bridging information and guide for moving USDC to Arc Testnet."""
    try:
        supported_chains = [
            {"chain": "Ethereum Sepolia", "chain_id": 11155111, "faucet": "https://sepoliafaucet.com"},
            {"chain": "Base Sepolia", "chain_id": 84532, "faucet": "https://faucet.base.org"},
        ]
        return {
            "bridge_protocol": "Circle CCTP v2",
            "destination": "Arc Testnet (Chain ID: 5042002)",
            "supported_source_chains": supported_chains,
            "steps": [
                "1. Approve USDC spend on source chain (MetaMask signature)",
                "2. Burn USDC on source chain (MetaMask signature)",
                "3. Circle attestation (~20 seconds — automatic)",
                "4. USDC minted on Arc Testnet (automatic via Orbit relayer)",
            ],
            "estimated_time": "~30-60 seconds",
            "fees": "Circle protocol fee: 0-14 bps. No additional fees.",
            "amount_requested": amount,
            "from_chain": from_chain,
            "note": "Only 2 MetaMask signatures needed. Circle handles the rest automatically.",
        }
    except Exception as e:
        return {"error": str(e)}