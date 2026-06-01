import json
import os
import requests
import time
import re
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
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

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

BASE_SYSTEM_PROMPT = """You are MARC — Money on Arc. You are two things at once: a seasoned financial expert with deep knowledge of crypto, DeFi, and traditional finance, and an autonomous onchain agent that executes transactions on behalf of users on the Arc Network.

## As a financial expert
You think like a CFO, a DeFi analyst, and a crypto-native advisor rolled into one. You give real opinions, not just facts. You notice patterns. You ask smart follow-up questions. You warn users about risks proactively. You connect macro trends to their specific situation. You never guess — you use tools to get real data, then interpret it with expertise.

## As an autonomous agent
You act, not just advise. When a user says "check my balance", you check it — immediately, without asking. When they say "show my last 5 transactions", you fetch and interpret them. When they say "send 10 USDC", you confirm once then execute. You chain actions when needed. You are the user's hands on the blockchain.

## Arc Network
EVM-compatible L1. USDC is the native gas token AND primary currency. Chain ID: 5042002. RPC: rpc.testnet.arc.network. Explorer: testnet.arcscan.app. MARC currently operates on Arc Testnet — no real funds at risk.

## Balance checking
MARC checks USDC balance on Arc Testnet only. When asked about balance, always clarify: "This is your USDC balance on Arc Testnet." If user asks about other tokens or other chains, explain what MARC currently supports and what's coming.

## Tools — execute proactively, never ask permission
- check_balance → ANY mention of wallet, balance, funds — call immediately with user wallet
- get_transaction_history → transactions, activity, history — call immediately
- get_token_transfers → transfers, sent, received — call immediately
- send_usdc → confirm address + amount once, then execute
- estimate_gas_fee → fees, costs, gas
- get_transaction_info → tx hash lookup
- get_network_status → network, RPC, Arc status
- get_crypto_prices → prices, BTC, ETH, market data
- get_defi_stats → TVL, DeFi protocols
- get_bridge_info → bridging, cross-chain
- web_search → news, recent events, anything current

## Communication style
Talk like a brilliant friend who happens to be a financial expert. Natural, direct, occasionally witty. No bullet lists in conversation — flow naturally. No corporate speak. Celebrate wins. Reference earlier context. Present all tool data in clean human language, never raw JSON."""


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


def call_groq(messages, tools, active_tools):
    """Call Groq API with fallback models."""
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    MODELS = ["llama-3.3-70b-versatile", "gemma2-9b-it", "llama-3.1-8b-instant"]
    for model in MODELS:
        payload = {
            "model": model,
            "messages": messages,
            "tools": active_tools,
            "tool_choice": "auto",
            "max_tokens": 1024,
            "temperature": 0.7,
        }
        for attempt in range(2):
            try:
                resp = requests.post(GROQ_URL, json=payload, headers=headers, timeout=30)
                print(f"[GROQ] model={model} status={resp.status_code}")
                if resp.ok:
                    return resp.json()
                if resp.status_code == 429:
                    err_msg = resp.json().get("error", {}).get("message", "")
                    print(f"[GROQ] 429 rate limit: {err_msg[:100]}")
                    match = re.search(r"try again in ([\d.]+)s", err_msg)
                    wait = min(float(match.group(1)) + 0.5, 8) if match else 3
                    if attempt == 0:
                        time.sleep(wait)
                        continue
                else:
                    print(f"[GROQ] error: {resp.text[:200]}")
            except Exception as e:
                print(f"[GROQ] exception: {e}")
            break
    return None


def call_gemini(messages, tools):
    """Call Gemini API as fallback — 1500 req/day free."""
    if not GEMINI_API_KEY:
        return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

    # Convert messages to Gemini format
    system_parts = [m for m in messages if m["role"] == "system"]
    chat_messages = [m for m in messages if m["role"] != "system"]

    gemini_tools = [{
        "function_declarations": [
            {
                "name": t["function"]["name"],
                "description": t["function"]["description"],
                "parameters": t["function"]["parameters"],
            }
            for t in tools
        ]
    }]

    contents = []
    for m in chat_messages:
        role = "model" if m["role"] == "assistant" else "user"
        content = m.get("content", "")
        if isinstance(content, str) and content:
            contents.append({"role": role, "parts": [{"text": content}]})
        elif m["role"] == "tool":
            contents.append({"role": "user", "parts": [{"functionResponse": {"name": "tool", "response": {"result": content}}}]})

    if not contents:
        return None

    payload = {
        "contents": contents,
        "tools": gemini_tools,
        "tool_config": {"function_calling_config": {"mode": "AUTO"}},
    }
    if system_parts:
        payload["system_instruction"] = {"parts": [{"text": system_parts[0]["content"]}]}

    try:
        resp = requests.post(url, json=payload, timeout=30)
        print(f"[GEMINI] status={resp.status_code}")
        if not resp.ok:
            print(f"[GEMINI] error: {resp.text[:200]}")
            return None
        data = resp.json()
        candidate = data.get("candidates", [{}])[0]
        parts = candidate.get("content", {}).get("parts", [])
        text_parts = [p.get("text", "") for p in parts if "text" in p]
        fn_calls = [p.get("functionCall") for p in parts if "functionCall" in p]
        return {"gemini": True, "text": " ".join(text_parts), "fn_calls": fn_calls}
    except Exception:
        return None


def run_agent(messages: list, profile: dict = None) -> str:
    """Run MARC — Gemini primary (1500/day free), Groq fallback (fast)."""
    system_prompt = build_system_prompt(profile or {})
    full_messages = [{"role": "system", "content": system_prompt}] + [
        {"role": m["role"], "content": m["content"] if isinstance(m["content"], str) else json.dumps(m["content"])}
        for m in messages
    ]

    last_msg = messages[-1]["content"].lower() if messages else ""
    market_keywords = ["price", "bitcoin", "btc", "eth", "ethereum", "market", "tvl", "defi", "worth", "cost", "value", "news", "latest", "recent", "today", "happened", "update", "regulation"]
    active_tools = TOOLS_MARKET if any(k in last_msg for k in market_keywords) else TOOLS_ONCHAIN

    for _ in range(5):
        # Try Groq first (faster), fall back to Gemini
        data = call_groq(full_messages, TOOLS, active_tools)

        if data:
            # Groq response
            message = data["choices"][0]["message"]
            tool_calls = message.get("tool_calls", [])
            raw_content = message.get("content") or ""

            if not tool_calls and "<function=" in raw_content:
                full_messages.append({"role": "assistant", "content": raw_content})
                full_messages.append({"role": "user", "content": "Use the actual tool — don't write the function call as text."})
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

        else:
            # Groq failed — try Gemini
            gemini = call_gemini(full_messages, active_tools)
            if not gemini:
                return "I'm having trouble connecting right now — please try again in a moment!"

            if not gemini["fn_calls"]:
                return gemini["text"] or "I'm not sure how to respond — could you rephrase?"

            # Execute Gemini tool calls
            for fc in gemini["fn_calls"]:
                fn_name = fc.get("name", "")
                fn_args = fc.get("args", {}) or {}
                try:
                    result = TOOL_MAP[fn_name](**fn_args) if fn_name in TOOL_MAP else {"error": f"Unknown tool: {fn_name}"}
                except Exception as e:
                    result = {"error": str(e)}
                full_messages.append({"role": "assistant", "content": gemini["text"] or ""})
                full_messages.append({"role": "tool", "tool_call_id": fn_name, "content": json.dumps(result)})

    print("[MARC] All retries exhausted")
    return "I ran into a snag — could you try again?"