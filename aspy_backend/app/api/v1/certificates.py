from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.v1.auth import get_current_active_user
from app.models.user import User
from app.models.subscription import Subscription, SubscriptionStatus, PlanType
from app.models.code_execution import CodeExecution
from app.models.language import Language
from datetime import datetime

router = APIRouter()

@router.get("/certificates", tags=["Certificates"])
def get_user_certificates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of earned certificates based on language usage.
    Only for PRO or ENTERPRISE users.
    """
    # 1. Check Subscription eligibility
    active_sub = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == SubscriptionStatus.ACTIVE,
    ).first()

    has_access = False
    if active_sub and active_sub.plan:
        # Assuming PRO and ENTERPRISE are logic based on name or Type
        # Or simply if it's not STARTER (Free).
        # Let's check plan name/type.
        if active_sub.plan.type in [PlanType.PRO, PlanType.ENTERPRISE]:
             has_access = True
    
    if not has_access:
        return {
            "eligible": False,
            "message": "Upgrade to Pro or Enterprise to unlock certificates.",
            "certificates": []
        }

    # 2. Get Used Languages
    # We want languages where user has at least one execution
    # Distinct language_ids from executions
    
    used_lang_ids = db.query(CodeExecution.language_id)\
        .filter(CodeExecution.user_id == current_user.id)\
        .filter(CodeExecution.language_id != None)\
        .distinct().all()
    
    # Flatten list of tuples
    used_ids = [r[0] for r in used_lang_ids]
    
    certificates = []
    
    if used_ids:
        langs = db.query(Language).filter(Language.id.in_(used_ids)).all()
        for lang in langs:
            # Maybe get date of first usage?
            first_use = db.query(CodeExecution.created_at)\
                .filter(CodeExecution.user_id == current_user.id, CodeExecution.language_id == lang.id)\
                .order_by(CodeExecution.created_at.asc()).first()
            
            certificates.append({
                "id": f"cert_{current_user.id}_{lang.slug}",
                "language": lang.name,
                "slug": lang.slug,
                "issued_at": first_use[0] if first_use else datetime.utcnow(),
                "download_url": "#" # Frontend will handle generation or we provide a separate endpoint
            })

    return {
        "eligible": True,
        "certificates": certificates
    }
