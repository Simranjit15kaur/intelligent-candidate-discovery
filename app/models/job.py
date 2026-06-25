
from pydantic import BaseModel, Field
import uuid 
import datetime 

class JobCreate(BaseModel):
    title : str 
    description : str 
    required_skills : list[str]
    min_experience : float = Field(ge = 0)
    required_certs : list[str] | None = None 


class JobRead(BaseModel):
    id : uuid.UUID
    title : str 
    description : str | None 
    required_skills : list[str]
    min_experience : float
    required_certs: list[str] | None 
    created_at : datetime.datetime 

    model_config = {"from_attributes" : True}

