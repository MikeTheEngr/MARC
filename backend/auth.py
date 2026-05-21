import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Anon client — for auth operations
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_ANON_KEY"),
)

# Service role client — bypasses RLS for profile inserts
admin: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY", os.getenv("SUPABASE_ANON_KEY")),
)


def sign_up(email: str, password: str, username: str, language: str, risk_appetite: str) -> dict:
    """Register a new user with email/password."""
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.user:
            admin.table("profiles").insert({
                "id": res.user.id,
                "username": username,
                "language": language,
                "risk_appetite": risk_appetite,
            }).execute()
            return {
                "success": True,
                "user_id": res.user.id,
                "access_token": res.session.access_token if res.session else None,
                "profile": {
                    "username": username,
                    "language": language,
                    "risk_appetite": risk_appetite,
                }
            }
        return {"success": False, "error": "Signup failed — no user returned"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def sign_in(email: str, password: str) -> dict:
    """Sign in with email/password."""
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if res.user:
            profile = admin.table("profiles").select("*").eq("id", res.user.id).single().execute()
            return {
                "success": True,
                "user_id": res.user.id,
                "access_token": res.session.access_token,
                "profile": profile.data,
            }
        return {"success": False, "error": "Invalid credentials"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def wallet_sign_in(wallet_address: str, username: str = None, language: str = "English", risk_appetite: str = "beginner") -> dict:
    """Sign in or register via MetaMask wallet address."""
    try:
        fake_email = f"{wallet_address.lower()}@wallet.marc"
        fake_password = f"wallet_{wallet_address.lower()}_marc_secret"

        # Try sign in first
        try:
            res = supabase.auth.sign_in_with_password({"email": fake_email, "password": fake_password})
            if res.user:
                profile = admin.table("profiles").select("*").eq("id", res.user.id).single().execute()
                return {
                    "success": True,
                    "user_id": res.user.id,
                    "access_token": res.session.access_token,
                    "profile": profile.data,
                    "is_new": False,
                }
        except Exception:
            pass

        # New wallet user — register
        res = supabase.auth.sign_up({"email": fake_email, "password": fake_password})
        if res.user:
            profile_data = {
                "id": res.user.id,
                "username": username or f"0x...{wallet_address[-4:]}",
                "wallet_address": wallet_address,
                "language": language,
                "risk_appetite": risk_appetite,
            }
            admin.table("profiles").insert(profile_data).execute()
            return {
                "success": True,
                "user_id": res.user.id,
                "access_token": res.session.access_token if res.session else None,
                "profile": profile_data,
                "is_new": True,
            }
        return {"success": False, "error": "Wallet sign-in failed"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_profile(user_id: str) -> dict:
    """Fetch user profile from Supabase."""
    try:
        res = admin.table("profiles").select("*").eq("id", user_id).single().execute()
        return res.data or {}
    except Exception:
        return {}


def update_profile(user_id: str, updates: dict) -> dict:
    """Update user profile fields."""
    try:
        res = admin.table("profiles").update(updates).eq("id", user_id).execute()
        return {"success": True, "data": res.data}
    except Exception as e:
        return {"success": False, "error": str(e)}