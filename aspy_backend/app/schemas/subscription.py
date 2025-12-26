from pydantic import BaseModel, model_serializer
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.subscription import PlanType, SubscriptionStatus

class PlanBase(BaseModel):
    name: str
    type: PlanType
    price: int
    currency: str = "USD"
    features: Dict[str, Any]

class Plan(PlanBase):
    id: int

    class Config:
        from_attributes = True

class SubscriptionBase(BaseModel):
    plan_id: int

class SubscriptionCreate(SubscriptionBase):
    pass

class Subscription(SubscriptionBase):
    id: int
    user_id: int
    status: SubscriptionStatus
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: Optional[bool] = False
    created_at: datetime
    cancelled_at: Optional[datetime] = None

    class Config:
        from_attributes = True
    
    @model_serializer
    def ser_model(self):
        """Custom serializer to convert status enum to lowercase"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'plan_id': self.plan_id,
            'status': self.status.value.lower() if isinstance(self.status, SubscriptionStatus) else str(self.status).lower(),
            'current_period_start': self.current_period_start,
            'current_period_end': self.current_period_end,
            'cancel_at_period_end': self.cancel_at_period_end,
            'created_at': self.created_at,
            'cancelled_at': self.cancelled_at,
        }