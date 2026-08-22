"""Initialize database tables and active campaign record."""
import sys
from pathlib import Path

# Add root directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.models import init_db, reset_db, SessionLocal
from app.database.repository import get_or_create_campaign
from app.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, EXPORTS_DATA_DIR


def purge_dataset_files():
    """Delete all generated JSON and CSV data files across raw, processed, and export directories."""
    for directory in [RAW_DATA_DIR, PROCESSED_DATA_DIR, EXPORTS_DATA_DIR]:
        if directory.exists():
            for file in directory.glob("*.*"):
                if file.is_file() and file.name != ".gitkeep":
                    try:
                        file.unlink()
                    except Exception as e:
                        print(f"Warning: Failed to delete {file}: {e}")


def run_init_db(reset: bool = False):
    if reset:
        print("Purging database tables and stale data files...")
        reset_db()
        purge_dataset_files()
        print("Stale dataset files purged successfully.")
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
