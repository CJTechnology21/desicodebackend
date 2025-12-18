from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr
from app.core.email import send_contact_email
import os

router = APIRouter()

class ContactRequest(BaseModel):
    name: str
    email: EmailStr
    query_type: str
    message: str

@router.post("/contact", tags=["Contact"])
async def send_contact_form(request: ContactRequest, background_tasks: BackgroundTasks):
    """
    Send a contact email to the admin/support team.
    """
    admin_email = os.getenv("ADMIN_EMAIL", "support@desicodes.com") # Replace with the real receiving email
    
    # We send the email to the admin, containing the user's message
    body = request.dict()
    
    try:
        # Send to admin
        background_tasks.add_task(
            send_contact_email, 
            subject=f"New Contact Request: {request.query_type}", 
            email_to=[admin_email], 
            body=body
        )
        return {"message": "Message sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
