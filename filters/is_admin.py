import os

admins = [int(x) for x in os.getenv("ADMINS", "").split(",") if x]

def is_admin(user_id: int) -> bool:
    return user_id in admins
