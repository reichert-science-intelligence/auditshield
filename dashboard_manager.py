"""
Dashboard Manager - Role-based dashboard configurations
Executive, Compliance, Provider, and Coder views
"""
import json

from database import get_db_manager


class DashboardManager:
    """
    Role-based dashboard configurations

    Different views for:
    - Executives (high-level metrics)
    - Compliance Teams (operational details)
    - Providers (personal performance)
    - Coders (validation queue)
    """

    def __init__(self):
        self.db = get_db_manager()

    def create_dashboard_config(
        self,
        dashboard_name: str,
        user_role: str,
        widget_layout: dict,
        filter_defaults: dict,
    ) -> int:
        """Create or update dashboard configuration"""
        param_placeholder = "%s" if self.db.db_type == "postgresql" else "?"

        widget_layout_param = json.dumps(widget_layout)
        filter_defaults_param = json.dumps(filter_defaults)

        query = f"""
        INSERT INTO dashboard_configs (
            dashboard_name, user_role, widget_layout, filter_defaults
        ) VALUES (
            {param_placeholder}, {param_placeholder}, {param_placeholder}, {param_placeholder}
        )
        """

        params = (dashboard_name, user_role, widget_layout_param, filter_defaults_param)

        if self.db.db_type == "postgresql":
            query += " RETURNING config_id"
            result = self.db.execute_query(query, params, fetch="one")
            return result["config_id"]
        else:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                cursor.execute("SELECT last_insert_rowid()")
                config_id = cursor.fetchone()[0]
                conn.commit()
                return config_id

    def get_executive_dashboard_data(self) -> dict:
        """Get high-level metrics for executive dashboard"""
        from compliance_forecasting import ComplianceForecaster
        from financial_calculator import FinancialImpactCalculator

        calc = FinancialImpactCalculator()
        forecaster = ComplianceForecaster()

        exposure = calc.calculate_current_exposure(lookback_months=12)

        forecast = forecaster.get_forecast_dashboard()

        risk_query = """
        SELECT
            risk_tier,
            COUNT(*) as provider_count,
            SUM(financial_risk_estimate) as total_risk
        FROM provider_meat_scores
        GROUP BY risk_tier
        """
        risk_dist = self.db.execute_query(risk_query, fetch="all")
        risk_breakdown = {row["risk_tier"]: row for row in risk_dist} if risk_dist else {}

        audit_query = """
        SELECT COUNT(*) as count
        FROM radv_audits
        WHERE audit_status = 'ACTIVE'
        """
        audits = self.db.execute_query(audit_query, fetch="one")

        return {
            "financial_exposure": {
                "current": exposure.get("current_exposure", 0),
                "annualized": exposure.get("annualized_exposure", 0),
                "validation_rate": exposure.get("current_validation_rate", 0),
            },
            "compliance_forecast": forecast,
            "provider_risk_distribution": risk_breakdown,
            "active_audits": audits.get("count", 0) if audits else 0,
            "dashboard_type": "EXECUTIVE",
        }

    def get_compliance_dashboard_data(self) -> dict:
        """Get operational metrics for compliance teams"""
        from hcc_reconciliation import HCCReconciliation
        from realtime_validation import RealtimeValidationEngine

        validation_engine = RealtimeValidationEngine()
        reconciler = HCCReconciliation()

        validation_metrics = validation_engine.get_validation_dashboard_metrics()
        reconciliation_metrics = reconciler.get_reconciliation_dashboard()

        time_filter = (
            "scheduled_date >= CURRENT_DATE - INTERVAL '30 days'"
            if self.db.db_type == "postgresql"
            else "scheduled_date >= DATE('now', '-30 days')"
        )
        edu_query = f"""
        SELECT
            session_status,
            COUNT(*) as count
        FROM education_sessions
        WHERE {time_filter}
        GROUP BY session_status
        """
        edu_stats = self.db.execute_query(edu_query, fetch="all")
        edu_breakdown = (
            {row["session_status"]: row["count"] for row in edu_stats}
            if edu_stats
            else {}
        )

        alert_query = """
        SELECT
            severity,
            COUNT(*) as count
        FROM automated_alerts
        WHERE dismissed = FALSE
        AND action_required = TRUE
        GROUP BY severity
        """
        alerts = self.db.execute_query(alert_query, fetch="all")
        alert_breakdown = (
            {row["severity"]: row["count"] for row in alerts} if alerts else {}
        )

        return {
            "validation_metrics": validation_metrics,
            "reconciliation_opportunities": reconciliation_metrics,
            "education_status": edu_breakdown,
            "pending_alerts": alert_breakdown,
            "dashboard_type": "COMPLIANCE",
        }

    def get_provider_dashboard_data(self, provider_id: str) -> dict:
        """Get personal performance metrics for individual provider"""
        from realtime_validation import RealtimeValidationEngine

        validation_engine = RealtimeValidationEngine()
        feedback = validation_engine.get_provider_live_feedback(provider_id)

        param_placeholder = "%s" if self.db.db_type == "postgresql" else "?"
        score_query = f"""
        SELECT *
        FROM provider_meat_scores
        WHERE provider_id = {param_placeholder}
        """
        scores = self.db.execute_query(score_query, (provider_id,), fetch="one")

        time_filter = (
            "encounter_date >= CURRENT_DATE - INTERVAL '30 days'"
            if self.db.db_type == "postgresql"
            else "encounter_date >= DATE('now', '-30 days')"
        )
        trend_query = f"""
        SELECT
            DATE(encounter_date) as date,
            COUNT(*) as total,
            SUM(CASE WHEN validation_status = 'PASS' THEN 1 ELSE 0 END) as passed
        FROM hcc_audit_trail
        WHERE provider_id = {param_placeholder}
        AND {time_filter}
        GROUP BY DATE(encounter_date)
        ORDER BY date DESC
        LIMIT 30
        """
        trends = self.db.execute_query(trend_query, (provider_id,), fetch="all")

        edu_query = f"""
        SELECT *
        FROM education_sessions
        WHERE provider_id = {param_placeholder}
        ORDER BY scheduled_date DESC
        LIMIT 5
        """
        education = self.db.execute_query(edu_query, (provider_id,), fetch="all")

        return {
            "live_feedback": feedback,
            "overall_scores": scores,
            "trend_data": trends,
            "education_history": education,
            "dashboard_type": "PROVIDER",
        }

    def create_standard_dashboards(self) -> list[dict]:
        """Create standard dashboard configurations"""
        dashboards = [
            {
                "dashboard_name": "Executive Summary",
                "user_role": "EXECUTIVE",
                "widget_layout": {
                    "widgets": [
                        {
                            "type": "financial_exposure_card",
                            "position": {"row": 1, "col": 1},
                        },
                        {
                            "type": "compliance_forecast_chart",
                            "position": {"row": 1, "col": 2},
                        },
                        {
                            "type": "provider_risk_distribution",
                            "position": {"row": 2, "col": 1},
                        },
                        {
                            "type": "active_audits_status",
                            "position": {"row": 2, "col": 2},
                        },
                    ]
                },
                "filter_defaults": {"lookback_months": 12},
            },
            {
                "dashboard_name": "Compliance Operations",
                "user_role": "COMPLIANCE",
                "widget_layout": {
                    "widgets": [
                        {
                            "type": "realtime_validation_queue",
                            "position": {"row": 1, "col": 1},
                        },
                        {
                            "type": "reconciliation_opportunities",
                            "position": {"row": 1, "col": 2},
                        },
                        {
                            "type": "education_tracker",
                            "position": {"row": 2, "col": 1},
                        },
                        {
                            "type": "alert_center",
                            "position": {"row": 2, "col": 2},
                        },
                    ]
                },
                "filter_defaults": {"lookback_days": 30},
            },
            {
                "dashboard_name": "Provider Performance",
                "user_role": "PROVIDER",
                "widget_layout": {
                    "widgets": [
                        {
                            "type": "live_session_feedback",
                            "position": {"row": 1, "col": 1},
                        },
                        {
                            "type": "personal_validation_rate",
                            "position": {"row": 1, "col": 2},
                        },
                        {
                            "type": "trend_chart_30d",
                            "position": {"row": 2, "col": 1},
                        },
                        {
                            "type": "education_recommendations",
                            "position": {"row": 2, "col": 2},
                        },
                    ]
                },
                "filter_defaults": {"show_peers": False},
            },
        ]

        created = []
        for dash in dashboards:
            try:
                config_id = self.create_dashboard_config(**dash)
                created.append(
                    {"config_id": config_id, "dashboard_name": dash["dashboard_name"]}
                )
            except Exception as e:
                created.append(
                    {
                        "config_id": None,
                        "dashboard_name": dash["dashboard_name"],
                        "error": str(e),
                    }
                )

        return created


if __name__ == "__main__":
    manager = DashboardManager()

    print("Creating standard dashboards...")
    dashboards = manager.create_standard_dashboards()

    print(f"\nCreated {len(dashboards)} dashboards:")
    for dash in dashboards:
        status = (
            f"config_id={dash['config_id']}"
            if dash.get("config_id")
            else f"error: {dash.get('error', 'unknown')}"
        )
        print(f"   - {dash['dashboard_name']} ({status})")

    print("\nTesting dashboard data retrieval...")
    exec_data = manager.get_executive_dashboard_data()
    print(f"   Executive dashboard: {exec_data['dashboard_type']}")
    print(
        f"   Financial exposure: ${exec_data['financial_exposure']['current']:,.0f}"
    )
