from pydantic import BaseModel, Field 
import datetime 
import uuid


class CandidateCreate(BaseModel):
    name : str 
    profile_text : str 
    skills : list[str] | None = None 
    years_experience : float = Field(ge = 0)
    certifications : list[str] | None = None 
    last_active : datetime.datetime | None = None 
    profile_complete : float = Field(ge = 0.0, le = 1.0)
    raw_data: dict | None = None 


class CandidateRead(BaseModel):
    id : uuid.UUID 
    name : str 
    profile_text : str 
    skills: list[str] | None 
    years_experience : float 
    certifications : list[str] | None 
    last_active : datetime.datetime | None 
    profile_complete : float 
    raw_data : dict | None 
    created_at : datetime.datetime 

    model_config = {"from_attributes": True}