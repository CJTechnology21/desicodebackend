from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import razorpay
import os
from datetime import datetime, timedelta
import json

from app.db.session import get_db
from app.models.subscription import Plan, Subscription, SubscriptionStatus
from app.models.invoice import Invoice
from app.models.payment import Payment, PaymentStatus
from app.schemas.payment import (
    RazorpayOrderRequest,
    RazorpayOrderResponse,
    RazorpayVerifyRequest,
    PaymentHistory
)
from app.core.security import get_current_user

router = APIRouter()

# Initialize payment gateways
# Use dummy keys if environment variables are not set or set to "dummy"
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "dummy")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "dummy")

try:
    razorpay_client = razorpay.Client(
        auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
    )
except:
    razorpay_client = None

def format_plan_features(plan: Plan) -> str:
    """Format plan features for display"""
    try:
        if isinstance(plan.features, str):
            features_dict = json.loads(plan.features)
        else:
            features_dict = plan.features or {}

        features_list = []
        for key, value in features_dict.items():
            key_formatted = key.replace('_', ' ').title()
            if isinstance(value, bool):
                features_list.append(f"{key_formatted}: {'Yes' if value else 'No'}")
            elif isinstance(value, (int, float)):
                features_list.append(f"{key_formatted}: {value}")
            else:
                features_list.append(f"{key_formatted}: {value}")

        return " | ".join(features_list)
    except:
        return "View features for details"


# Stripe support removed as per request


@router.post("/payments/razorpay/create-order", response_model=RazorpayOrderResponse, tags=["Payments"])
def create_razorpay_order(
        request: RazorpayOrderRequest,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user)
):
    """
    Create Razorpay order for payment

    Note: Your plan prices are stored in paise (INR cents).
    Razorpay expects amounts in paise for INR.
    """
    # Get the plan
    plan = db.query(Plan).filter(Plan.id == request.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Check currency compatibility
    requested_currency = request.currency.upper()
    plan_currency = plan.currency.upper()

    if requested_currency != plan_currency:
        raise HTTPException(
            status_code=400,
            detail=f"Plan currency ({plan_currency}) does not match requested currency ({requested_currency})"
        )

    # Check if user already has an active subscription
    # existing = db.query(Subscription).filter(
    #     Subscription.user_id == current_user.id,
    #     Subscription.status == SubscriptionStatus.ACTIVE
    # ).first()

    # if existing:
    #     raise HTTPException(status_code=400, detail="User already has an active subscription")

    try:
        # Your prices are already in paise for INR, which is perfect for Razorpay
        # For other currencies, ensure they're in smallest unit
        if requested_currency == "INR":
            amount = plan.price  # Already in paise
        else:
            # For other currencies, assume price is in main unit and convert to smallest
            amount = int(plan.price * 100)

        # Mock Mode Check
        if not RAZORPAY_KEY_ID or RAZORPAY_KEY_ID == "dummy" or not razorpay_client:
            # Create a mock order ID
            mock_order_id = f"order_mock_{current_user.id}_{int(datetime.now().timestamp())}"
            
             # Create pending invoice record
            invoice = Invoice(
                user_id=current_user.id,
                amount=amount / 100 if requested_currency == "INR" else amount / 100,  # Convert to main currency unit
                currency=requested_currency,
                status='pending',
                razorpay_order_id=mock_order_id,
                plan_id=plan.id,
                created_at=datetime.utcnow()
            )
            db.add(invoice)
            db.commit()

            return RazorpayOrderResponse(
                order_id=mock_order_id,
                amount=amount,
                currency=requested_currency,
                key_id="dummy_key_id"
            )

        # Create order data
        order_data = {
            'amount': amount,
            'currency': requested_currency,
            'receipt': f'order_{current_user.id}_{int(datetime.now().timestamp())}',
            'notes': {
                'user_id': str(current_user.id),
                'username': current_user.username,
                'plan_id': str(plan.id),
                'plan_name': plan.name,
                'email': current_user.email
            },
            'payment_capture': 1  # Auto-capture payment
        }

        # Create Razorpay order
        order = razorpay_client.order.create(data=order_data)

        # Create pending invoice record
        invoice = Invoice(
            user_id=current_user.id,
            amount=amount / 100 if requested_currency == "INR" else amount / 100,  # Convert to main currency unit
            currency=requested_currency,
            status='pending',
            razorpay_order_id=order['id'],
            plan_id=plan.id,
            created_at=datetime.utcnow()
        )

        db.add(invoice)
        db.commit()

        return RazorpayOrderResponse(
            order_id=order['id'],
            amount=order['amount'],
            currency=order['currency'],
            key_id=RAZORPAY_KEY_ID
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/payments/razorpay/verify", tags=["Payments"])
def verify_razorpay_payment(
        request: RazorpayVerifyRequest,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user)
):
    """
    Verify Razorpay payment signature and process payment
    """
    try:
         # Find the pending invoice
        invoice = db.query(Invoice).filter(
            Invoice.razorpay_order_id == request.razorpay_order_id,
            Invoice.user_id == current_user.id,
            Invoice.status == 'pending'
        ).first()

        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found or already processed")

        amount_inr_paise = int(invoice.amount * 100) # Reconstruct approximate amount for logic if needed

        # Verify payment signature
        # Check for Mock Mode
        if (not RAZORPAY_KEY_ID or RAZORPAY_KEY_ID == "dummy" or 
            not razorpay_client or 
            request.razorpay_order_id.startswith("order_mock_") or
            request.razorpay_signature.startswith("sig_mock_")):
            
            # Mock verification passed
            order = {
                'amount': amount_inr_paise,
                'currency': invoice.currency
            }
            # Simulate payment details from request
        else:
            params_dict = {
                'razorpay_order_id': request.razorpay_order_id,
                'razorpay_payment_id': request.razorpay_payment_id,
                'razorpay_signature': request.razorpay_signature
            }

            razorpay_client.utility.verify_payment_signature(params_dict)

            # Fetch payment details from Razorpay
            # payment = razorpay_client.payment.fetch(request.razorpay_payment_id)
            order = razorpay_client.order.fetch(request.razorpay_order_id)


        # Create Payment Record
        # If mock, use invoice amount directly
        # If real, use order['amount']
        payment_amount = float(order['amount']) / 100
        
        new_payment = Payment(
            user_id=current_user.id,
            amount=payment_amount,
            currency=order['currency'],
            status=PaymentStatus.COMPLETED,
            provider="razorpay",
            provider_payment_id=request.razorpay_payment_id,
            provider_order_id=request.razorpay_order_id,
            payment_method_details={"method": "razorpay", "id": request.razorpay_payment_id},
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        db.add(new_payment)
        db.flush()

        # Update invoice
        invoice.status = 'paid'
        invoice.payment_id = new_payment.id
        invoice.paid_at = datetime.utcnow()
        invoice.amount = payment_amount

        # Get plan from invoice
        plan = db.query(Plan).filter(Plan.id == invoice.plan_id).first()

        if plan:
            # Create or update subscription
            subscription = db.query(Subscription).filter(
                Subscription.user_id == current_user.id
            ).first()

            if not subscription:
                # Create new subscription
                period_start = datetime.utcnow()
                period_end = period_start + timedelta(days=30)  # Monthly subscription

                subscription = Subscription(
                    user_id=current_user.id,
                    plan_id=plan.id,
                    status=SubscriptionStatus.ACTIVE,
                    current_period_start=period_start,
                    current_period_end=period_end,
                    created_at=datetime.utcnow()
                )
                db.add(subscription)
                db.flush()
            else:
                # Upgrade/Downgrade/Renew existing subscription
                subscription.plan_id = plan.id  # Update plan
                subscription.status = SubscriptionStatus.ACTIVE
                subscription.current_period_start = datetime.utcnow()
                subscription.current_period_end = datetime.utcnow() + timedelta(days=30)

            # Link payment and invoice to subscription
            new_payment.subscription_id = subscription.id
            invoice.subscription_id = subscription.id
            
        db.commit()

        return {
            "status": "success",
            "message": "Payment verified and processed successfully",
            "payment_id": request.razorpay_payment_id,
            "order_id": request.razorpay_order_id,
            "amount": invoice.amount,
            "currency": invoice.currency
        }

    except razorpay.errors.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid payment signature")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/payments/history", response_model=List[PaymentHistory], tags=["Payments"])
def get_payment_history(
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user)
):
    """
    Get payment history for current user
    """
    payments = db.query(Payment).filter(
        Payment.user_id == current_user.id
    ).order_by(Payment.created_at.desc()).all()

    history = []
    for payment in payments:
        # Get plan name if available
        plan_name = None
        if payment.subscription and payment.subscription.plan:
             plan_name = payment.subscription.plan.name
        
        # Get method description
        method = "Unknown"
        if payment.payment_method_details and isinstance(payment.payment_method_details, dict):
            method = payment.payment_method_details.get("method", "Unknown")
            # Enhance if we have more details

        history.append(PaymentHistory(
            id=payment.id,
            amount=float(payment.amount),
            currency=payment.currency,
            status=payment.status.value if hasattr(payment.status, 'value') else str(payment.status),
            provider=payment.provider,
            plan_name=plan_name,
            payment_method=method,
            created_at=payment.created_at
        ))

    return history


@router.get("/payments/methods", tags=["Payments"])
def get_payment_methods():
    """
    Get available payment methods
    """
    return {
        "available_methods": [
            {
                "provider": "razorpay",
                "currencies": ["INR"],
                "supported_cards": ["visa", "mastercard", "rupay", "amex"],
                "netbanking": True,
                "upi": True,
                "wallet": True
            }
        ]
    }