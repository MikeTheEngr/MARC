from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from agent import run_agent
from memory import get_history, save_history, clear_history
from auth import sign_up, sign_in, wallet_sign_in, get_profile

app = FastAPI(title="MARC API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Auth ──────────────────────────────────────────────────────
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


# ── Routes ────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "MARC API live", "network": "Arc Testnet"}


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


@app.post("/chat")
async def chat(req: ChatRequest):
    profile = get_profile(req.user_id) if req.user_id else {}
    history = get_history(req.user_id) if req.user_id else []
    history.append({"role": "user", "content": req.message})
    reply = run_agent(history, profile)
    history.append({"role": "assistant", "content": reply})
    if req.user_id:
        save_history(req.user_id, history)
    return {"reply": reply}


@app.delete("/chat/history/{user_id}")
async def clear(user_id: str):
    clear_history(user_id)
    return {"success": True}


# ── Blockchain endpoints ──────────────────────────────────────
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