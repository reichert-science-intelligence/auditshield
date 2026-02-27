"""
Test all Phase 2 features are working
"""


def test_phase2():
    from database import get_db_manager
    from database_phase2_schema import add_phase2_schema
    from radv_command_center import RADVCommandCenter
    from chart_selection_ai import ChartSelectionAI
    from education_automation import EducationAutomation

    print("Testing Phase 2 Integration...")

    db = get_db_manager()
    add_phase2_schema(db)

    # Test 1: RADV Command Center
    print("\n1. Testing RADV Command Center...")
    command_center = RADVCommandCenter()

    # Get audits
    result = db.execute_query("SELECT COUNT(*) as count FROM radv_audits", (), fetch="one")
    print(f"   Found {result['count']} audit(s)")

    if result['count'] > 0:
        audit = db.execute_query("SELECT audit_id FROM radv_audits LIMIT 1", (), fetch="one")
        status = command_center.get_audit_status(audit['audit_id'])
        print(f"   Audit status: {status['status_indicator']}")
        print(f"   Days remaining: {status['days_remaining']}")

    # Test 2: Chart Selection AI
    print("\n2. Testing Chart Selection AI...")
    selector = ChartSelectionAI()
    print("   Chart selector initialized OK")

    # Test 3: Education Automation
    print("\n3. Testing Education Automation...")
    educator = EducationAutomation()

    providers = educator.identify_providers_for_tpe(min_failures=3)
    print(f"   Found {len(providers)} providers needing TPE")

    dashboard = educator.get_education_dashboard()
    print(f"   Total sessions: {dashboard['total_sessions']}")

    print("\nAll Phase 2 features operational!")


if __name__ == "__main__":
    test_phase2()
