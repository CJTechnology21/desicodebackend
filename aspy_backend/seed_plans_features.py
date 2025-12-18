import sys
import os
from datetime import datetime

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import ALL models to ensure they're registered with SQLAlchemy
from app.models.subscription import Plan, PlanType
import app.models.user
import app.models.invoice
import app.models.payment
import app.models.code_execution
import app.models.language

# Now import session
from app.db.session import SessionLocal

def seed_plans():
    db = SessionLocal()

    # Clear existing plans to avoid conflicts with new types/schema
    # db.query(Plan).delete()
    # db.commit()
    # print("Cleared usage of old plans.")


    plans = [
        {
            "name": "Starter",
            "type": PlanType.STARTER,
            "price": 0,
            "currency": "USD",
            "features": {
                "team_members": "1 Team member",
                "projects": "5 Projects",
                "support": "Community support",
                "storage": "1GB Storage",
                "analytics": "Basic analytics"
            }
        },
        {
            "name": "Pro",
            "type": PlanType.PRO,
            "price": 2900,  # $29.00 -> stored as cents
            "currency": "USD",
            "features": {
                "team_members": "5 Team members",
                "projects": "Unlimited projects",
                "support": "Priority email support",
                "storage": "50GB Storage",
                "analytics": "Advanced analytics",
                "custom_domains": "Custom domains"
            }
        },
        {
            "name": "Enterprise",
            "type": PlanType.ENTERPRISE,
            "price": 9900, # $99.00 -> stored as cents
            "currency": "USD",
            "features": {
                "team_members": "Unlimited team members",
                "projects": "Unlimited projects",
                "support": "24/7 Phone support",
                "storage": "Unlimited storage",
                "analytics": "Custom reporting",
                "security": "SSO & Advanced security",
                 "sla": "SLA Guarantee"
            }
        }
    ]

    for plan_data in plans:
        existing = db.query(Plan).filter(Plan.type == plan_data["type"]).first()
        if existing:
            # Update existing plan features
            existing.features = plan_data["features"]
            existing.price = plan_data["price"]
            existing.currency = plan_data["currency"]
            existing.name = plan_data["name"] # Should match but updating just in case
            print(f"Updated plan {plan_data['name']}.")
        else:
            plan = Plan(**plan_data)
            db.add(plan)
            print(f"Added plan {plan_data['name']}.")

    db.commit()
    db.close()
    print("Plans seeded successfully!")

if __name__ == "__main__":
    seed_plans()