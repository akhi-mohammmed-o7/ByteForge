import hashlib
import random
import string
import uuid
from datetime import datetime

def generate_skill_hash(user_id: int, skill_id: int, score: float, timestamp: str = None) -> str:
    if timestamp is None:
        timestamp = datetime.utcnow().isoformat()
    salt = str(uuid.uuid4())[:8]
    raw = f"PRAMAAN::{user_id}::{skill_id}::{score:.4f}::{timestamp}::{salt}"
    return hashlib.sha256(raw.encode()).hexdigest()

def generate_anonymous_id() -> str:
    chars = string.ascii_uppercase + string.digits
    return "SH-" + ''.join(random.choices(chars, k=5))