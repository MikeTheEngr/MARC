import json
import os
import requests
from dotenv import load_dotenv
from arc_tools import (
    check_balance, send_usdc, estimate_gas_fee,
    get_transaction_info, get_transaction_history,
    get_token_transfers, get_network_status,
    get_crypto_prices, get_defi_stats, web_search,
    get_bridge_info,
)

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

TOOL_MAP = {
    "check_balance": check_balance,
    "send_usdc": send_usdc,
    "estimate_gas_fee": estimate_gas_fee,
    "get_transaction_info": get_transaction_info,
    "get_transaction_history": get_transaction_history,
    "get_token_transfers": get_token_transfers,
    "get_network_status": get_network_status,
    "get_crypto_prices": get_crypto_prices,
    "get_defi_stats": get_defi_stats,
    "web_search": web_search,
    "get_bridge_info": get_bridge_info,
}

TOOLS = [
    {"type": "function", "function": {
        "name": "check_balance",
        "description": "Check USDC wallet balance on Arc Testnet. Call IMMEDIATELY when user asks about wallet or balance — pass the user's wallet address from their profile.",
        "parameters": {"type": "object", "properties": {"address": {"type": "string", "description": "Wallet address to check"}}, "required": ["address"]},
    }},
    {"type": "function", "function": {
        "name": "send_usdc",
        "description": "Send USDC to a wallet address on Arc Testnet. Always confirm address and amount with user before calling.",
        "parameters": {"type": "object", "properties": {"to_address": {"type": "string"}, "amount": {"type": "number"}}, "required": ["to_address", "amount"]},
    }},
    {"type": "function", "function": {
        "name": "estimate_gas_fee",
        "description": "Estimate current gas fees on Arc Testnet in USDC.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    }},
    {"type": "function", "function": {
        "name": "get_transaction_info",
        "description": "Get details of a specific transaction by its hash.",
        "parameters": {"type": "object", "properties": {"tx_hash": {"type": "string"}}, "required": ["tx_hash"]},
    }},
    {"type": "function", "function": {
        "name": "get_transaction_history",
        "description": "Get recent transaction history for a wallet address. Call this when user asks about recent transactions, activity, or history.",
        "parameters": {"type": "object", "properties": {"address": {"type": "string"}, "limit": {"type": "integer", "description": "Number of transactions to fetch (default 10)"}}, "required": ["address"]},
    }},
    {"type": "function", "function": {
        "name": "get_token_transfers",
        "description": "Get recent USDC token transfers (sent/received) for a wallet. Call when user asks about transfers, payments sent or received.",
        "parameters": {"type": "object", "properties": {"address": {"type": "string"}}, "required": ["address"]},
    }},
    {"type": "function", "function": {
        "name": "get_network_status",
        "description": "Check Arc Testnet connection, latest block, and gas price.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    }},
    {"type": "function", "function": {
        "name": "get_crypto_prices",
        "description": "Get live cryptocurrency prices from CoinGecko. Call when user asks about BTC, ETH, USDC prices, market data, or crypto prices.",
        "parameters": {"type": "object", "properties": {"coins": {"type": "string", "description": "Comma-separated CoinGecko coin IDs e.g. 'bitcoin,ethereum,usd-coin'"}}, "required": []},
    }},
    {"type": "function", "function": {
        "name": "get_defi_stats",
        "description": "Get DeFi market overview including total TVL and top protocols. Call when user asks about DeFi market, TVL, or top DeFi protocols.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    }},
    {"type": "function", "function": {
        "name": "get_bridge_info",
        "description": "Get bridging information for moving USDC to Arc Testnet. Call when user asks to bridge, transfer from another chain, or move USDC across chains.",
        "parameters": {"type": "object", "properties": {"from_chain": {"type": "string", "description": "Source chain e.g. Ethereum Sepolia, Base Sepolia"}, "amount": {"type": "number", "description": "Amount of USDC to bridge"}}, "required": []},
    }},
    {"type": "function", "function": {
        "name": "web_search",
        "description": "Search the web for real-time information. Call this for: latest crypto news, recent events, protocol updates, regulatory news, anything that happened recently, current trends. Do NOT use for prices or balances — use the dedicated tools for those.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "Search query"}}, "required": ["query"]},
    }},
]

# Groq supports max 8 tools reliably — use subset based on context
TOOLS_ONCHAIN = [t for t in TOOLS if t["function"]["name"] in ["check_balance","send_usdc","estimate_gas_fee","get_transaction_info","get_transaction_history","get_token_transfers","get_network_status","web_search","get_bridge_info"]]
TOOLS_MARKET = [t for t in TOOLS if t["function"]["name"] in ["get_crypto_prices","get_defi_stats","estimate_gas_fee","get_network_status","check_balance","get_transaction_history","web_search"]]

BASE_SYSTEM_PROMPT = """You are MARC — Money on Arc. An AI finance companion on Arc Network (EVM L1, USDC gas token, Chain ID 5042002).

Personality: warm, sharp, peer-level. Talk like a real person — no corporate speak, no bullet lists in conversation. Celebrate wins. Reference what the user said earlier.

Knowledge: Arc Network, DeFi, stablecoins, wallets, security, cross-chain, NFTs, DAOs, traditional finance, crypto markets.

Tools — call immediately when needed, never guess:
- check_balance → wallet/balance questions (use user wallet address)
- get_transaction_history → recent transactions/activity  
- get_token_transfers → USDC transfers in/out
- send_usdc → confirm address+amount first
- estimate_gas_fee → fee questions
- get_transaction_info → tx hash lookup
- get_network_status → network questions
- get_crypto_prices → price/market questions
- get_defi_stats → DeFi TVL questions
- get_bridge_info → bridge/cross-chain questions
- web_search → news, recent events, anything time-sensitive

Rules: present tool results in clean human language. Mention testnet lightly. Never raw JSON."""


def build_system_prompt(profile: dict) -> str:
    if not profile:
        return BASE_SYSTEM_PROMPT
    name = profile.get("username", "there")
    wallet = profile.get("wallet_address", "")
    language = profile.get("language", "English")
    risk = profile.get("risk_appetite", "beginner")

    if risk == "beginner":
        tone = "Tone: beginner mode — simple analogies, spell out jargon, check if they follow, warm and encouraging."
    else:
        tone = "Tone: experienced mode — peer-to-peer, technical terms ok, get straight to point, no hand-holding."

    wallet_note = f'User wallet: {wallet} — always pass this to onchain tools. Never ask for address.' if wallet else "No wallet connected — tell user to connect wallet for onchain actions."

    return BASE_SYSTEM_PROMPT + f"""

User: {name} | Lang: {language} | {tone}
{wallet_note}"""


def run_agent(messages: list, profile: dict = None) -> str:
    system_prompt = build_system_prompt(profile or {})
    full_messages = [{"role": "system", "content": system_prompt}] + [
        {"role": m["role"], "content": m["content"] if isinstance(m["content"], str) else json.dumps(m["content"])}
        for m in messages
    ]
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}

    # Pick tool set based on message content
    last_msg = messages[-1]["content"].lower() if messages else ""
    market_keywords = ["price", "bitcoin", "btc", "eth", "ethereum", "market", "tvl", "defi", "worth", "cost", "value", "news", "latest", "recent", "today", "happened", "update", "regulation"]
    active_tools = TOOLS_MARKET if any(k in last_msg for k in market_keywords) else TOOLS_ONCHAIN

    for _ in range(5):
        payload = {
            "model": model,
            "messages": full_messages,
            "tools": active_tools,
            "tool_choice": "auto",
            "max_tokens": 1024,
            "temperature": 0.7,
        }
        # Try primary model, fall back to alternatives on rate limit
        import re, time
        MODELS = ["llama-3.3-70b-versatile", "gemma2-9b-it", "llama-3.1-8b-instant"]
        resp = None
        for model in MODELS:
            payload["model"] = model
            for attempt in range(2):
                resp = requests.post(GROQ_URL, json=payload, headers=headers, timeout=30)
                if resp.ok:
                    break
                if resp.status_code == 429:
                    err_msg = resp.json().get("error", {}).get("message", "")
                    match = re.search(r"try again in ([\d.]+)s", err_msg)
                    wait = min(float(match.group(1)) + 0.5, 8) if match else 3
                    if attempt == 0:
                        time.sleep(wait)
                        continue
                break
            if resp and resp.ok:
                break

        if not resp or not resp.ok:
            error_detail = resp.json().get("error", {}).get("message", "Unknown error") if resp else "No response"
            return f"I'm at capacity right now — please try again in a few seconds!"
        data = resp.json()
        message = data["choices"][0]["message"]
        tool_calls = message.get("tool_calls", [])
        raw_content = message.get("content") or ""

        # Detect malformed tool call printed as text
        if not tool_calls and "<function=" in raw_content:
            full_messages.append({"role": "assistant", "content": raw_content})
            full_messages.append({"role": "user", "content": "Please use the actual tool — don't write the function call as text."})
            continue

        if not tool_calls:
            return raw_content or "I'm not sure how to respond — could you rephrase?"

        full_messages.append({
            "role": "assistant",
            "content": raw_content,
            "tool_calls": tool_calls,
        })

        for tc in tool_calls:
            fn_name = tc["function"]["name"]
            raw_args = tc["function"].get("arguments", "{}")
            try:
                fn_args = json.loads(raw_args) if raw_args and raw_args.strip() not in ("null", "") else {}
                if not isinstance(fn_args, dict):
                    fn_args = {}
            except Exception:
                fn_args = {}

            try:
                result = TOOL_MAP[fn_name](**fn_args) if fn_name in TOOL_MAP else {"error": f"Unknown tool: {fn_name}"}
            except Exception as e:
                result = {"error": str(e)}

            full_messages.append({"role": "tool", "tool_call_id": tc["id"], "content": json.dumps(result)})

    return "I ran into a snag — could you try again?"