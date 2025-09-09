import asyncio
import logging
import os
import requests
import json
from typing import Dict, Set
from sqlmodel import Session, select
from dotenv import load_dotenv

from livekit import api, rtc

from app.models.db import engine
from app.models.schema import Meeting

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MeetingAgent:
    def __init__(self):
        self.active_agents: Dict[int, rtc.Room] = {}
        self.monitoring = True
        self.livekit_api = None

    async def monitor_meetings(self):
        """Monitor database for active meetings and join/leave as needed"""
        logger.info("Starting meeting monitoring...")
        
        self.livekit_api = api.LiveKitAPI(
            os.getenv('LIVEKIT_URL'),
            os.getenv('LIVEKIT_API_KEY'),
            os.getenv('LIVEKIT_API_SECRET'),
        )
        
        while self.monitoring:
            try:
                with Session(engine) as db:
                    
                    active_meetings = db.exec(
                        select(Meeting).where(
                            Meeting.start_ts != None, 
                            Meeting.end_ts == None
                        )
                    ).all()
                    
                    current_meeting_ids = {m.id for m in active_meetings}
                    agent_meeting_ids = set(self.active_agents.keys())
                    
                    # Join new meetings
                    for meeting in active_meetings:
                        if meeting.id not in agent_meeting_ids:
                            logger.info(f"New active meeting found: {meeting.id}")
                            await self.join_meeting(meeting.id)
                    
                    # Leave ended meetings
                    for meeting_id in agent_meeting_ids - current_meeting_ids:
                        logger.info(f"Meeting ended: {meeting_id}")
                        await self.leave_meeting(meeting_id)
                        
            except Exception as e:
                logger.error(f"Error monitoring meetings: {e}")
            
            await asyncio.sleep(10)  # Check every 10 seconds

    async def join_meeting(self, meeting_id: int):
        """Join a LiveKit meeting as AI agent"""
        try:
            # Create agent token
            token = api.AccessToken(
                os.getenv('LIVEKIT_API_KEY'),
                os.getenv('LIVEKIT_API_SECRET')
            )
            token.with_identity("AI-Assistant")
            token.with_name("Meeting AI Assistant")
            token.with_grants(api.VideoGrants(
                room_join=True,
                room=str(meeting_id),
                can_subscribe=True,
                can_publish=False  # Agent only listens
            ))
            
            
            room = rtc.Room()
            
            # Set up event handlers
            await self.setup_room_handlers(room, meeting_id)
            
            # Connect to room
            await room.connect(
                os.getenv('LIVEKIT_URL'),
                token.to_jwt()
            )
            
            self.active_agents[meeting_id] = room
            logger.info(f"AI agent joined meeting {meeting_id}")
            
        except Exception as e:
            logger.error(f"Error joining meeting {meeting_id}: {e}")

    async def setup_room_handlers(self, room: rtc.Room, meeting_id: int):
        
        @room.on("participant_connected")
        def on_participant_connected(participant: rtc.RemoteParticipant):
            logger.info(f"Participant joined meeting {meeting_id}: {participant.identity}")
        
        @room.on("participant_disconnected")
        def on_participant_disconnected(participant: rtc.RemoteParticipant):
            logger.info(f"Participant left meeting {meeting_id}: {participant.identity}")
        
        @room.on("track_subscribed")
        def on_track_subscribed(track: rtc.Track, publication: rtc.TrackPublication, participant: rtc.RemoteParticipant):
            if track.kind == rtc.TrackKind.KIND_AUDIO:
                logger.info(f"Audio track subscribed from {participant.identity} in meeting {meeting_id}")
            elif track.kind == rtc.TrackKind.KIND_VIDEO:
                logger.info(f"Video track subscribed from {participant.identity} in meeting {meeting_id}")

    async def leave_meeting(self, meeting_id: int):
        try:
            if meeting_id in self.active_agents:
                room = self.active_agents[meeting_id]
                await room.disconnect()
                del self.active_agents[meeting_id]
                logger.info(f"AI agent left meeting {meeting_id}")
        except Exception as e:
            logger.error(f"Error leaving meeting {meeting_id}: {e}")

    async def start(self):
        logger.info("Starting Meeting AI Agent...")
        logger.info("Agent will join meetings automatically but transcription is handled by browser")
        await self.monitor_meetings()

    def stop(self):
        self.monitoring = False
        logger.info("Meeting AI Agent stopped")

if __name__ == "__main__":
    agent = MeetingAgent()
    try:
        asyncio.run(agent.start())
    except KeyboardInterrupt:
        agent.stop()
        print("Agent stopped")