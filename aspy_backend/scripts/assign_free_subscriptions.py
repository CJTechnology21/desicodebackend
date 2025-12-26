"""
Script to assign free subscriptions to users who don't have any subscription
"""
import sqlite3
from datetime import datetime, timedelta
import os

db_path = os.path.join(os.path.dirname(__file__), '..', 'dev.db')

def assign_free_subscriptions():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Find the FREE plan ID
        cursor.execute("SELECT id FROM plans WHERE type = 'FREE' LIMIT 1")
        result = cursor.fetchone()
        
        if not result:
            print("❌ Error: No FREE plan found. Please run seed_plans.py first.")
            return
        
        free_plan_id = result[0]
        print(f"Found FREE plan with ID: {free_plan_id}")
        
        # Find all users without an active subscription
        cursor.execute("""
            SELECT u.id, u.username, u.email
            FROM users u
            WHERE NOT EXISTS (
                SELECT 1 FROM subscriptions s 
                WHERE s.user_id = u.id AND s.status = 'ACTIVE'
            )
        """)
        
        users = cursor.fetchall()
        print(f"Found {len(users)} users without active subscriptions")
        
        period_start = datetime.utcnow()
        # For free plan, set end date far in the future (100 years)
        period_end = period_start + timedelta(days=36500)
        
        for user_id, username, email in users:
            print(f"  ✓ Creating FREE subscription for user {user_id} ({username}, {email})")
            
            cursor.execute("""
                INSERT INTO subscriptions 
                (user_id, plan_id, status, current_period_start, current_period_end, cancel_at_period_end, created_at)
                VALUES (?, ?, 'ACTIVE', ?, ?, 0, ?)
            """, (user_id, free_plan_id, period_start.isoformat(), period_end.isoformat(), period_start.isoformat()))
        
        conn.commit()
        print(f"\n✅ Successfully created {len(users)} free subscriptions")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    assign_free_subscriptions()
