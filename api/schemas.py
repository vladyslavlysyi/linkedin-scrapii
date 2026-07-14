from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class JobResponse(BaseModel):
    id: int
    title: str
    company: str
    location: Optional[str]
    date_posted: Optional[str]
    job_link: str
    description: Optional[str]
    scraped_at: datetime

    class Config:
        from_attributes = True

class PaginatedJobs(BaseModel):
    total: int
    jobs: list[JobResponse]
