from app.models.user import User
from app.models.subscription import Subscription, Plan
from app.models.code_execution import CodeExecution
from app.models.language import Language
from app.db.base import Base
from app.db.session import engine

print('Creating tables...')
Base.metadata.create_all(bind=engine)
print('Tables created.')
