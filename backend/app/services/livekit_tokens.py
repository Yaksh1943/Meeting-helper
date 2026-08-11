import jwt
import os
import time


def generate_room_token(room_name: str, identity: str):
    """Generate LiveKit room token for participant"""
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    if not api_key or not api_secret:
        raise ValueError("LIVEKIT_API_KEY and LIVEKIT_API_SECRET must be set in environment")

    now = int(time.time())
    payload = {
        "iss": api_key,
        "sub": identity,
        "nbf": now,
        "exp": now + 3600,
        "room": room_name,
        "video": {
            "room": room_name,
            "roomJoin": True,
            "roomList": True,
            "roomRecord": False,
            "roomAdmin": False,
            "roomCreate": True,
            "canPublish": True,
            "canSubscribe": True,
            "canPublishData": True,
            "canUpdateOwnMetadata": True,
        }
    }

    token = jwt.encode(payload, api_secret, algorithm="HS256")
    return token, room_name