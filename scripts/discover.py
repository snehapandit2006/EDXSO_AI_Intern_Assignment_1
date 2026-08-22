"""CLI Script: Run Creator Discovery Stage."""
from app.discovery import run_discovery

if __name__ == "__main__":
    creators = run_discovery()
    print(f"\n[CLI Discovery] Successfully discovered {len(creators)} real creator records.")
