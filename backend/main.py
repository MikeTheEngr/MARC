from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from agent import run_agent
from memory import get_history, save_history, clear_history
from auth import sign_up, sign_in, wallet_sign_in, get_profile
from Conversations import (
    create_conversation, get_conversations,
    get_conversation_messages, save_message,
    update_conversation_title, delete_conversation,
)

app = FastAPI(title="MARC API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Models ────────────────────────────────────────────────────
class SignUpRequest(BaseModel):
    email: str
    password: str
    username: str
    language: str = "English"
    risk_appetite: str = "beginner"

class SignInRequest(BaseModel):
    email: str
    password: str

class WalletSignInRequest(BaseModel):
    wallet_address: str
    username: Optional[str] = None
    language: str = "English"
    risk_appetite: str = "beginner"

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None

class NewConversationRequest(BaseModel):
    user_id: str
    title: str = "New Chat"


# ── Root ──────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "MARC API live", "network": "Arc Testnet"}


# ── Auth ──────────────────────────────────────────────────────
@app.post("/auth/signup")
async def signup(req: SignUpRequest):
    result = sign_up(req.email, req.password, req.username, req.language, req.risk_appetite)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/auth/signin")
async def signin(req: SignInRequest):
    result = sign_in(req.email, req.password)
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["error"])
    return result

@app.post("/auth/wallet")
async def wallet_login(req: WalletSignInRequest):
    result = wallet_sign_in(req.wallet_address, req.username, req.language, req.risk_appetite)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.get("/profile/{user_id}")
async def profile(user_id: str):
    data = get_profile(user_id)
    if not data:
        raise HTTPException(status_code=404, detail="Profile not found")
    return data


# ── Conversations ─────────────────────────────────────────────
@app.get("/conversations/{user_id}")
async def list_conversations(user_id: str):
    return get_conversations(user_id)

@app.post("/conversations")
async def new_conversation(req: NewConversationRequest):
    return create_conversation(req.user_id, req.title)

@app.get("/conversations/{conversation_id}/messages")
async def list_messages(conversation_id: str):
    return get_conversation_messages(conversation_id)

@app.delete("/conversations/{conversation_id}")
async def remove_conversation(conversation_id: str):
    delete_conversation(conversation_id)
    return {"success": True}


# ── Chat ──────────────────────────────────────────────────────
@app.post("/chat")
async def chat(req: ChatRequest):
    profile = get_profile(req.user_id) if req.user_id else {}

    # Load history from Redis for fast context
    history = get_history(req.user_id) if req.user_id else []
    history.append({"role": "user", "content": req.message})

    # Run MARC
    reply = run_agent(history, profile)
    history.append({"role": "assistant", "content": reply})

    # Save to Redis for fast memory
    if req.user_id:
        save_history(req.user_id, history)

    # Persist to Supabase conversation
    conv_id = req.conversation_id
    if req.user_id and conv_id:
        save_message(conv_id, "user", req.message)
        save_message(conv_id, "assistant", reply)

        # Auto-title: use first user message if title is still "New Chat"
        convs = get_conversations(req.user_id)
        current = next((c for c in convs if c["id"] == conv_id), None)
        if current and current.get("title") == "New Chat":
            title = req.message[:40] + ("..." if len(req.message) > 40 else "")
            update_conversation_title(conv_id, title)

    return {"reply": reply, "conversation_id": conv_id}

@app.delete("/chat/history/{user_id}")
async def clear(user_id: str):
    clear_history(user_id)
    return {"success": True}


# ── Blockchain ────────────────────────────────────────────────
from arc_tools import check_balance, send_usdc, estimate_gas_fee, get_transaction_info, get_network_status

class BalanceRequest(BaseModel):
    address: Optional[str] = None

class SendRequest(BaseModel):
    to_address: str
    amount: float

@app.post("/balance")
def balance(req: BalanceRequest):
    return check_balance(req.address)

@app.post("/send")
def send(req: SendRequest):
    return send_usdc(req.to_address, req.amount)

@app.get("/fees")
def fees():
    return estimate_gas_fee()

@app.get("/transaction/{tx_hash}")
def transaction(tx_hash: str):
    return get_transaction_info(tx_hash)

@app.get("/network")
def network():
    return get_network_status()