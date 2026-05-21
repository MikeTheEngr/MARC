import json
import os
import requests
from dotenv import load_dotenv
from arc_tools import check_balance, send_usdc, estimate_gas_fee, get_transaction_info, get_network_status

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

TOOL_MAP = {
    "check_balance": check_balance,
    "send_usdc": send_usdc,
    "estimate_gas_fee": estimate_gas_fee,
    "get_transaction_info": get_transaction_info,
    "get_network_status": get_network_status,
}

TOOLS = [
    {"type": "function", "function": {"name": "check_balance", "description": "Check USDC wallet balance on Arc Testnet. Call IMMEDIATELY when user asks about wallet or balance — no address needed.", "parameters": {"type": "object", "properties": {"address": {"type": "string", "description": "Optional wallet address"}}, "required": []}}},
    {"type": "function", "function": {"name": "send_usdc", "description": "Send USDC to a wallet address. Always confirm with user before calling.", "parameters": {"type": "object", "properties": {"to_address": {"type": "string"}, "amount": {"type": "number"}}, "required": ["to_address", "amount"]}}},
    {"type": "function", "function": {"name": "estimate_gas_fee", "description": "Estimate current gas fees on Arc Testnet.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "get_transaction_info", "description": "Get details of a transaction by its hash.", "parameters": {"type": "object", "properties": {"tx_hash": {"type": "string"}}, "required": ["tx_hash"]}}},
    {"type": "function", "function": {"name": "get_network_status", "description": "Check Arc Testnet connection and latest block.", "parameters": {"type": "object", "properties": {}, "required": []}}},
]

BASE_SYSTEM_PROMPT = """You are MARC — Money on Arc. You are the smartest, most personable AI financial companion on the Arc Network — a Layer-1 blockchain where USDC is the native gas token.

You are like that brilliant friend who works in finance and Web3 — real talk, not corporate speak. Warm, sharp, occasionally funny, genuinely invested in helping people. You never make anyone feel dumb.

Your personality:
- Conversational and natural — talk like a human, not a help page
- Confident but never arrogant — share knowledge generously
- Witty when the moment calls for it, serious when it matters
- Celebrate wins ("let's gooo", "clean transfer!")
- Ask smart follow-up questions when needed
- Never use bullet lists in casual conversation — flow naturally
- Remember what the user said earlier and refer back naturally

What you know:
- Arc: EVM-compatible L1, USDC is gas token AND currency, Chain ID 5042002
- DeFi: liquidity pools, AMMs, yield farming, lending, staking
- Stablecoins: USDC, USDT, DAI — mechanics, risks, use cases
- Wallets: hot/cold, seed phrases, MetaMask, hardware wallets
- Security: phishing, rug pulls, smart contract risks
- Cross-border payments, remittances, crypto vs SWIFT
- NFTs, DAOs, tokenomics, traditional finance

Tool rules:
- Wallet or balance mentioned → call check_balance IMMEDIATELY with no arguments
- Present results in clean human language, never raw JSON
- Confirm address + amount before sending
- Mention testnet lightly when relevant, don't repeat it"""


def build_system_prompt(profile: dict) -> str:
    if not profile:
        return BASE_SYSTEM_PROMPT
    name = profile.get("username", "there")
    wallet = profile.get("wallet_address", "not connected")
    language = profile.get("language", "English")
    risk = profile.get("risk_appetite", "beginner")
    return BASE_SYSTEM_PROMPT + f"""

User profile — personalize every response:
- Name: {name} — use naturally in conversation
- Wallet: {wallet}
- Language: {language} — respond in this language if not English
- Experience: {risk} — {'keep it simple, encourage and reassure' if risk == 'beginner' else 'use technical terms, treat as peer'}"""


def run_agent(messages: list, profile: dict = None) -> str:
    system_prompt = build_system_prompt(profile or {})

    full_messages = [{"role": "system", "content": system_prompt}] + [
        {"role": m["role"], "content": m["content"] if isinstance(m["content"], str) else json.dumps(m["content"])}
        for m in messages
    ]

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    for _ in range(5):
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": full_messages,
            "tools": TOOLS,
            "tool_choice": "auto",
            "max_tokens": 1024,
            "temperature": 0.7,
        }

        resp = requests.post(GROQ_URL, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        message = data["choices"][0]["message"]
        tool_calls = message.get("tool_calls", [])

        if not tool_calls:
            return message.get("content") or "I'm not sure how to respond — could you rephrase?"

        # Add assistant message with tool calls
        full_messages.append({
            "role": "assistant",
            "content": message.get("content") or "",
            "tool_calls": tool_calls,
        })

        # Execute each tool
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

            full_messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": json.dumps(result),
            })

    return "I ran into a snag — could you try again?"