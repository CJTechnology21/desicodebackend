"""
Script to fix existing subscriptions that are missing current_period_end using SQL
"""
import sqlite3
from datetime import datetime, timedelta
import os

db_path = os.path.join(os.path.dirname(__file__), '..', 'dev.db')

def fix_subscriptions():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Find all subscriptions without current_period_end
        cursor.execute("""
            SELECT s.id, s.user_id, s.plan_id, s.current_period_start, p.type
            FROM subscriptions s
            JOIN plans p ON s.plan_id = p.id
            WHERE s.status = 'ACTIVE' AND s.current_period_end IS NULL
        """)
        
        subscriptions = cursor.fetchall()
        print(f"Found {len(subscriptions)} subscriptions without current_period_end")
        
        for sub_id, user_id, plan_id, period_start_str, plan_type in subscriptions:
            # Parse the period_start datetime
            period_start = datetime.fromisoformat(period_start_str.replace('Z', '+00:00'))
            
            # Set period_end based on plan type
            if plan_type == 'FREE':
                # For free plan, set end date far in the future (100 years)
                period_end = period_start + timedelta(days=36500)
                print(f"  ✓ Subscription {sub_id} (User {user_id}): Setting FREE plan end date to {period_end}")
            else:
                # For paid plans, set to 30 days from start
                period_end = period_start + timedelta(days=30)
                print(f"  ✓ Subscription {sub_id} (User {user_id}): Setting {plan_type} plan end date to {period_end}")
            
            # Update the subscription
            cursor.execute(
                "UPDATE subscriptions SET current_period_end = ? WHERE id = ?",
                (period_end.isoformat(), sub_id)
            )
        
        conn.commit()
        print(f"\n✅ Successfully updated {len(subscriptions)} subscriptions")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    fix_subscriptions()
