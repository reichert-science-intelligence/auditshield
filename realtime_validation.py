"""
Real-time validation engine for Phase 3 proactive intelligence
Processes encounters as they're documented with live M.E.A.T. validation
"""
import json
import threading
import time
from typing import Dict, List, Optional
from datetime import datetime

from app_config import get_anthropic_client
from database import get_db_manager
from meat_validator import MEATValidator


class RealtimeValidationEngine:
    """
    Real-time validation engine that processes encounters as they're documented

    Features:
    1. Live M.E.A.T. validation during documentation
    2. Smart prompts for missing elements
    3. Auto-alerts for high-risk patterns
    4. Provider feedback loops
    """

    def __init__(self):
        self.db = get_db_manager()
        self.validator = MEATValidator()
        self.client = get_anthropic_client()

        # Validation thresholds
        self.auto_alert_threshold = 70  # Confidence below this triggers alert
        self.high_priority_hccs = [
            "HCC 36",
            "HCC 37",
            "HCC 38",  # Diabetes with complications
            "HCC 226",  # CHF
            "HCC 280",  # COPD
            "HCC 327",
            "HCC 328",
            "HCC 329",  # CKD
            "HCC 17",
            "HCC 18",
            "HCC 19",  # Active cancers
        ]

    def queue_encounter_for_validation(
        self,
        encounter_id: str,
        patient_id: str,
        provider_id: str,
        encounter_date: str,
        hcc_codes: List[str],
        documentation_text: str,
    ) -> int:
        """
        Add encounter to validation queue

        Returns: queue_id
        """
        # Determine priority
        is_high_priority = any(hcc in self.high_priority_hccs for hcc in hcc_codes)
        priority = "HIGH" if is_high_priority else "NORMAL"

        param_placeholder = "%s" if self.db.db_type == "postgresql" else "?"

        # Handle HCC array for SQLite (store as JSON)
        hcc_codes_param = hcc_codes
        if self.db.db_type == "sqlite":
            hcc_codes_param = json.dumps(hcc_codes)

        query = f"""
        INSERT INTO realtime_validation_queue (
            encounter_id, patient_id, provider_id, encounter_date,
            hcc_codes, documentation_text, validation_priority
        ) VALUES (
            {param_placeholder}, {param_placeholder}, {param_placeholder}, {param_placeholder},
            {param_placeholder}, {param_placeholder}, {param_placeholder}
        )
        """

        if self.db.db_type == "postgresql":
            query += " RETURNING queue_id"
            result = self.db.execute_query(
                query,
                (
                    encounter_id,
                    patient_id,
                    provider_id,
                    encounter_date,
                    hcc_codes_param,
                    documentation_text,
                    priority,
                ),
                fetch="one",
            )
            queue_id = result["queue_id"]
        else:
            self.db.execute_query(
                query,
                (
                    encounter_id,
                    patient_id,
                    provider_id,
                    encounter_date,
                    hcc_codes_param,
                    documentation_text,
                    priority,
                ),
                fetch="none",
            )
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT last_insert_rowid()")
                queue_id = cursor.fetchone()[0]

        # Trigger background validation (thread-safe, works without event loop)
        thread = threading.Thread(
            target=self._process_validation,
            args=(queue_id,),
            daemon=True,
        )
        thread.start()

        return queue_id

    def _process_validation(self, queue_id: int):
        """Background validation processing (runs in thread)"""
        param_placeholder = "%s" if self.db.db_type == "postgresql" else "?"

        # Get queue item
        query = f"""
        SELECT *
        FROM realtime_validation_queue
        WHERE queue_id = {param_placeholder}
        """

        item = self.db.execute_query(query, (queue_id,), fetch="one")

        if not item:
            return

        # Parse HCC codes
        hcc_codes = item["hcc_codes"]
        if self.db.db_type == "sqlite" and isinstance(hcc_codes, str):
            hcc_codes = json.loads(hcc_codes) if hcc_codes else []
        elif not hcc_codes:
            hcc_codes = []

        # Validate each HCC
        validation_results = []
        auto_alerts = []

        for hcc_code in hcc_codes:
            result = self.validator.validate_hcc_documentation(
                hcc_code=hcc_code,
                diagnosis=hcc_code,
                documentation=item["documentation_text"],
                encounter_date=str(item["encounter_date"]),
            )

            validation_results.append(result)

            # Generate alerts if needed
            if result.get("confidence_score", 100) < self.auto_alert_threshold:
                alert = self._generate_validation_alert(
                    hcc_code=hcc_code,
                    result=result,
                    provider_id=item["provider_id"],
                )
                auto_alerts.append(alert)

        # Update queue with results
        results_param = validation_results
        alerts_param = auto_alerts

        if self.db.db_type == "sqlite":
            results_param = json.dumps(validation_results)
            alerts_param = json.dumps(auto_alerts)

        ts_expr = (
            "CURRENT_TIMESTAMP"
            if self.db.db_type == "postgresql"
            else "DATETIME('now')"
        )
        update_query = f"""
        UPDATE realtime_validation_queue
        SET queue_status = 'PROCESSED',
            processed_at = {ts_expr},
            validation_results = {param_placeholder},
            auto_alerts = {param_placeholder}
        WHERE queue_id = {param_placeholder}
        """

        self.db.execute_query(
            update_query, (results_param, alerts_param, queue_id), fetch="none"
        )

        # Create automated alerts
        for alert in auto_alerts:
            self._create_alert(
                alert_type="VALIDATION_FAILURE",
                severity="HIGH"
                if item["validation_priority"] == "HIGH"
                else "MEDIUM",
                title=alert["title"],
                message=alert["message"],
                triggered_by=item["provider_id"],
                related_entity_type="ENCOUNTER",
                related_entity_id=item["encounter_id"],
            )

    def _generate_validation_alert(
        self, hcc_code: str, result: Dict, provider_id: str
    ) -> Dict:
        """Generate actionable alert for failed validation"""
        meat_elements = result.get("meat_elements", {})
        missing_elements = []
        for element in ["monitor", "evaluate", "assess", "treat"]:
            elem_data = meat_elements.get(element, {})
            if not elem_data.get("present"):
                missing_elements.append(element.upper())

        return {
            "title": f"Documentation Gap Detected: {hcc_code}",
            "message": f"Missing M.E.A.T. elements: {', '.join(missing_elements)}. {result.get('recommendations', '')}",
            "hcc_code": hcc_code,
            "provider_id": provider_id,
            "severity": "HIGH" if hcc_code in self.high_priority_hccs else "MEDIUM",
        }

    def _create_alert(
        self,
        alert_type: str,
        severity: str,
        title: str,
        message: str,
        triggered_by: str,
        related_entity_type: str,
        related_entity_id: str,
    ):
        """Create automated alert in database"""
        param_placeholder = "%s" if self.db.db_type == "postgresql" else "?"

        query = f"""
        INSERT INTO automated_alerts (
            alert_type, severity, title, message, triggered_by,
            related_entity_type, related_entity_id, action_required
        ) VALUES (
            {param_placeholder}, {param_placeholder}, {param_placeholder}, {param_placeholder},
            {param_placeholder}, {param_placeholder}, {param_placeholder}, TRUE
        )
        """

        self.db.execute_query(
            query,
            (
                alert_type,
                severity,
                title,
                message,
                triggered_by,
                related_entity_type,
                related_entity_id,
            ),
            fetch="none",
        )

    def get_provider_live_feedback(self, provider_id: str) -> Dict:
        """
        Get real-time feedback for provider during documentation session

        Returns actionable guidance
        """
        param_placeholder = "%s" if self.db.db_type == "postgresql" else "?"

        # PostgreSQL vs SQLite time interval
        time_filter = (
            "processed_at >= CURRENT_TIMESTAMP - INTERVAL '1 hour'"
            if self.db.db_type == "postgresql"
            else "processed_at >= DATETIME('now', '-1 hour')"
        )

        query = f"""
        SELECT
            queue_id,
            encounter_id,
            hcc_codes,
            validation_results,
            auto_alerts,
            processed_at
        FROM realtime_validation_queue
        WHERE provider_id = {param_placeholder}
        AND queue_status = 'PROCESSED'
        AND {time_filter}
        ORDER BY processed_at DESC
        LIMIT 10
        """

        recent_validations = self.db.execute_query(query, (provider_id,), fetch="all")

        if not recent_validations:
            return {
                "status": "NO_RECENT_ACTIVITY",
                "message": "No recent documentation to review",
            }

        # Parse results
        total_hccs = 0
        failed_hccs = 0
        common_gaps = {"monitor": 0, "evaluate": 0, "assess": 0, "treat": 0}

        for validation in recent_validations:
            results = validation["validation_results"]
            if self.db.db_type == "sqlite" and isinstance(results, str):
                results = json.loads(results) if results else []
            elif not results:
                results = []

            for result in results:
                total_hccs += 1
                if result.get("validation_status") == "FAIL":
                    failed_hccs += 1

                    # Track which elements are missing
                    for element, data in result.get("meat_elements", {}).items():
                        if not data.get("present"):
                            common_gaps[element] = common_gaps.get(element, 0) + 1

        # Generate feedback
        current_rate = (
            (total_hccs - failed_hccs) / total_hccs * 100 if total_hccs > 0 else 100
        )
        most_common_gap = (
            max(common_gaps.items(), key=lambda x: x[1])[0]
            if common_gaps
            else "treat"
        )

        feedback = {
            "current_session_rate": round(current_rate, 1),
            "hccs_documented": total_hccs,
            "hccs_failed": failed_hccs,
            "most_common_gap": most_common_gap.upper(),
            "gap_frequency": common_gaps,
            "recommendation": self._generate_live_recommendation(
                current_rate, most_common_gap
            ),
        }

        return feedback

    def _generate_live_recommendation(
        self, current_rate: float, most_common_gap: str
    ) -> str:
        """Generate actionable recommendation for provider"""
        if current_rate >= 95:
            return "Excellent documentation! Keep it up."
        elif current_rate >= 85:
            return f"Good work, but watch your {most_common_gap.upper()} elements. Add specific details."
        else:
            return f"Documentation needs improvement. Focus on {most_common_gap.upper()} - be specific about current management."

    def get_validation_dashboard_metrics(self) -> Dict:
        """Get real-time metrics for validation dashboard"""
        # Last 24 hours metrics
        time_filter = (
            "queued_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours'"
            if self.db.db_type == "postgresql"
            else "queued_at >= DATETIME('now', '-24 hours')"
        )

        query = f"""
        SELECT
            COUNT(*) as total_validated,
            AVG(CASE WHEN queue_status = 'PROCESSED' THEN 1.0 ELSE 0.0 END) as processing_rate
        FROM realtime_validation_queue
        WHERE {time_filter}
        """

        metrics = self.db.execute_query(query, fetch="one")

        # Alert counts
        alert_time_filter = (
            "triggered_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours'"
            if self.db.db_type == "postgresql"
            else "triggered_at >= DATETIME('now', '-24 hours')"
        )

        alert_query = f"""
        SELECT severity, COUNT(*) as count
        FROM automated_alerts
        WHERE {alert_time_filter}
        AND dismissed = FALSE
        GROUP BY severity
        """

        alerts = self.db.execute_query(alert_query, fetch="all")
        alert_breakdown = {row["severity"]: row["count"] for row in alerts} if alerts else {}

        return {
            "total_validated_24h": metrics["total_validated"] if metrics else 0,
            "processing_rate": round(
                (metrics["processing_rate"] or 0) * 100, 1
            )
            if metrics
            else 0,
            "active_alerts": alert_breakdown,
            "total_alerts": sum(alert_breakdown.values()),
        }


# ==================== DEMO/TEST ====================

if __name__ == "__main__":
    engine = RealtimeValidationEngine()

    # Simulate real-time validation
    queue_id = engine.queue_encounter_for_validation(
        encounter_id="ENC001",
        patient_id="PAT001",
        provider_id="PRV0001",
        encounter_date="2026-02-26",
        hcc_codes=["HCC 226", "HCC 280"],
        documentation_text="CHF stable. COPD managed with inhalers.",
    )

    print(f"Queued for validation: {queue_id}")

    # Wait for background validation to complete (API call takes ~5-15 sec)
    print("Processing validation (waiting 20s for API)...")
    time.sleep(20)

    # Get provider feedback
    feedback = engine.get_provider_live_feedback("PRV0001")
    print("\nProvider Feedback:")
    print(json.dumps(feedback, indent=2))

    # Get dashboard metrics
    metrics = engine.get_validation_dashboard_metrics()
    print("\nDashboard Metrics:")
    print(json.dumps(metrics, indent=2))
