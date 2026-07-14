from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    location = Column(String(255))
    date_posted = Column(String(100))
    job_link = Column(String(2048), unique=True, nullable=False)
    description = Column(Text)
    scraped_at = Column(DateTime, default=datetime.utcnow)

class Person(Base):
    __tablename__ = "people"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    headline = Column(Text)
    location = Column(String(255))
    profile_link = Column(String(2048), unique=True, nullable=False)
    snippet = Column(Text)
    scraped_at = Column(DateTime, default=datetime.utcnow)
