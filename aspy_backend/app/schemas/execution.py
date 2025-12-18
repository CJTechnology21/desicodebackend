from pydantic import BaseModel

class CodeRunRequest(BaseModel):
    language: str
    code: str

class CodeRunResponse(BaseModel):
    output: str
