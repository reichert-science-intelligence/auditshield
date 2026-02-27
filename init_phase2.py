"""
Initialize Phase 2 database and demo data
Run this after deploying to set up the system
"""

from database import get_db_manager
from database_phase2_schema import add_phase2_schema
from radv_command_center import seed_demo_audit


def initialize_phase2():
    print("Initializing AuditShield-Live Phase 2...")

    # Get database connection
    db = get_db_manager()

    # Add Phase 2 schema
    print("\nAdding Phase 2 database schema...")
    add_phase2_schema(db)

    # Create demo audit
    print("\nCreating demo RADV audit...")
    audit_id = seed_demo_audit()

    print("\nPhase 2 initialization complete!")
    print(f"   Demo audit ID: {audit_id}")
    print("   Navigate to 'RADV Command Center' tab to view")
    print("\nReady to use all Phase 2 features:")
    print("   - RADV Command Center")
    print("   - Chart Selection AI")
    print("   - Education Tracker")


if __name__ == "__main__":
    initialize_phase2()
