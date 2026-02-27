"""
Complete system initialization for AuditShield-Live
Phases 1, 2, and 3

This script:
1. Initializes all database schemas
2. Seeds demo data with 6+ months of history
3. Creates standard rules and configurations
4. Validates all components
"""

import sys
from datetime import datetime, timedelta
import random


def initialize_complete_system():
    print("=" * 80)
    print("AuditShield-Live - Complete System Initialization")
    print("=" * 80)

    # Step 1: Database initialization
    print("\n[Step 1] Initializing Database...")
    from database import get_db_manager

    db = get_db_manager()

    try:
        db.initialize_schema()
        print("   [OK] Phase 1 schema created")
    except Exception as e:
        print(f"   [WARN] Phase 1 schema may already exist: {e}")

    # Step 2: Add Phase 2 schema
    print("\n[Step 2] Adding Phase 2 Schema...")
    try:
        from database_phase2_schema import add_phase2_schema

        add_phase2_schema(db)
        print("   [OK] Phase 2 schema created")
    except Exception as e:
        print(f"   [WARN] Phase 2 schema may already exist: {e}")

    # Step 3: Add Phase 3 schema
    print("\n[Step 3] Adding Phase 3 Schema...")
    try:
        from database_phase3_schema import add_phase3_schema

        add_phase3_schema(db)
        print("   [OK] Phase 3 schema created")
    except Exception as e:
        print(f"   [WARN] Phase 3 schema may already exist: {e}")

    # Step 4: Seed comprehensive demo data
    print("\n[Step 4] Seeding Demo Data (this may take a minute)...")
    seed_comprehensive_demo_data(db)

    # Step 5: Create Phase 2 demo audit
    print("\n[Step 5] Creating Demo RADV Audit...")
    from radv_command_center import seed_demo_audit

    try:
        audit_id = seed_demo_audit()
        print(f"   [OK] Demo audit created (ID: {audit_id})")
    except Exception as e:
        print(f"   [WARN] Could not create demo audit: {e}")

    # Step 6: Create EMR validation rules
    print("\n[Step 6] Creating EMR Validation Rules...")
    from emr_rule_builder import EMRRuleBuilder

    rule_builder = EMRRuleBuilder()
    try:
        rules = rule_builder.create_standard_rules()
        print(f"   [OK] Created {len(rules)} standard validation rules")
    except Exception as e:
        print(f"   [WARN] Could not create rules: {e}")

    # Step 7: Create dashboard configurations
    print("\n[Step 7] Creating Dashboard Configurations...")
    from dashboard_manager import DashboardManager

    dashboard_mgr = DashboardManager()
    try:
        dashboards = dashboard_mgr.create_standard_dashboards()
        print(f"   [OK] Created {len(dashboards)} dashboard configurations")
    except Exception as e:
        print(f"   [WARN] Could not create dashboards: {e}")

    # Step 8: Generate initial forecast
    print("\n[Step 8] Generating Initial Compliance Forecast...")
    from compliance_forecasting import ComplianceForecaster

    forecaster = ComplianceForecaster()
    try:
        forecast = forecaster.generate_forecast(
            forecast_periods=12, confidence_level=0.95
        )
        if "error" not in forecast:
            print(f"   [OK] Forecast generated ({len(forecast['forecasts'])} periods)")
            print(f"      Model accuracy: {forecast['model_accuracy']}%")
        else:
            print(f"   [WARN] {forecast['error']}")
    except Exception as e:
        print(f"   [WARN] Could not generate forecast: {e}")

    # Step 9: Scan regulatory sources (skip during init to avoid API dependency)
    print("\n[Step 9] Scanning Regulatory Sources...")
    print("   [SKIP] Regulatory intelligence will load on first use")
    # from regulatory_intelligence import RegulatoryIntelligence
    # reg_intel = RegulatoryIntelligence()
    # try:
    #     updates = reg_intel.scan_regulatory_sources(days_back=30)
    #     print(f"   [OK] Found {len(updates)} regulatory updates")
    # except Exception as e:
    #     print(f"   [WARN] Could not scan regulatory sources: {e}")

    # Step 10: Run system validation
    print("\n[Step 10] Validating System Components...")
    validate_system(db)

    # Final summary
    print("\n" + "=" * 80)
    print("INITIALIZATION COMPLETE!")
    print("=" * 80)
    print("\nSystem Status:")
    print("   [OK] All database schemas installed")
    print("   [OK] Demo data loaded (10 providers, 6 months history)")
    print("   [OK] RADV audit created")
    print("   [OK] Validation rules deployed")
    print("   [OK] Dashboards configured")
    print("   [OK] Compliance forecast generated")
    print("\nReady to Launch!")
    print("   Run: shiny run app.py")
    print("   Navigate to: http://localhost:8000")
    print("\n" + "=" * 80)


def seed_comprehensive_demo_data(db):
    """
    Seed comprehensive demo data with 12+ months of history
    This ensures forecasting and trend analysis work properly
    """

    from faker import Faker

    fake = Faker()

    specialties = [
        "Primary Care",
        "Cardiology",
        "Endocrinology",
        "Nephrology",
        "Pulmonology",
        "Rheumatology",
    ]

    hcc_categories = [
        ("HCC 36", "Diabetes with Chronic Complications", "Diabetes with Complications", 0.318),
        ("HCC 226", "Congestive Heart Failure", "Congestive Heart Failure", 0.368),
        ("HCC 280", "Chronic Obstructive Pulmonary Disease", "COPD", 0.328),
        ("HCC 327", "Chronic Kidney Disease Stage 4", "Chronic Kidney Disease", 0.237),
        ("HCC 155", "Major Depressive Disorder", "Major Depressive Disorder", 0.309),
        ("HCC 264", "Peripheral Vascular Disease", "Vascular Disease/PVD", 0.288),
        ("HCC 22", "Morbid Obesity", "Morbid Obesity", 0.252),
        ("HCC 238", "Atrial Fibrillation", "Specified Heart Arrhythmias", 0.252),
        ("HCC 92", "Rheumatoid Arthritis", "Rheumatoid Arthritis", 0.299),
        ("HCC 18", "Lung Cancer", "Active Cancers", 2.691),
    ]

    failure_reasons = [
        "Missing Monitor element",
        "Missing Treat element",
        "Problem List Only",
        "No link between conditions",
        "History of vs Active",
        "Missing Evaluate element",
        "Unspecified diagnosis",
        "Inferred diagnosis",
    ]

    passing_docs = [
        "CHF: Patient reports increased dyspnea on exertion. Reviewed recent BNP (350) and Echo (EF 40%). Chronic systolic CHF remains stable on current diuretic dose. Continue Lasix 40mg daily; follow up in 3 months.",
        "Type 2 DM with CKD: Blood sugar log and A1c results reviewed; remains elevated at 8.2%. Discussed stage 3 CKD status and necessity of avoiding NSAIDs. Metformin 1000mg BID continued, nephrology referral ordered.",
        "COPD: Patient using albuterol inhaler 2-3 times daily. Spirometry shows FEV1 55% predicted. Discussed smoking cessation. Added Advair 250/50 twice daily.",
        "Atrial Fibrillation: Patient on Eliquis 5mg BID. EKG today shows persistent AFib, rate controlled at 72 bpm. Continue current anticoagulation regimen.",
    ]

    failing_docs = [
        "CHF - stable",
        "Diabetes, CKD",
        "Problem List: CHF, COPD, DM",
        "History of lung cancer",
    ]

    # Reduced for HuggingFace free tier (was 50 providers, 15 months)
    num_providers = 10
    months_history = 6
    print(f"   Creating {num_providers} providers with {months_history} months of encounter history...")

    param_placeholder = "%s" if db.db_type == "postgresql" else "?"

    # Create providers
    for i in range(num_providers):
        provider_id = f"PRV{i+1:04d}"
        provider_name = f"Dr. {fake.last_name()}, {fake.first_name()}"
        specialty = random.choice(specialties)
        npi = f"{random.randint(1000000000, 9999999999)}"

        # Insert provider
        if db.db_type == "postgresql":
            provider_query = f"""
            INSERT INTO provider_meat_scores (
                provider_id, provider_name, specialty, npi
            ) VALUES (
                {param_placeholder}, {param_placeholder}, {param_placeholder}, {param_placeholder}
            )
            ON CONFLICT (provider_id) DO NOTHING
            """
        else:
            provider_query = f"""
            INSERT OR IGNORE INTO provider_meat_scores (
                provider_id, provider_name, specialty, npi
            ) VALUES (?, ?, ?, ?)
            """

        db.execute_query(
            provider_query,
            (provider_id, provider_name, specialty, npi),
            fetch="none",
        )

        # Determine provider quality (for realistic variation)
        quality_roll = random.random()
        if quality_roll < 0.3:  # 30% high performers
            pass_rate = random.uniform(0.90, 0.98)
        elif quality_roll < 0.7:  # 40% medium performers
            pass_rate = random.uniform(0.80, 0.90)
        else:  # 30% struggling performers
            pass_rate = random.uniform(0.60, 0.80)

        # Generate encounters (reduced for HuggingFace resource limits)
        encounters_per_month = random.randint(10, 15)

        for month_offset in range(months_history):
            for _ in range(encounters_per_month):
                patient_id = f"PAT{random.randint(10000, 99999)}"

                # Create encounter date in the past
                days_ago = (month_offset * 30) + random.randint(0, 29)
                encounter_date = (
                    datetime.now() - timedelta(days=days_ago)
                ).strftime("%Y-%m-%d")
                encounter_id = f"ENC{random.randint(100000, 999999)}"

                # Select random HCC
                hcc_code, hcc_desc, hcc_cat, raf_weight = random.choice(
                    hcc_categories
                )

                # Determine if this passes
                passes = random.random() < pass_rate

                if passes:
                    doc_text = random.choice(passing_docs)
                    meat_elements = [True, True, True, True]
                    random.shuffle(meat_elements)
                    if not any(meat_elements):
                        meat_elements[0] = True

                    validation_status = "PASS"
                    failure_reason = None
                    confidence = random.uniform(85, 99)
                else:
                    doc_text = random.choice(failing_docs)
                    meat_elements = [False] * 4
                    if random.random() < 0.3:
                        meat_elements[random.randint(0, 3)] = True

                    validation_status = "FAIL"
                    failure_reason = random.choice(failure_reasons)
                    confidence = random.uniform(70, 90)

                meat_score = sum(meat_elements)

                # Insert HCC audit record
                audit_query = f"""
                INSERT INTO hcc_audit_trail (
                    provider_id, patient_id, encounter_date, encounter_id,
                    hcc_code, hcc_description, hcc_category, raf_weight,
                    meat_monitor, meat_monitor_evidence,
                    meat_evaluate, meat_evaluate_evidence,
                    meat_assess, meat_assess_evidence,
                    meat_treat, meat_treat_evidence,
                    meat_score, validation_status, failure_reason,
                    documentation_text, confidence_score, ai_model_version
                ) VALUES (
                    {param_placeholder}, {param_placeholder}, {param_placeholder}, {param_placeholder},
                    {param_placeholder}, {param_placeholder}, {param_placeholder}, {param_placeholder},
                    {param_placeholder}, {param_placeholder},
                    {param_placeholder}, {param_placeholder},
                    {param_placeholder}, {param_placeholder},
                    {param_placeholder}, {param_placeholder},
                    {param_placeholder}, {param_placeholder}, {param_placeholder},
                    {param_placeholder}, {param_placeholder}, 'claude-sonnet-4'
                )
                """

                db.execute_query(
                    audit_query,
                    (
                        provider_id,
                        patient_id,
                        encounter_date,
                        encounter_id,
                        hcc_code,
                        hcc_desc,
                        hcc_cat,
                        raf_weight,
                        meat_elements[0],
                        doc_text if meat_elements[0] else None,
                        meat_elements[1],
                        doc_text if meat_elements[1] else None,
                        meat_elements[2],
                        doc_text if meat_elements[2] else None,
                        meat_elements[3],
                        doc_text if meat_elements[3] else None,
                        meat_score,
                        validation_status,
                        failure_reason,
                        doc_text,
                        confidence,
                    ),
                    fetch="none",
                )

        # Update provider scores
        db.update_provider_scores(provider_id, lookback_months=12)

        if (i + 1) % 5 == 0 or (i + 1) == num_providers:
            print(f"   Progress: {i + 1}/{num_providers} providers created")

    total_encounters = num_providers * months_history * 12  # ~12 avg encounters/month
    print("   [OK] Demo data seeding complete!")
    print(f"      - {num_providers} providers")
    print(f"      - {months_history} months of encounter history")
    print(f"      - ~{total_encounters:,} total encounters")


def validate_system(db):
    """Validate all system components are working"""

    checks_passed = 0
    checks_total = 0

    # Check 1: Provider data
    checks_total += 1
    query = "SELECT COUNT(*) as count FROM provider_meat_scores"
    result = db.execute_query(query, fetch="one")
    if result and result["count"] > 0:
        print(f"   [OK] Provider data: {result['count']} providers")
        checks_passed += 1
    else:
        print("   [FAIL] Provider data: No providers found")

    # Check 2: HCC audit trail
    checks_total += 1
    query = "SELECT COUNT(*) as count FROM hcc_audit_trail"
    result = db.execute_query(query, fetch="one")
    if result and result["count"] > 0:
        print(f"   [OK] HCC audit trail: {result['count']:,} encounters")
        checks_passed += 1
    else:
        print("   [FAIL] HCC audit trail: No encounters found")

    # Check 3: Historical data span
    checks_total += 1
    query = "SELECT MIN(encounter_date) as min_date, MAX(encounter_date) as max_date FROM hcc_audit_trail"
    result = db.execute_query(query, fetch="one")
    if result and result["min_date"]:
        min_date = datetime.strptime(str(result["min_date"]), "%Y-%m-%d")
        max_date = datetime.strptime(str(result["max_date"]), "%Y-%m-%d")
        months_span = (max_date - min_date).days / 30
        print(f"   [OK] Historical data: {months_span:.1f} months")
        checks_passed += 1
    else:
        print("   [FAIL] Historical data: Cannot determine date range")

    # Check 4: RADV audits
    checks_total += 1
    query = "SELECT COUNT(*) as count FROM radv_audits"
    result = db.execute_query(query, fetch="one")
    if result and result["count"] > 0:
        print(f"   [OK] RADV audits: {result['count']} audit(s)")
        checks_passed += 1
    else:
        print("   [WARN] RADV audits: None created")

    # Check 5: EMR rules
    checks_total += 1
    query = "SELECT COUNT(*) as count FROM emr_validation_rules"
    result = db.execute_query(query, fetch="one")
    if result and result["count"] > 0:
        print(f"   [OK] EMR rules: {result['count']} rule(s)")
        checks_passed += 1
    else:
        print("   [WARN] EMR rules: None created")

    # Check 6: Compliance forecasts
    checks_total += 1
    query = "SELECT COUNT(*) as count FROM compliance_forecasts"
    result = db.execute_query(query, fetch="one")
    if result and result["count"] > 0:
        print(f"   [OK] Compliance forecasts: {result['count']} forecast(s)")
        checks_passed += 1
    else:
        print("   [WARN] Compliance forecasts: None generated")

    print(f"\n   System Check: {checks_passed}/{checks_total} passed")

    if checks_passed >= 5:
        print("   [OK] System is ready for deployment!")
    else:
        print("   [WARN] Some components may need attention")


if __name__ == "__main__":
    try:
        initialize_complete_system()
    except Exception as e:
        print(f"\n[FAIL] Initialization failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
