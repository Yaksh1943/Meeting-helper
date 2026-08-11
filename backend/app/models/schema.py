from sqlmodel import SQLModel , Field
from typing import Optional

class Meeting(SQLModel,table= True):
    id: Optional[int] = Field(default=None, primary_key= True)
    title: str
    host_email:str
    start_ts: Optional[int] = None
    end_ts: Optional[int] = None

class Participant(SQLModel,table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    meeting_id: int
    name: str
    email: str
    joined_at: Optional[int] = None
    reminder_sent: bool = False

class TranscriptSegment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    meeting_id: int
    ts_start: Optional[int] = None
    ts_end: Optional[int] = None
    speaker: Optional[str] = None
    text: str 

class Summary(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    meeting_id: int
    start_min: int
    end_min: int
    type: str
    text: str

class ActionItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    meeting_id: int
    text: str    

class Decision(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    meeting_id: int
    text: str

class CreateMeetingRequest(SQLModel):
    title: str
    host_email: str

class InviteParticipantsRequest(SQLModel):
    emails: list[str]    

class SummaryType:
    FINAL = "final"
    SUMMARY = "summary"
    TIMELINE = "timeline"