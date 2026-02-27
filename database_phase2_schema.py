"""
Phase 2 database extensions for audit response workflow
Run this to add Phase 2 tables to existing database
"""


def add_phase2_schema(db_manager):
    """Add Phase 2 tables to existing database"""
    
    if db_manager.db_type == "postgresql":
        serial_type = "SERIAL"
        text_array = "TEXT[]"
        timestamp_default = "CURRENT_TIMESTAMP"
        json_type = "JSONB"
    else:
        serial_type = "INTEGER PRIMARY KEY AUTOINCREMENT"
        text_array = "TEXT"
        timestamp_default = "CURRENT_TIMESTAMP"
        json_type = "TEXT"  # Store JSON as text in SQLite
    
    schema_sql = f"""
    -- RADV Audit Tracking
    CREATE TABLE IF NOT EXISTS radv_audits (
        audit_id {serial_type},
        audit_notice_id VARCHAR(50) UNIQUE NOT NULL,
        contract_id VARCHAR(50) NOT NULL,
        contract_name VARCHAR(200),
        audit_year INTEGER NOT NULL,
        notification_date DATE NOT NULL,
        medical_record_due_date DATE NOT NULL,
        sample_size INTEGER NOT NULL,
        audit_status VARCHAR(20) DEFAULT 'ACTIVE',
        final_error_rate DECIMAL(5,2),
        financial_outcome DECIMAL(12,2),
        created_at TIMESTAMP DEFAULT {timestamp_default},
        updated_at TIMESTAMP DEFAULT {timestamp_default}
    );

    -- Sampled Enrollees (from CMS audit notice)
    CREATE TABLE IF NOT EXISTS audit_sample_enrollees (
        sample_id {serial_type},
        audit_id INTEGER NOT NULL,
        enrollee_id VARCHAR(50) NOT NULL,
        enrollee_name VARCHAR(200),
        date_of_birth DATE,
        hccs_to_validate {text_array},
        total_raf_weight DECIMAL(5,3),
        record_request_status VARCHAR(20) DEFAULT 'PENDING',
        records_received_date DATE,
        submission_status VARCHAR(20) DEFAULT 'NOT_SUBMITTED',
        submitted_date DATE,
        validation_result VARCHAR(20),
        failed_hccs {text_array},
        notes TEXT,
        created_at TIMESTAMP DEFAULT {timestamp_default}
    );

    -- Medical Records for Audit
    CREATE TABLE IF NOT EXISTS audit_medical_records (
        record_id {serial_type},
        sample_id INTEGER NOT NULL,
        audit_id INTEGER NOT NULL,
        enrollee_id VARCHAR(50) NOT NULL,
        encounter_date DATE NOT NULL,
        encounter_type VARCHAR(50),
        provider_id VARCHAR(50),
        provider_name VARCHAR(200),
        hccs_supported {text_array},
        record_quality_score DECIMAL(5,2),
        ai_recommendation_rank INTEGER,
        meat_completeness_score DECIMAL(5,2),
        documentation_gaps TEXT,
        selected_for_submission BOOLEAN DEFAULT FALSE,
        submitted_to_cms BOOLEAN DEFAULT FALSE,
        file_path TEXT,
        created_at TIMESTAMP DEFAULT {timestamp_default}
    );

    -- Chart Selection AI Scores
    CREATE TABLE IF NOT EXISTS chart_selection_scores (
        score_id {serial_type},
        record_id INTEGER NOT NULL,
        sample_id INTEGER NOT NULL,
        overall_score DECIMAL(5,2) NOT NULL,
        meat_score DECIMAL(5,2),
        documentation_quality_score DECIMAL(5,2),
        completeness_score DECIMAL(5,2),
        provider_reliability_score DECIMAL(5,2),
        encounter_recency_score DECIMAL(5,2),
        ai_analysis {json_type},
        recommendation VARCHAR(20),
        confidence_level DECIMAL(5,2),
        created_at TIMESTAMP DEFAULT {timestamp_default}
    );

    -- Provider Education Sessions (TPE)
    CREATE TABLE IF NOT EXISTS education_sessions (
        session_id {serial_type},
        provider_id VARCHAR(50) NOT NULL,
        session_type VARCHAR(50) NOT NULL,
        focus_areas {text_array},
        scheduled_date DATE NOT NULL,
        scheduled_time TIME,
        educator_assigned VARCHAR(100),
        session_status VARCHAR(20) DEFAULT 'SCHEDULED',
        completed_date DATE,
        attendance_status VARCHAR(20),
        pre_session_validation_rate DECIMAL(5,2),
        post_session_validation_rate DECIMAL(5,2),
        materials_sent BOOLEAN DEFAULT FALSE,
        materials_list {text_array},
        followup_required BOOLEAN DEFAULT FALSE,
        followup_date DATE,
        session_notes TEXT,
        created_at TIMESTAMP DEFAULT {timestamp_default}
    );

    -- Education Materials Library
    CREATE TABLE IF NOT EXISTS education_materials (
        material_id {serial_type},
        material_name VARCHAR(200) NOT NULL,
        material_type VARCHAR(50),
        category VARCHAR(50),
        hcc_categories {text_array},
        file_path TEXT,
        description TEXT,
        last_updated DATE,
        usage_count INTEGER DEFAULT 0,
        effectiveness_score DECIMAL(5,2),
        created_at TIMESTAMP DEFAULT {timestamp_default}
    );

    -- Audit Timeline Tasks
    CREATE TABLE IF NOT EXISTS audit_tasks (
        task_id {serial_type},
        audit_id INTEGER NOT NULL,
        task_name VARCHAR(200) NOT NULL,
        task_category VARCHAR(50),
        due_date DATE NOT NULL,
        assigned_to VARCHAR(100),
        priority VARCHAR(20) DEFAULT 'MEDIUM',
        status VARCHAR(20) DEFAULT 'PENDING',
        completed_date DATE,
        completion_notes TEXT,
        dependencies {text_array},
        created_at TIMESTAMP DEFAULT {timestamp_default}
    );

    -- Create indexes
    CREATE INDEX IF NOT EXISTS idx_audit_enrollees ON audit_sample_enrollees(audit_id);
    CREATE INDEX IF NOT EXISTS idx_audit_records ON audit_medical_records(sample_id);
    CREATE INDEX IF NOT EXISTS idx_chart_scores ON chart_selection_scores(record_id);
    CREATE INDEX IF NOT EXISTS idx_education_provider ON education_sessions(provider_id);
    CREATE INDEX IF NOT EXISTS idx_audit_tasks ON audit_tasks(audit_id);
    """
    
    # Execute schema creation
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        for statement in schema_sql.split(';'):
            if statement.strip():
                try:
                    cursor.execute(statement)
                except Exception as e:
                    if "already exists" not in str(e).lower():
                        raise
        conn.commit()
        cursor.close()
    
    print("Phase 2 schema added successfully.")


# Run this to upgrade existing database
if __name__ == "__main__":
    from database import get_db_manager
    
    db = get_db_manager()
    add_phase2_schema(db)
    print("Phase 2 database schema installation complete!")
