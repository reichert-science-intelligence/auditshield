"""
Phase 3 database extensions for proactive intelligence
Real-time validation, forecasting, and regulatory tracking
"""


def add_phase3_schema(db_manager):
    """Add Phase 3 tables to existing database"""

    if db_manager.db_type == "postgresql":
        serial_type = "SERIAL"
        text_array = "TEXT[]"
        timestamp_default = "CURRENT_TIMESTAMP"
        json_type = "JSONB"
    else:
        serial_type = "INTEGER PRIMARY KEY AUTOINCREMENT"
        text_array = "TEXT"
        timestamp_default = "CURRENT_TIMESTAMP"
        json_type = "TEXT"

    schema_sql = f"""
    -- Real-time validation queue
    CREATE TABLE IF NOT EXISTS realtime_validation_queue (
        queue_id {serial_type},
        encounter_id VARCHAR(50) NOT NULL,
        patient_id VARCHAR(50) NOT NULL,
        provider_id VARCHAR(50) NOT NULL,
        encounter_date DATE NOT NULL,
        hcc_codes {text_array},
        documentation_text TEXT,
        validation_priority VARCHAR(20) DEFAULT 'NORMAL',
        queue_status VARCHAR(20) DEFAULT 'PENDING',
        queued_at TIMESTAMP DEFAULT {timestamp_default},
        processed_at TIMESTAMP,
        validation_results {json_type},
        auto_alerts {text_array},
        created_at TIMESTAMP DEFAULT {timestamp_default}
    );

    -- HCC reconciliation (add/delete recommendations)
    CREATE TABLE IF NOT EXISTS hcc_reconciliation (
        reconciliation_id {serial_type},
        patient_id VARCHAR(50) NOT NULL,
        encounter_id VARCHAR(50),
        reconciliation_type VARCHAR(10) NOT NULL,
        hcc_code VARCHAR(10) NOT NULL,
        hcc_description VARCHAR(200),
        current_status VARCHAR(20),
        recommended_action VARCHAR(20),
        supporting_evidence TEXT,
        confidence_score DECIMAL(5,2),
        financial_impact DECIMAL(12,2),
        action_taken BOOLEAN DEFAULT FALSE,
        action_date DATE,
        action_by VARCHAR(100),
        created_at TIMESTAMP DEFAULT {timestamp_default}
    );

    -- Compliance forecast models
    CREATE TABLE IF NOT EXISTS compliance_forecasts (
        forecast_id {serial_type},
        forecast_date DATE NOT NULL,
        forecast_period VARCHAR(20) NOT NULL,
        contract_id VARCHAR(50),
        predicted_validation_rate DECIMAL(5,2),
        predicted_error_rate DECIMAL(5,2),
        predicted_financial_impact DECIMAL(12,2),
        confidence_interval_low DECIMAL(5,2),
        confidence_interval_high DECIMAL(5,2),
        trend_direction VARCHAR(20),
        key_drivers {text_array},
        forecast_model_version VARCHAR(20),
        created_at TIMESTAMP DEFAULT {timestamp_default}
    );

    -- Regulatory updates tracking
    CREATE TABLE IF NOT EXISTS regulatory_updates (
        update_id {serial_type},
        source VARCHAR(100) NOT NULL,
        update_date DATE NOT NULL,
        update_type VARCHAR(50),
        title VARCHAR(500),
        summary TEXT,
        full_text TEXT,
        affected_hccs {text_array},
        impact_level VARCHAR(20),
        implementation_date DATE,
        url TEXT,
        processed BOOLEAN DEFAULT FALSE,
        action_items {text_array},
        created_at TIMESTAMP DEFAULT {timestamp_default}
    );

    -- EMR validation rules
    CREATE TABLE IF NOT EXISTS emr_validation_rules (
        rule_id {serial_type},
        rule_name VARCHAR(200) NOT NULL,
        rule_type VARCHAR(50) NOT NULL,
        hcc_codes {text_array},
        condition_logic {json_type},
        validation_message TEXT,
        rule_severity VARCHAR(20) DEFAULT 'WARNING',
        active BOOLEAN DEFAULT TRUE,
        trigger_count INTEGER DEFAULT 0,
        last_triggered TIMESTAMP,
        created_by VARCHAR(100),
        created_at TIMESTAMP DEFAULT {timestamp_default},
        updated_at TIMESTAMP DEFAULT {timestamp_default}
    );

    -- Dashboard configurations
    CREATE TABLE IF NOT EXISTS dashboard_configs (
        config_id {serial_type},
        dashboard_name VARCHAR(100) NOT NULL,
        user_role VARCHAR(50) NOT NULL,
        widget_layout {json_type},
        filter_defaults {json_type},
        refresh_interval_seconds INTEGER DEFAULT 300,
        active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT {timestamp_default}
    );

    -- Automated alerts/notifications
    CREATE TABLE IF NOT EXISTS automated_alerts (
        alert_id {serial_type},
        alert_type VARCHAR(50) NOT NULL,
        severity VARCHAR(20) NOT NULL,
        title VARCHAR(200),
        message TEXT,
        triggered_by VARCHAR(100),
        triggered_at TIMESTAMP DEFAULT {timestamp_default},
        recipients {text_array},
        delivery_status VARCHAR(20) DEFAULT 'PENDING',
        delivered_at TIMESTAMP,
        related_entity_type VARCHAR(50),
        related_entity_id VARCHAR(50),
        action_required BOOLEAN DEFAULT FALSE,
        action_taken BOOLEAN DEFAULT FALSE,
        dismissed BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT {timestamp_default}
    );

    -- Performance metrics tracking
    CREATE TABLE IF NOT EXISTS system_metrics (
        metric_id {serial_type},
        metric_date DATE NOT NULL,
        metric_name VARCHAR(100) NOT NULL,
        metric_value DECIMAL(12,2),
        metric_category VARCHAR(50),
        comparison_period VARCHAR(20),
        previous_value DECIMAL(12,2),
        pct_change DECIMAL(5,2),
        trend VARCHAR(20),
        created_at TIMESTAMP DEFAULT {timestamp_default}
    );

    -- Create indexes
    CREATE INDEX IF NOT EXISTS idx_validation_queue_status ON realtime_validation_queue(queue_status);
    CREATE INDEX IF NOT EXISTS idx_validation_queue_provider ON realtime_validation_queue(provider_id);
    CREATE INDEX IF NOT EXISTS idx_reconciliation_patient ON hcc_reconciliation(patient_id);
    CREATE INDEX IF NOT EXISTS idx_reconciliation_action ON hcc_reconciliation(action_taken);
    CREATE INDEX IF NOT EXISTS idx_forecast_date ON compliance_forecasts(forecast_date);
    CREATE INDEX IF NOT EXISTS idx_regulatory_updates_date ON regulatory_updates(update_date);
    CREATE INDEX IF NOT EXISTS idx_emr_rules_active ON emr_validation_rules(active);
    CREATE INDEX IF NOT EXISTS idx_alerts_severity ON automated_alerts(severity, delivery_status);
    """

    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        for statement in schema_sql.split(";"):
            if statement.strip():
                try:
                    cursor.execute(statement)
                except Exception as e:
                    if "already exists" not in str(e).lower():
                        raise
        conn.commit()
        cursor.close()

    print("Phase 3 schema added successfully")


if __name__ == "__main__":
    from database import get_db_manager

    db = get_db_manager()
    add_phase3_schema(db)
    print("Phase 3 database schema installation complete!")
