from app.db.session import engine
from sqlalchemy import text

print("Migrating schema...")
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE code_executions ADD COLUMN IF NOT EXISTS language_id INTEGER;"))
        conn.execute(text("ALTER TABLE code_executions DROP CONSTRAINT IF EXISTS fk_code_executions_languages;"))
        conn.execute(text("ALTER TABLE code_executions ADD CONSTRAINT fk_code_executions_languages FOREIGN KEY (language_id) REFERENCES languages(id);"))
        conn.commit()
        print("Schema updated successfully.")
    except Exception as e:
        print(f"Error: {e}")
