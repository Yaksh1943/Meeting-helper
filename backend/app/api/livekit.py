from fastapi import APIRouter, Query
import os
from app.services.livekit_tokens import generate_room_token

router = APIRouter()

@router.get("/connection-details")
def connection_details(
    roomName: str = Query(...), participantName: str = Query(...)
):
    token, room = generate_room_token(roomName, participantName)
    server_url = os.getenv("LIVEKIT_URL", "wss://meet.livekit.io")
    return {
        "serverUrl": server_url,
        "roomName": roomName,
        "participantName": participantName,
        "participantToken": token,
    }