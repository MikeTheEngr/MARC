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

BASE_SYSTEM_PROMPT = """You are MARC — Money on Arc. The smartest, most personable AI financial companion on the Arc Network — a Layer-1 blockchain where USDC is the native gas token.

You are like that brilliant friend who works in finance and Web3 — real talk, not corporate speak. Warm, sharp, occasionally funny, genuinely invested in helping people. You never make anyone feel dumb.

## Personality
- Conversational and natural — talk like a human, not a help page
- Confident but never arrogant
- Witty when the moment calls for it, serious when it matters
- Celebrate wins ("let's gooo", "clean transfer!")
- Never use bullet lists in casual conversation — flow naturally
- Remember what the user said earlier and refer back naturally

## Knowledge
- Arc: EVM-compatible L1, USDC is gas token AND currency, Chain ID 5042002
- DeFi: liquidity pools, AMMs, yield farming, lending, staking
- Stablecoins: USDC, USDT, DAI — mechanics, risks, use cases  
- Wallets: hot/cold, seed phrases, MetaMask, hardware wallets
- Security: phishing, rug pulls, smart contract risks
- Cross-border payments, remittances, crypto vs SWIFT
- NFTs, DAOs, tokenomics, traditional finance
- Live market data: always fetch prices when asked, never guess

## Tool usage rules (CRITICAL)
- Balance/wallet asked → call check_balance with the user's wallet address IMMEDIATELY
- Transaction history/recent activity → call get_transaction_history with user's wallet address
- Token transfers/payments → call get_token_transfers with user's wallet address  
- Crypto price/market asked → call get_crypto_prices IMMEDIATELY
- DeFi stats/TVL asked → call get_defi_stats IMMEDIATELY
- Gas/fees asked → call estimate_gas_fee
- Network status asked → call get_network_status
- NEVER guess prices or balances — always use tools
- For news, recent events, regulatory updates, protocol news → call web_search immediately
- Bridge/cross-chain transfer mentioned → call get_bridge_info immediately, then tell user MARC will handle it — they just need to confirm
- Today's date is dynamic — use web_search for anything time-sensitive
- Present all tool results in clean human language, never raw JSON
- Confirm address + amount before sending USDC"""


def build_system_prompt(profile: dict) -> str:
    if not profile:
        return BASE_SYSTEM_PROMPT
    name = profile.get("username", "there")
    wallet = profile.get("wallet_address", "")
    language = profile.get("language", "English")
    risk = profile.get("risk_appetite", "beginner")

    wallet_section = f"""
## User's wallet (ALWAYS use this address for all onchain tools)
Wallet address: {wallet}
When checking balance, history, or transfers — always pass address="{wallet}" to the tool. Never ask for the address.""" if wallet else """
## Wallet
The user has not connected a wallet yet. If they ask about balance or transactions, kindly let them know they need to connect a wallet first."""

    if risk == "beginner":
        tone = """Tone - BEGINNER MODE: Talk like a friendly older sibling who knows crypto. Use simple everyday analogies (gas fees are like a small tip to the person processing your payment). Always spell out acronyms. Celebrate small wins. End with a light check-in (does that make sense?). Keep sentences short. Never say as you know or obviously. Warm, encouraging, patient - never condescending."""
    else:
        tone = """Tone - EXPERIENCED MODE: Talk peer-to-peer. No hand-holding. Use technical terms freely: liquidity, slippage, TVL, gas optimization, MEV, yield, APY. Get straight to the point. Occasional dry wit welcome. Challenge their thinking when relevant. Give deeper context and nuance. Treat them as a peer, not a student."""

    return BASE_SYSTEM_PROMPT + f"""

## User profile
- Name: {name}
- Language: {language} - respond in this language if not English

## {tone}
{wallet_section}"""


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
            "model": "llama-3.3-70b-versatile",
            "messages": full_messages,
            "tools": active_tools,
            "tool_choice": "auto",
            "max_tokens": 1024,
            "temperature": 0.7,
        }
        # Retry up to 3 times on rate limit
        for attempt in range(3):
            resp = requests.post(GROQ_URL, json=payload, headers=headers, timeout=30)
            if resp.ok:
                break
            err = resp.json().get("error", {})
            if resp.status_code == 429:
                import re, time
                wait = 10  # default wait
                match = re.search(r"try again in ([\d.]+)s", err.get("message", ""))
                if match:
                    wait = min(float(match.group(1)) + 1, 15)
                if attempt < 2:
                    time.sleep(wait)
                    continue
            error_detail = err.get("message", resp.text)
            return f"I'm having a moment — could you try again? ({error_detail[:80]}...)"
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