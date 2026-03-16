"""
Entry point for HuggingFace Spaces deployment
Auto-initializes database on first run
"""
from pathlib import Path

# Use same path as database.py for SQLite
_db_dir = Path(__file__).resolve().parent
db_path = _db_dir / "auditshield.db"

if not db_path.exists():
    print("First-time setup detected...")

    # Initialize Phase 1
    from database import get_db_manager

    db = get_db_manager()
    db.initialize_schema()
    db.seed_demo_data()

    # Initialize Phase 2
    from database_phase2_schema import add_phase2_schema
    from radv_command_center import seed_demo_audit

    add_phase2_schema(db)
    seed_demo_audit()

    print("Database initialized with demo data")

# HuggingFace Spaces uses this entry point
if __name__ == "__main__":
    import uvicorn

    # Use module:app string so uvicorn loads app after our init
    uvicorn.run("app:app", host="0.0.0.0", port=7860)
