"""
AuditShield Phase 1 - Database Manager
Unified interface for SQLite (dev) and PostgreSQL (prod)
"""
import os
import sqlite3
import pandas as pd
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from contextlib import contextmanager
import json

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from psycopg2.pool import SimpleConnectionPool
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False


class DatabaseManager:
    """
    Unified database interface supporting SQLite (dev) and PostgreSQL (prod)
    Handles connection pooling, query execution, and data aggregation
    """

    def __init__(self, db_type: str = "sqlite", connection_string: Optional[str] = None):
        """
        Initialize database manager

        Args:
            db_type: "sqlite" or "postgresql"
            connection_string: Connection string for PostgreSQL, or path for SQLite
        """
        self.db_type = db_type.lower()

        if self.db_type == "postgresql" and POSTGRES_AVAILABLE:
            if not connection_string:
                connection_string = os.getenv(
                    "DATABASE_URL",
                    "postgresql://user:password@localhost:5432/auditshield"
                )
            self.pool = SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=connection_string
            )
        else:
            self.db_type = "sqlite"
            self.db_path = connection_string or os.path.join(
                os.path.dirname(__file__), "auditshield.db"
            )
            self.pool = None

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        if self.db_type == "postgresql":
            conn = self.pool.getconn()
            try:
                yield conn
            finally:
                self.pool.putconn(conn)
        else:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            finally:
                conn.close()

    def execute_query(self, query: str, params: Optional[Tuple] = None,
                     fetch: str = "all") -> Any:
        """Execute a query and return results"""
        with self.get_connection() as conn:
            if self.db_type == "postgresql":
                cursor = conn.cursor(cursor_factory=RealDictCursor)
            else:
                cursor = conn.cursor()

            try:
                cursor.execute(query, params or ())

                if fetch == "all":
                    results = cursor.fetchall()
                    if self.db_type == "sqlite":
                        results = [dict(row) for row in results]
                    return results
                elif fetch == "one":
                    result = cursor.fetchone()
                    if self.db_type == "sqlite" and result:
                        result = dict(result)
                    return result
                else:
                    conn.commit()
                    return cursor.rowcount

            except Exception as e:
                conn.rollback()
                raise Exception(f"Database error: {str(e)}")
            finally:
                cursor.close()

    def initialize_schema(self):
        """Create all tables if they don't exist"""
        if self.db_type == "postgresql":
            serial_type = "SERIAL"
            text_array = "TEXT[]"
            timestamp_default = "CURRENT_TIMESTAMP"
        else:
            serial_type = "INTEGER PRIMARY KEY AUTOINCREMENT"
            text_array = "TEXT"
            timestamp_default = "CURRENT_TIMESTAMP"

        schema_sql = f"""
        CREATE TABLE IF NOT EXISTS provider_meat_scores (
            provider_id VARCHAR(50) PRIMARY KEY,
            provider_name VARCHAR(200) NOT NULL,
            specialty VARCHAR(100),
            npi VARCHAR(10),
            total_hccs_submitted INTEGER DEFAULT 0,
            total_hccs_validated INTEGER DEFAULT 0,
            validation_rate DECIMAL(5,2),
            last_calculated_date DATE,
            risk_tier VARCHAR(10),
            financial_risk_estimate DECIMAL(12,2),
            quarter VARCHAR(7),
            contract_id VARCHAR(50),
            created_at TIMESTAMP DEFAULT {timestamp_default},
            updated_at TIMESTAMP DEFAULT {timestamp_default}
        );

        CREATE TABLE IF NOT EXISTS hcc_audit_trail (
            audit_id {serial_type},
            provider_id VARCHAR(50) NOT NULL,
            patient_id VARCHAR(50) NOT NULL,
            encounter_date DATE NOT NULL,
            encounter_id VARCHAR(50),
            hcc_code VARCHAR(10) NOT NULL,
            hcc_description VARCHAR(200),
            hcc_category VARCHAR(50),
            raf_weight DECIMAL(5,3),
            meat_monitor BOOLEAN DEFAULT FALSE,
            meat_monitor_evidence TEXT,
            meat_evaluate BOOLEAN DEFAULT FALSE,
            meat_evaluate_evidence TEXT,
            meat_assess BOOLEAN DEFAULT FALSE,
            meat_assess_evidence TEXT,
            meat_treat BOOLEAN DEFAULT FALSE,
            meat_treat_evidence TEXT,
            meat_score INTEGER,
            validation_status VARCHAR(20),
            failure_reason VARCHAR(500),
            documentation_text TEXT,
            confidence_score DECIMAL(5,2),
            ai_model_version VARCHAR(20),
            reviewed_by VARCHAR(100),
            reviewed_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT {timestamp_default},
            updated_at TIMESTAMP DEFAULT {timestamp_default}
        );

        CREATE TABLE IF NOT EXISTS failure_patterns (
            pattern_id {serial_type},
            provider_id VARCHAR(50) NOT NULL,
            failure_category VARCHAR(100) NOT NULL,
            hcc_category VARCHAR(50),
            occurrence_count INTEGER DEFAULT 0,
            example_encounters {text_array},
            last_occurrence DATE,
            remediation_status VARCHAR(20) DEFAULT 'OPEN',
            assigned_educator VARCHAR(100),
            education_date DATE,
            follow_up_score DECIMAL(5,2),
            created_at TIMESTAMP DEFAULT {timestamp_default},
            updated_at TIMESTAMP DEFAULT {timestamp_default}
        );

        CREATE TABLE IF NOT EXISTS provider_education (
            education_id {serial_type},
            provider_id VARCHAR(50) NOT NULL,
            education_type VARCHAR(50),
            focus_areas {text_array},
            educator VARCHAR(100),
            scheduled_date DATE,
            completed_date DATE,
            materials_sent BOOLEAN DEFAULT FALSE,
            attendance_status VARCHAR(20) DEFAULT 'SCHEDULED',
            pre_training_score DECIMAL(5,2),
            post_training_score DECIMAL(5,2),
            notes TEXT,
            created_at TIMESTAMP DEFAULT {timestamp_default}
        );

        CREATE INDEX IF NOT EXISTS idx_audit_provider ON hcc_audit_trail(provider_id);
        CREATE INDEX IF NOT EXISTS idx_audit_encounter_date ON hcc_audit_trail(encounter_date);
        CREATE INDEX IF NOT EXISTS idx_audit_validation_status ON hcc_audit_trail(validation_status);
        CREATE INDEX IF NOT EXISTS idx_audit_hcc_category ON hcc_audit_trail(hcc_category);
        CREATE INDEX IF NOT EXISTS idx_patterns_provider ON failure_patterns(provider_id);
        CREATE INDEX IF NOT EXISTS idx_education_provider ON provider_education(provider_id);
        """

        with self.get_connection() as conn:
            cursor = conn.cursor()
            for statement in schema_sql.split(';'):
                if statement.strip():
                    try:
                        cursor.execute(statement)
                    except Exception:
                        pass
            conn.commit()
            cursor.close()

    def get_provider_scores(self,
                           lookback_months: int = 12,
                           specialties: Optional[List[str]] = None,
                           risk_tiers: Optional[List[str]] = None,
                           min_hccs: int = 0) -> pd.DataFrame:
        """Get provider scorecard data with filters"""
        where_clauses = []
        params = []

        if specialties:
            ph = ','.join(['%s'] * len(specialties)) if self.db_type == 'postgresql' else ','.join(['?'] * len(specialties))
            where_clauses.append(f"pms.specialty IN ({ph})")
            params.extend(specialties)

        if risk_tiers:
            ph = ','.join(['%s'] * len(risk_tiers)) if self.db_type == 'postgresql' else ','.join(['?'] * len(risk_tiers))
            where_clauses.append(f"pms.risk_tier IN ({ph})")
            params.extend(risk_tiers)

        if min_hccs > 0:
            where_clauses.append("pms.total_hccs_submitted >= %s" if self.db_type == 'postgresql' else "pms.total_hccs_submitted >= ?")
            params.append(min_hccs)

        where_sql = " AND " + " AND ".join(where_clauses) if where_clauses else ""
        ph = '%s' if self.db_type == 'postgresql' else '?'

        query = f"""
        SELECT
            pms.provider_id, pms.provider_name, pms.specialty, pms.npi,
            pms.total_hccs_submitted, pms.total_hccs_validated, pms.validation_rate,
            pms.risk_tier, pms.financial_risk_estimate, pms.last_calculated_date,
            (SELECT failure_category FROM failure_patterns fp
             WHERE fp.provider_id = pms.provider_id
             ORDER BY occurrence_count DESC LIMIT 1) as top_failure_reason
        FROM provider_meat_scores pms
        WHERE 1=1 {where_sql}
        ORDER BY CASE pms.risk_tier WHEN 'RED' THEN 1 WHEN 'YELLOW' THEN 2 WHEN 'GREEN' THEN 3 END,
                 pms.validation_rate ASC
        """

        results = self.execute_query(query, tuple(params), fetch="all")

        if not results:
            return pd.DataFrame(columns=[
                'provider_id', 'provider_name', 'specialty', 'npi',
                'total_hccs_submitted', 'total_hccs_validated', 'validation_rate',
                'risk_tier', 'financial_risk_estimate', 'last_calculated_date',
                'top_failure_reason'
            ])

        df = pd.DataFrame(results)
        df['top_failure_reason'] = df['top_failure_reason'].fillna('No failures detected')
        return df

    def get_provider_failure_patterns(self, provider_id: str, lookback_months: int = 12) -> pd.DataFrame:
        """Get detailed failure patterns for a specific provider"""
        cutoff_date = datetime.now() - timedelta(days=lookback_months * 30)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d')
        ph = '%s' if self.db_type == 'postgresql' else '?'

        query = f"""
        SELECT failure_category, hcc_category, occurrence_count, remediation_status, last_occurrence
        FROM failure_patterns
        WHERE provider_id = {ph} AND (last_occurrence >= {ph} OR last_occurrence IS NULL)
        ORDER BY occurrence_count DESC LIMIT 10
        """
        results = self.execute_query(query, (provider_id, cutoff_str), fetch="all")

        if not results:
            return pd.DataFrame(columns=['failure_category', 'hcc_category', 'occurrence_count', 'remediation_status', 'last_occurrence'])
        return pd.DataFrame(results)

    def get_meat_element_breakdown(self, provider_id: str, lookback_months: int = 12) -> pd.DataFrame:
        """Get M.E.A.T. element compliance rates for a provider"""
        cutoff_date = datetime.now() - timedelta(days=lookback_months * 30)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d')
        ph = '%s' if self.db_type == 'postgresql' else '?'

        query = f"""
        SELECT 'Monitor' as element,
               ROUND(100.0 * SUM(CASE WHEN meat_monitor THEN 1 ELSE 0 END) / COUNT(*), 1) as compliance_rate
        FROM hcc_audit_trail WHERE provider_id = {ph} AND encounter_date >= {ph}
        UNION ALL
        SELECT 'Evaluate', ROUND(100.0 * SUM(CASE WHEN meat_evaluate THEN 1 ELSE 0 END) / COUNT(*), 1)
        FROM hcc_audit_trail WHERE provider_id = {ph} AND encounter_date >= {ph}
        UNION ALL
        SELECT 'Assess', ROUND(100.0 * SUM(CASE WHEN meat_assess THEN 1 ELSE 0 END) / COUNT(*), 1)
        FROM hcc_audit_trail WHERE provider_id = {ph} AND encounter_date >= {ph}
        UNION ALL
        SELECT 'Treat', ROUND(100.0 * SUM(CASE WHEN meat_treat THEN 1 ELSE 0 END) / COUNT(*), 1)
        FROM hcc_audit_trail WHERE provider_id = {ph} AND encounter_date >= {ph}
        """
        results = self.execute_query(query, (provider_id, cutoff_str) * 4, fetch="all")

        if not results:
            return pd.DataFrame({'element': ['Monitor', 'Evaluate', 'Assess', 'Treat'], 'compliance_rate': [0.0, 0.0, 0.0, 0.0]})
        return pd.DataFrame(results)

    def insert_hcc_audit(self, audit_data: Dict[str, Any]) -> int:
        """Insert a new HCC audit record"""
        ph = '%s' if self.db_type == 'postgresql' else '?'
        query = f"""
        INSERT INTO hcc_audit_trail (
            provider_id, patient_id, encounter_date, encounter_id,
            hcc_code, hcc_description, hcc_category, raf_weight,
            meat_monitor, meat_monitor_evidence, meat_evaluate, meat_evaluate_evidence,
            meat_assess, meat_assess_evidence, meat_treat, meat_treat_evidence,
            meat_score, validation_status, failure_reason, documentation_text,
            confidence_score, ai_model_version
        ) VALUES (
            {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph},
            {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph},
            {ph}, {ph}, {ph}, {ph}, {ph}, {ph}
        )
        """
        params = (
            audit_data['provider_id'], audit_data['patient_id'], audit_data['encounter_date'],
            audit_data.get('encounter_id'), audit_data['hcc_code'], audit_data.get('hcc_description'),
            audit_data.get('hcc_category'), audit_data.get('raf_weight', 0.0),
            audit_data.get('meat_monitor', False), audit_data.get('meat_monitor_evidence'),
            audit_data.get('meat_evaluate', False), audit_data.get('meat_evaluate_evidence'),
            audit_data.get('meat_assess', False), audit_data.get('meat_assess_evidence'),
            audit_data.get('meat_treat', False), audit_data.get('meat_treat_evidence'),
            audit_data.get('meat_score', 0), audit_data['validation_status'],
            audit_data.get('failure_reason'), audit_data.get('documentation_text'),
            audit_data.get('confidence_score', 0.0), audit_data.get('ai_model_version', 'claude-sonnet-4')
        )

        if self.db_type == "postgresql":
            query += " RETURNING audit_id"
            result = self.execute_query(query, params, fetch="one")
            return result['audit_id']
        else:
            self.execute_query(query, params, fetch="none")
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT last_insert_rowid()")
                return cursor.fetchone()[0]

    def update_hcc_audit(self, audit_id: int, validation_result: Dict[str, Any]) -> int:
        """Update an existing HCC audit record with new validation results"""
        ph = '%s' if self.db_type == 'postgresql' else '?'
        meat = validation_result.get('meat_elements', {})

        query = f"""
        UPDATE hcc_audit_trail SET
            meat_monitor = {ph}, meat_monitor_evidence = {ph},
            meat_evaluate = {ph}, meat_evaluate_evidence = {ph},
            meat_assess = {ph}, meat_assess_evidence = {ph},
            meat_treat = {ph}, meat_treat_evidence = {ph},
            meat_score = {ph}, validation_status = {ph}, failure_reason = {ph},
            confidence_score = {ph}, updated_at = CURRENT_TIMESTAMP
        WHERE audit_id = {ph}
        """
        params = (
            meat.get('monitor', {}).get('present', False),
            meat.get('monitor', {}).get('evidence'),
            meat.get('evaluate', {}).get('present', False),
            meat.get('evaluate', {}).get('evidence'),
            meat.get('assess', {}).get('present', False),
            meat.get('assess', {}).get('evidence'),
            meat.get('treat', {}).get('present', False),
            meat.get('treat', {}).get('evidence'),
            validation_result.get('meat_score', 0),
            validation_result.get('validation_status', 'PENDING'),
            validation_result.get('failure_reason'),
            validation_result.get('confidence_score', 0.0),
            audit_id
        )
        return self.execute_query(query, params, fetch="none")

    def update_provider_scores(self, provider_id: str, lookback_months: int = 12):
        """Recalculate and update provider scorecard metrics from audit trail"""
        cutoff_date = datetime.now() - timedelta(days=lookback_months * 30)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d')
        ph = '%s' if self.db_type == 'postgresql' else '?'

        calc_query = f"""
        SELECT COUNT(*) as total_hccs,
               SUM(CASE WHEN validation_status = 'PASS' THEN 1 ELSE 0 END) as validated_hccs,
               ROUND(100.0 * SUM(CASE WHEN validation_status = 'PASS' THEN 1 ELSE 0 END) / COUNT(*), 2) as validation_rate,
               SUM(CASE WHEN validation_status = 'FAIL' THEN raf_weight ELSE 0 END) * 1142.50 as financial_risk
        FROM hcc_audit_trail
        WHERE provider_id = {ph} AND encounter_date >= {ph}
        """
        metrics = self.execute_query(calc_query, (provider_id, cutoff_str), fetch="one")

        if not metrics or metrics['total_hccs'] == 0:
            return

        validation_rate = metrics['validation_rate'] or 0.0
        risk_tier = 'GREEN' if validation_rate >= 90 else ('YELLOW' if validation_rate >= 80 else 'RED')

        if self.db_type == "postgresql":
            self.execute_query(f"""
            INSERT INTO provider_meat_scores (provider_id, total_hccs_submitted, total_hccs_validated, validation_rate, financial_risk_estimate, risk_tier, last_calculated_date, updated_at)
            VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, CURRENT_DATE, CURRENT_TIMESTAMP)
            ON CONFLICT (provider_id) DO UPDATE SET
                total_hccs_submitted = EXCLUDED.total_hccs_submitted,
                total_hccs_validated = EXCLUDED.total_hccs_validated,
                validation_rate = EXCLUDED.validation_rate,
                financial_risk_estimate = EXCLUDED.financial_risk_estimate,
                risk_tier = EXCLUDED.risk_tier,
                last_calculated_date = CURRENT_DATE,
                updated_at = CURRENT_TIMESTAMP
            """, (provider_id, metrics['total_hccs'], metrics['validated_hccs'], validation_rate, metrics['financial_risk'], risk_tier), fetch="none")
        else:
            # SQLite: UPDATE first (provider must exist from seed/creation)
            existing = self.execute_query(
                f"SELECT provider_name, specialty, npi FROM provider_meat_scores WHERE provider_id = {ph}",
                (provider_id,), fetch="one"
            )
            pname = (existing or {}).get('provider_name') or 'Unknown'
            pspec = (existing or {}).get('specialty') or ''
            pnpi = (existing or {}).get('npi') or ''
            self.execute_query(f"""
            INSERT INTO provider_meat_scores (provider_id, provider_name, specialty, npi, total_hccs_submitted, total_hccs_validated, validation_rate, financial_risk_estimate, risk_tier, last_calculated_date, updated_at)
            VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, DATE('now'), DATETIME('now'))
            ON CONFLICT(provider_id) DO UPDATE SET
                total_hccs_submitted = excluded.total_hccs_submitted,
                total_hccs_validated = excluded.total_hccs_validated,
                validation_rate = excluded.validation_rate,
                financial_risk_estimate = excluded.financial_risk_estimate,
                risk_tier = excluded.risk_tier,
                last_calculated_date = DATE('now'),
                updated_at = DATETIME('now')
            """, (provider_id, pname, pspec, pnpi, metrics['total_hccs'], metrics['validated_hccs'], validation_rate, metrics['financial_risk'], risk_tier), fetch="none")

        self._update_failure_patterns(provider_id, lookback_months)

    def _update_failure_patterns(self, provider_id: str, lookback_months: int):
        """Aggregate failure patterns from audit trail"""
        cutoff_date = datetime.now() - timedelta(days=lookback_months * 30)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d')
        ph = '%s' if self.db_type == 'postgresql' else '?'

        pattern_query = f"""
        SELECT failure_reason as failure_category, hcc_category,
               COUNT(*) as occurrence_count, MAX(encounter_date) as last_occurrence
        FROM hcc_audit_trail
        WHERE provider_id = {ph} AND encounter_date >= {ph}
          AND validation_status = 'FAIL' AND failure_reason IS NOT NULL
        GROUP BY failure_reason, hcc_category
        """
        patterns = self.execute_query(pattern_query, (provider_id, cutoff_str), fetch="all")

        self.execute_query(f"DELETE FROM failure_patterns WHERE provider_id = {ph}", (provider_id,), fetch="none")

        for pattern in patterns:
            self.execute_query(f"""
            INSERT INTO failure_patterns (provider_id, failure_category, hcc_category, occurrence_count, last_occurrence)
            VALUES ({ph}, {ph}, {ph}, {ph}, {ph})
            """, (provider_id, pattern['failure_category'], pattern['hcc_category'], pattern['occurrence_count'], pattern['last_occurrence']), fetch="none")

    def get_provider_hccs(self, provider_id: str, lookback_months: int = 12) -> List[Dict]:
        """Get all HCC audit records for a provider (used by MEATValidator.batch_validate_provider)"""
        cutoff_date = datetime.now() - timedelta(days=lookback_months * 30)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d')
        ph = '%s' if self.db_type == 'postgresql' else '?'

        query = f"""
        SELECT audit_id, patient_id, encounter_date, encounter_id, hcc_code, hcc_description,
               hcc_category, raf_weight, validation_status, failure_reason, documentation_text,
               meat_monitor, meat_evaluate, meat_assess, meat_treat, meat_score, confidence_score
        FROM hcc_audit_trail
        WHERE provider_id = {ph} AND encounter_date >= {ph}
        ORDER BY encounter_date DESC
        """
        return self.execute_query(query, (provider_id, cutoff_str), fetch="all")

    def get_provider_info(self, provider_id: str) -> Optional[Dict]:
        """Get provider metadata"""
        ph = '%s' if self.db_type == 'postgresql' else '?'
        return self.execute_query(f"SELECT provider_id, provider_name, specialty, npi FROM provider_meat_scores WHERE provider_id = {ph}", (provider_id,), fetch="one")

    def seed_demo_data(self):
        """Populate database with realistic demo data (50 providers, varying compliance)"""
        import random
        try:
            from faker import Faker
        except ImportError:
            Faker = None

        fake = Faker() if Faker else None
        specialties = ['Primary Care', 'Cardiology', 'Endocrinology', 'Nephrology', 'Pulmonology', 'Rheumatology']
        hcc_categories = [
            ('HCC 36', 'Diabetes with Chronic Complications', 'Diabetes with Complications', 0.318),
            ('HCC 226', 'Congestive Heart Failure', 'Congestive Heart Failure', 0.368),
            ('HCC 280', 'Chronic Obstructive Pulmonary Disease', 'COPD', 0.328),
            ('HCC 327', 'Chronic Kidney Disease Stage 4', 'Chronic Kidney Disease', 0.237),
            ('HCC 155', 'Major Depressive Disorder', 'Major Depressive Disorder', 0.309),
            ('HCC 264', 'Peripheral Vascular Disease', 'Vascular Disease/PVD', 0.288),
            ('HCC 22', 'Morbid Obesity', 'Morbid Obesity', 0.252),
            ('HCC 238', 'Atrial Fibrillation', 'Specified Heart Arrhythmias', 0.252),
            ('HCC 92', 'Rheumatoid Arthritis', 'Rheumatoid Arthritis', 0.299),
            ('HCC 18', 'Lung Cancer', 'Active Cancers', 2.691)
        ]
        failure_reasons = [
            'Missing Monitor element', 'Missing Treat element', 'Problem List Only',
            'No link between conditions', 'History of vs Active', 'Missing Evaluate element',
            'Unspecified diagnosis', 'Inferred diagnosis'
        ]
        passing_docs = [
            "CHF: Patient reports increased dyspnea. Reviewed BNP (350) and Echo (EF 40%). Chronic systolic CHF stable. Continue Lasix 40mg daily.",
            "Type 2 DM with CKD: A1c reviewed at 8.2%. Discussed stage 3 CKD. Metformin 1000mg BID continued, nephrology referral ordered.",
            "COPD: Using albuterol 2-3x daily. Spirometry FEV1 55%. Discussed smoking cessation. Added Advair 250/50 BID.",
        ]
        failing_docs = ["CHF - stable", "Diabetes, CKD", "Problem List: CHF, COPD, DM", "History of lung cancer"]

        ph = '%s' if self.db_type == 'postgresql' else '?'
        for i in range(50):
            provider_id = f"PRV{i+1:04d}"
            provider_name = f"Dr. {fake.last_name()}, {fake.first_name()}" if fake else f"Dr. Provider{i+1}"
            specialty = random.choice(specialties)
            npi = str(random.randint(1000000000, 9999999999))

            self.execute_query(
                f"INSERT OR IGNORE INTO provider_meat_scores (provider_id, provider_name, specialty, npi) VALUES ({ph}, {ph}, {ph}, {ph})"
                if self.db_type == 'sqlite' else
                f"INSERT INTO provider_meat_scores (provider_id, provider_name, specialty, npi) VALUES ({ph}, {ph}, {ph}, {ph}) ON CONFLICT (provider_id) DO NOTHING",
                (provider_id, provider_name, specialty, npi), fetch="none"
            )

            quality_roll = random.random()
            pass_rate = random.uniform(0.90, 0.98) if quality_roll < 0.3 else (random.uniform(0.80, 0.90) if quality_roll < 0.7 else random.uniform(0.60, 0.80))
            num_audits = random.randint(50, 200)

            for j in range(num_audits):
                patient_id = f"PAT{random.randint(10000, 99999)}"
                encounter_date = (datetime.now() - timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d')
                encounter_id = f"ENC{random.randint(100000, 999999)}"
                hcc_code, hcc_desc, hcc_cat, raf_weight = random.choice(hcc_categories)
                passes = random.random() < pass_rate

                if passes:
                    doc_text = random.choice(passing_docs)
                    meat_elements = [True] * 4
                    validation_status, failure_reason = 'PASS', None
                    confidence = random.uniform(85, 99)
                else:
                    doc_text = random.choice(failing_docs)
                    meat_elements = [random.random() < 0.3 for _ in range(4)]
                    if not any(meat_elements):
                        meat_elements[0] = True
                    validation_status, failure_reason = 'FAIL', random.choice(failure_reasons)
                    confidence = random.uniform(70, 90)

                meat_score = sum(meat_elements)
                audit_data = {
                    'provider_id': provider_id, 'patient_id': patient_id, 'encounter_date': encounter_date,
                    'encounter_id': encounter_id, 'hcc_code': hcc_code, 'hcc_description': hcc_desc,
                    'hcc_category': hcc_cat, 'raf_weight': raf_weight,
                    'meat_monitor': meat_elements[0], 'meat_monitor_evidence': doc_text if meat_elements[0] else None,
                    'meat_evaluate': meat_elements[1], 'meat_evaluate_evidence': doc_text if meat_elements[1] else None,
                    'meat_assess': meat_elements[2], 'meat_assess_evidence': doc_text if meat_elements[2] else None,
                    'meat_treat': meat_elements[3], 'meat_treat_evidence': doc_text if meat_elements[3] else None,
                    'meat_score': meat_score, 'validation_status': validation_status, 'failure_reason': failure_reason,
                    'documentation_text': doc_text, 'confidence_score': confidence, 'ai_model_version': 'claude-sonnet-4'
                }
                self.insert_hcc_audit(audit_data)

            self.update_provider_scores(provider_id, 12)
            if (i + 1) % 10 == 0:
                print(f"Created provider {i+1}/50")

        print("Demo data seeding complete!")

    def cleanup_all_data(self):
        """Clear all tables (for testing)"""
        for table in ['provider_education', 'failure_patterns', 'hcc_audit_trail', 'provider_meat_scores']:
            self.execute_query(f"DELETE FROM {table}", fetch="none")
        print("All data cleared")


def get_db_manager() -> DatabaseManager:
    """Factory function to get DatabaseManager with proper configuration"""
    db_type = os.getenv("DB_TYPE", "sqlite")

    if db_type == "postgresql" and not os.getenv("DATABASE_URL"):
        db_type = "sqlite"

    if db_type == "sqlite":
        connection_string = os.getenv("SQLITE_PATH", os.path.join(os.path.dirname(__file__), "auditshield.db"))
    else:
        connection_string = os.getenv("DATABASE_URL")

    db = DatabaseManager(db_type=db_type, connection_string=connection_string)
    db.initialize_schema()
    return db


if __name__ == "__main__":
    import sys
    db = get_db_manager()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "init":
            print("Schema initialized!")
        elif cmd == "seed":
            db.seed_demo_data()
        elif cmd == "clean":
            confirm = input("Delete all data? (yes/no): ")
            if confirm.lower() == "yes":
                db.cleanup_all_data()
        elif cmd == "test":
            scores = db.get_provider_scores(lookback_months=12)
            print(f"Providers: {len(scores)}")
            if len(scores) > 0:
                pid = scores.iloc[0]['provider_id']
                print(f"Failure patterns: {len(db.get_provider_failure_patterns(pid, 12))}")
                print("M.E.A.T. breakdown:", db.get_meat_element_breakdown(pid, 12).to_dict())
        else:
            print("Usage: python database.py [init|seed|clean|test]")
    else:
        print("Usage: python database.py [init|seed|clean|test]")
