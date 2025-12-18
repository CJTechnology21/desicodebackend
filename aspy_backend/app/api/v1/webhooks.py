from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
import hmac
import hashlib
import json
import os
from datetime import datetime

from app.db.session import get_db
from app.models.user import User
from app.models.subscription import Subscription, SubscriptionStatus, Plan
from app.models.invoice import Invoice

router = APIRouter()

razorpay_webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")


@router.post("/webhooks/razorpay", tags=["Webhooks"])
async def razorpay_webhook(
        request: Request,
        db: Session = Depends(get_db)
):
    """Handle Razorpay webhook events"""
    payload = await request.body()
    sig_header = request.headers.get('x-razorpay-signature')

    if not razorpay_webhook_secret:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    expected_signature = hmac.new(
        razorpay_webhook_secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, sig_header):
        raise HTTPException(status_code=400, detail="Invalid signature")

    data = json.loads(payload)
    event = data.get('event')

    if event == 'payment.captured':
        payment = data['payload']['payment']['entity']
        user_id = payment['notes'].get('user_id')
        plan_id = payment['notes'].get('plan_id')

        if user_id and plan_id:
            user = db.query(User).filter(User.id == user_id).first()
            plan = db.query(Plan).filter(Plan.id == plan_id).first()

            if user and plan:
                subscription = Subscription(
                    user_id=user.id,
                    plan_id=plan.id,
                    status=SubscriptionStatus.ACTIVE,
                    razorpay_payment_id=payment['id'],
                    current_period_start=datetime.utcnow(),
                    current_period_end=datetime.utcnow()
                )
                db.add(subscription)
                db.commit()

                invoice = Invoice(
                    user_id=user.id,
                    subscription_id=subscription.id,
                    amount=payment['amount'] / 100,
                    currency=payment['currency'],
                    status='paid',
                    razorpay_payment_id=payment['id'],
                    paid_at=datetime.fromtimestamp(payment['created_at'])
                )
                db.add(invoice)
                db.commit()

    return {"status": "success"}