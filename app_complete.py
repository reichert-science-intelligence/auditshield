# app_complete.py
"""
AuditShield-Live - Complete Application
Medicare Advantage RADV Audit Defense Platform

Auto-initializes on first run for HuggingFace Spaces deployment
"""

import os
import sys
from pathlib import Path


def check_and_initialize():
    """Check if database exists and initialize if needed"""
    import os
    db_path = Path(os.environ.get("SQLITE_PATH", "auditshield.db"))
    if not db_path.is_absolute():
        db_path = Path(__file__).resolve().parent / str(db_path)

    if not db_path.exists():
        print("=" * 80)
        print("🚀 First-time setup detected - initializing AuditShield-Live...")
        print("=" * 80)
        print("\nThis will take 1-2 minutes. Please wait...")

        try:
            # Run complete initialization
            from init_complete_system import initialize_complete_system

            initialize_complete_system()

            print("\n" + "=" * 80)
            print("✅ System initialized successfully!")
            print("=" * 80)

        except Exception as e:
            print(f"\n❌ Initialization failed: {e}")
            import traceback

            traceback.print_exc()
            sys.exit(1)
    else:
        print("✅ Database found - skipping initialization")


# Run initialization check
check_and_initialize()

# Import main app AFTER initialization
try:
    from app import app
except Exception as e:
    import traceback
    print("FATAL: Failed to import app")
    traceback.print_exc()
    sys.exit(1)

# Run the app
if __name__ == "__main__":
    import uvicorn

    # Get port from environment variable (HuggingFace Spaces sets this)
    port = int(os.environ.get("PORT", 7860))
    host = "0.0.0.0"

    print(f"\n🚀 Starting AuditShield-Live on {host}:{port}")
    print(
        f"   Environment: {'HuggingFace Spaces' if os.environ.get('SPACE_ID') else 'Local'}"
    )

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
    )
