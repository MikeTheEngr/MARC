import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY"),
)


def create_conversation(user_id: str, title: str) -> dict:
    try:
        res = supabase.table("conversations").insert({
            "user_id": user_id,
            "title": title,
        }).execute()
        return res.data[0] if res.data else {}
    except Exception as e:
        return {"error": str(e)}


def get_conversations(user_id: str) -> list:
    try:
        res = supabase.table("conversations").select("*").eq("user_id", user_id).order("updated_at", desc=True).limit(30).execute()
        return res.data or []
    except Exception:
        return []


def get_conversation_messages(conversation_id: str) -> list:
    try:
        res = supabase.table("conversation_messages").select("*").eq("conversation_id", conversation_id).order("created_at").execute()
        return res.data or []
    except Exception:
        return []


def save_message(conversation_id: str, role: str, content: str) -> dict:
    try:
        res = supabase.table("conversation_messages").insert({
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
        }).execute()
        # Update conversation updated_at
        supabase.table("conversations").update({"updated_at": "now()"}).eq("id", conversation_id).execute()
        return res.data[0] if res.data else {}
    except Exception as e:
        return {"error": str(e)}


def update_conversation_title(conversation_id: str, title: str):
    try:
        supabase.table("conversations").update({"title": title}).eq("id", conversation_id).execute()
    except Exception:
        pass


def delete_conversation(conversation_id: str):
    try:
        supabase.table("conversations").delete().eq("id", conversation_id).execute()
    except Exception:
        pass