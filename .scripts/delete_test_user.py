import os
import sys

from sqlalchemy import create_engine, text

# Use DATABASE_URL env if set, otherwise default to the backend config default.
database_url = os.environ.get(
    "DATABASE_URL", "postgresql://user:password@localhost:5432/musician_eval"
)
print("DB URL:", database_url)
engine = create_engine(database_url)

username = "musician-local"
with engine.connect() as conn:
    try:
        # user is a reserved word; quote it
        res = conn.execute(
            text('DELETE FROM "user" WHERE username = :username RETURNING id'),
            {"username": username},
        )
        deleted = res.rowcount
        conn.commit()
        if deleted:
            print(f"Deleted {deleted} row(s) for user {username}")
        else:
            print(f"User {username} not found, nothing to delete")
    except Exception as e:
        print("ERR deleting user:", repr(e))
        sys.exit(2)
