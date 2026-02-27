"""
HCC Reconciliation - Two-way ADD/DELETE recommendations
Proactively identify missing HCCs and unsupported HCCs before CMS discovers them
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from database import get_db_manager
from meat_validator import MEATValidator


class HCCReconciliation:
    """
    Two-way HCC reconciliation: identifies both missing HCCs (ADD) and
    unsupported HCCs (DELETE) before CMS discovers them

    This is critical for RADV defense - proactively removing bad codes
    """

    def __init__(self):
        self.db = get_db_manager()
        self.validator = MEATValidator()
        self.cms_base_rate = 1142.50

    def run_comprehensive_reconciliation(
        self,
        lookback_months: int = 12,
        min_confidence: float = 85.0,
    ) -> Dict:
        """
        Scan entire patient population for HCC reconciliation opportunities

        Returns both ADD and DELETE recommendations
        """
        add_recommendations = self._find_missing_hccs(lookback_months, min_confidence)
        delete_recommendations = self._find_unsupported_hccs(
            lookback_months, min_confidence
        )

        # Calculate financial impact
        add_value = sum(r["financial_impact"] for r in add_recommendations)
        delete_risk = sum(r["financial_impact"] for r in delete_recommendations)
        net_impact = add_value - delete_risk

        return {
            "add_recommendations": add_recommendations,
            "delete_recommendations": delete_recommendations,
            "summary": {
                "total_add_opportunities": len(add_recommendations),
                "total_delete_required": len(delete_recommendations),
                "add_financial_value": round(add_value, 2),
                "delete_financial_risk": round(delete_risk, 2),
                "net_financial_impact": round(net_impact, 2),
            },
        }

    def _find_missing_hccs(
        self, lookback_months: int, min_confidence: float
    ) -> List[Dict]:
        """
        Find HCCs that should be captured but are missing

        Logic:
        - Patient has documented condition in notes
        - Corresponding HCC not coded
        - Documentation supports the HCC
        """
        # Common missed HCC patterns
        missing_patterns = {
            "HCC 36": [
                "type 2 diabetes",
                "diabetic neuropathy",
                "diabetic nephropathy",
            ],
            "HCC 226": ["systolic heart failure", "diastolic heart failure", "CHF"],
            "HCC 280": ["chronic bronchitis", "emphysema", "COPD"],
            "HCC 327": ["chronic kidney disease stage 4", "CKD stage 4"],
            "HCC 155": ["major depressive disorder", "MDD", "recurrent depression"],
        }

        recommendations = []

        param_placeholder = "%s" if self.db.db_type == "postgresql" else "?"
        cutoff_date = (
            datetime.now() - timedelta(days=lookback_months * 30)
        ).strftime("%Y-%m-%d")

        # Find encounters with documentation mentioning conditions but HCC not coded
        query = f"""
        SELECT DISTINCT
            patient_id,
            encounter_id,
            encounter_date,
            documentation_text,
            provider_id
        FROM hcc_audit_trail
        WHERE encounter_date >= {param_placeholder}
        AND documentation_text IS NOT NULL
        LIMIT 100
        """

        encounters = self.db.execute_query(query, (cutoff_date,), fetch="all")

        for encounter in encounters:
            doc_text = (encounter.get("documentation_text") or "").lower()

            # Check for missing HCCs
            for hcc_code, keywords in missing_patterns.items():
                if any(keyword.lower() in doc_text for keyword in keywords):
                    check_query = f"""
                    SELECT COUNT(*) as count
                    FROM hcc_audit_trail
                    WHERE patient_id = {param_placeholder}
                    AND hcc_code = {param_placeholder}
                    AND encounter_date >= {param_placeholder}
                    """

                    exists = self.db.execute_query(
                        check_query,
                        (
                            encounter["patient_id"],
                            hcc_code,
                            cutoff_date,
                        ),
                        fetch="one",
                    )

                    if exists and (exists.get("count") or 0) == 0:
                        validation = self.validator.validate_hcc_documentation(
                            hcc_code=hcc_code,
                            diagnosis=f"Suspected {hcc_code}",
                            documentation=encounter["documentation_text"],
                            encounter_date=str(encounter["encounter_date"]),
                        )

                        if (
                            validation.get("confidence_score", 0) >= min_confidence
                            and validation.get("validation_status") == "PASS"
                        ):
                            raf_weight = self._get_raf_weight(hcc_code)
                            financial_impact = raf_weight * self.cms_base_rate

                            hcc_desc = self.validator._categorize_hcc(
                                hcc_code, ""
                            )

                            recommendation = {
                                "patient_id": encounter["patient_id"],
                                "encounter_id": encounter.get("encounter_id"),
                                "hcc_code": hcc_code,
                                "hcc_description": hcc_desc,
                                "supporting_evidence": (
                                    (encounter.get("documentation_text") or "")[:200]
                                    + "..."
                                ),
                                "confidence_score": validation["confidence_score"],
                                "financial_impact": round(financial_impact, 2),
                                "provider_id": encounter.get("provider_id"),
                            }

                            recommendations.append(recommendation)

                            self._save_reconciliation_record(
                                reconciliation_type="ADD",
                                **recommendation,
                            )

        return recommendations

    def _find_unsupported_hccs(
        self, lookback_months: int, min_confidence: float
    ) -> List[Dict]:
        """
        Find HCCs that are currently coded but lack documentation support

        These are RADV audit failures waiting to happen - delete them proactively
        """
        param_placeholder = "%s" if self.db.db_type == "postgresql" else "?"
        cutoff_date = (
            datetime.now() - timedelta(days=lookback_months * 30)
        ).strftime("%Y-%m-%d")

        # Find failed validations (include NULL confidence as potentially unsupported)
        query = f"""
        SELECT
            patient_id,
            encounter_id,
            hcc_code,
            hcc_description,
            raf_weight,
            documentation_text,
            failure_reason,
            confidence_score,
            provider_id
        FROM hcc_audit_trail
        WHERE validation_status = 'FAIL'
        AND encounter_date >= {param_placeholder}
        AND (confidence_score < {param_placeholder} OR confidence_score IS NULL)
        ORDER BY raf_weight DESC
        """

        unsupported = self.db.execute_query(
            query,
            (cutoff_date, min_confidence),
            fetch="all",
        )

        recommendations = []

        for hcc in unsupported:
            raf_weight = hcc.get("raf_weight") or 0
            financial_impact = raf_weight * self.cms_base_rate

            recommendation = {
                "patient_id": hcc["patient_id"],
                "encounter_id": hcc.get("encounter_id"),
                "hcc_code": hcc["hcc_code"],
                "hcc_description": hcc.get("hcc_description", ""),
                "supporting_evidence": f"FAIL: {hcc.get('failure_reason', 'Insufficient documentation')}",
                "confidence_score": hcc.get("confidence_score") or 0,
                "financial_impact": round(financial_impact, 2),
                "provider_id": hcc.get("provider_id"),
            }

            recommendations.append(recommendation)

            self._save_reconciliation_record(
                reconciliation_type="DELETE",
                **recommendation,
            )

        return recommendations

    def _save_reconciliation_record(
        self,
        reconciliation_type: str,
        patient_id: str,
        encounter_id: Optional[str],
        hcc_code: str,
        hcc_description: str,
        supporting_evidence: str,
        confidence_score: float,
        financial_impact: float,
        provider_id: Optional[str] = None,
    ):
        """Save reconciliation recommendation to database"""
        param_placeholder = "%s" if self.db.db_type == "postgresql" else "?"

        recommended_action = (
            "ADD_HCC" if reconciliation_type == "ADD" else "DELETE_HCC"
        )

        query = f"""
        INSERT INTO hcc_reconciliation (
            patient_id, encounter_id, reconciliation_type, hcc_code,
            hcc_description, recommended_action, supporting_evidence,
            confidence_score, financial_impact
        ) VALUES (
            {param_placeholder}, {param_placeholder}, {param_placeholder}, {param_placeholder},
            {param_placeholder}, {param_placeholder}, {param_placeholder},
            {param_placeholder}, {param_placeholder}
        )
        """

        self.db.execute_query(
            query,
            (
                patient_id,
                encounter_id,
                reconciliation_type,
                hcc_code,
                hcc_description,
                recommended_action,
                supporting_evidence,
                confidence_score,
                financial_impact,
            ),
            fetch="none",
        )

    def _get_raf_weight(self, hcc_code: str) -> float:
        """Get RAF weight for HCC (simplified - would query actual RAF table)"""
        raf_weights = {
            "HCC 36": 0.318,
            "HCC 37": 0.318,
            "HCC 38": 0.318,
            "HCC 226": 0.368,
            "HCC 280": 0.328,
            "HCC 327": 0.237,
            "HCC 328": 0.237,
            "HCC 329": 0.237,
            "HCC 155": 0.309,
            "HCC 264": 0.288,
            "HCC 22": 0.252,
            "HCC 238": 0.252,
            "HCC 92": 0.299,
            "HCC 18": 2.691,
        }
        return raf_weights.get(hcc_code, 0.20)

    def get_reconciliation_dashboard(self) -> Dict:
        """Get reconciliation metrics for dashboard"""
        time_filter = (
            "created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'"
            if self.db.db_type == "postgresql"
            else "created_at >= DATETIME('now', '-30 days')"
        )

        summary_query = f"""
        SELECT
            reconciliation_type,
            COUNT(*) as count,
            SUM(financial_impact) as total_impact,
            SUM(CASE WHEN action_taken THEN 1 ELSE 0 END) as actions_taken
        FROM hcc_reconciliation
        WHERE {time_filter}
        GROUP BY reconciliation_type
        """

        summary = self.db.execute_query(summary_query, fetch="all")

        metrics = {
            "ADD": {"count": 0, "total_impact": 0, "actions_taken": 0},
            "DELETE": {"count": 0, "total_impact": 0, "actions_taken": 0},
        }

        for row in summary:
            rtype = row.get("reconciliation_type", "ADD")
            if rtype in metrics:
                metrics[rtype] = {
                    "count": row["count"],
                    "total_impact": round((row["total_impact"] or 0), 2),
                    "actions_taken": row["actions_taken"] or 0,
                }

        total_count = metrics["ADD"]["count"] + metrics["DELETE"]["count"]
        total_actions = metrics["ADD"]["actions_taken"] + metrics["DELETE"]["actions_taken"]

        return {
            "add_opportunities": metrics["ADD"],
            "delete_requirements": metrics["DELETE"],
            "net_financial_impact": round(
                metrics["ADD"]["total_impact"] - metrics["DELETE"]["total_impact"], 2
            ),
            "action_rate": round(
                (total_actions / total_count) * 100, 1
            )
            if total_count > 0
            else 0,
        }

    def approve_reconciliation_action(
        self, reconciliation_id: int, approved_by: str
    ):
        """Approve and execute a reconciliation recommendation"""
        param_placeholder = "%s" if self.db.db_type == "postgresql" else "?"

        date_expr = (
            "CURRENT_DATE"
            if self.db.db_type == "postgresql"
            else "DATE('now')"
        )

        query = f"""
        UPDATE hcc_reconciliation
        SET action_taken = TRUE,
            action_date = {date_expr},
            action_by = {param_placeholder}
        WHERE reconciliation_id = {param_placeholder}
        """

        self.db.execute_query(
            query, (approved_by, reconciliation_id), fetch="none"
        )


if __name__ == "__main__":
    reconciler = HCCReconciliation()

    print("Running HCC Reconciliation...")
    results = reconciler.run_comprehensive_reconciliation(lookback_months=12)

    print("\nReconciliation Summary:")
    print(f"   ADD opportunities: {results['summary']['total_add_opportunities']}")
    print(f"   DELETE requirements: {results['summary']['total_delete_required']}")
    print(f"   ADD value: ${results['summary']['add_financial_value']:,.2f}")
    print(f"   DELETE risk: ${results['summary']['delete_financial_risk']:,.2f}")
    print(f"   Net impact: ${results['summary']['net_financial_impact']:,.2f}")

    dashboard = reconciler.get_reconciliation_dashboard()
    print("\nDashboard Metrics:")
    print(f"   Action rate: {dashboard['action_rate']}%")
    print(f"   Net financial impact: ${dashboard['net_financial_impact']:,.2f}")
