import sys
import os
sys.path.append(os.getcwd())
# Ensure DATABASE_URL is set in environment or .env
from services.db_migrations import run_migrations
run_migrations()
print("Migration script executed.")
run_migrations()
print("Migration script executed.")
