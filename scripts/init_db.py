"""Initialize database tables and active campaign record."""
import sys
from app.database.models import init_db, reset_db, SessionLocal
from app.database.repository import get_or_create_campaign

def run_init_db(reset: bool = False):
    if reset:
        print("Purging stale synthetic database records (resetting tables)...")
        reset_db()
    else:
        print("Initializing SQLite database tables...")
        init_db()
    
    db = SessionLocal()
    campaign = get_or_create_campaign(db)
    print(f"Database initialized successfully! Active Campaign ID: {campaign.id} ('{campaign.title}')")
    db.close()

if __name__ == "__main__":
    do_reset = "--reset" in sys.argv or "-r" in sys.argv
    run_init_db(reset=do_reset)
