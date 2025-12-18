from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class CodeExecution(Base):
    __tablename__ = "code_executions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    language = Column(String)
    language_id = Column(Integer, ForeignKey("languages.id"), nullable=True)
    code = Column(Text)
    output = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="executions")
    language_rel = relationship("Language", back_populates="code_executions")
