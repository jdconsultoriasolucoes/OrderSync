import os
from dotenv import load_dotenv

load_dotenv()

db_url = os.environ.get("DATABASE_URL", "NOT_FOUND")
env = os.environ.get("ENVIRONMENT", "NOT_FOUND")

if db_url != "NOT_FOUND":
    # Mask the password
    parts = db_url.split("@")
    if len(parts) > 1:
        prefix = parts[0].split("://")
        if len(prefix) > 1:
            protocol = prefix[0]
            user_pass = prefix[1].split(":")
            user = user_pass[0]
            masked_url = f"{protocol}://{user}:****@{parts[1]}"
        else:
            masked_url = db_url
    else:
        masked_url = db_url
else:
    masked_url = "NOT_FOUND"

print(f"ENVIRONMENT: {env}")
print(f"DATABASE_URL: {masked_url}")
