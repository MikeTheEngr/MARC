import json
import os
from upstash_redis import Redis
from dotenv import load_dotenv

load_dotenv()

redis = Redis(
    url=os.getenv("UPSTASH_REDIS_REST_URL"),
    token=os.getenv("UPSTASH_REDIS_REST_TOKEN"),
)

MAX_MESSAGES = 20  # keep last 20 messages per user


def get_history(user_id: str) -> list:
    """Load conversation history for a user from Redis."""
    try:
        raw = redis.get(f"marc:history:{user_id}")
        if raw:
            return json.loads(raw)
        return []
    except Exception:
        return []


def save_history(user_id: str, messages: list):
    """Save conversation history to Redis, capped at MAX_MESSAGES."""
    try:
        trimmed = messages[-MAX_MESSAGES:]
        redis.set(f"marc:history:{user_id}", json.dumps(trimmed), ex=60 * 60 * 24 * 7)  # 7 days TTL
    except Exception:
        pass


def clear_history(user_id: str):
    """Clear a user's conversation history."""
    try:
        redis.delete(f"marc:history:{user_id}")
    except Exception:
        pass