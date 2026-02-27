"""
Regulatory Intelligence - Agentic RAG for HCC/RADV regulatory monitoring
Monitors CMS.gov, AAPC, and other sources for regulatory changes
"""
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from anthropic import Anthropic
from database import get_db_manager


class RegulatoryIntelligence:
    """
    Agentic RAG system that monitors CMS.gov, AAPC, and other sources
    for regulatory changes affecting HCC coding and RADV audits

    Features:
    1. Auto-scrape regulatory sources
    2. AI-powered impact analysis
    3. Actionable recommendations
    4. Alert generation
    """

    def __init__(self):
        self.db = get_db_manager()
        self.client = Anthropic()
        self.model = "claude-sonnet-4-20250514"

        self.sources = {
            "CMS_RADV": "https://www.cms.gov/medicare/payment/risk-adjustment-data-validation",
            "CMS_HCC": "https://www.cms.gov/medicare/health-plans/medicareadvtgspecratestats/risk-adjustors",
            "AAPC": "https://www.aapc.com/blog/category/risk-adjustment",
            "CMS_MEMORANDA": "https://www.cms.gov/medicare/regulations-guidance/memoranda",
        }

    def scan_regulatory_sources(self, days_back: int = 30) -> List[Dict]:
        """
        Scan regulatory sources for new updates

        In production, this would use web_search and web_fetch tools
        For demo, we simulate with sample updates
        """
        sample_updates = [
            {
                "source": "CMS",
                "update_date": (
                    datetime.now() - timedelta(days=5)
                ).strftime("%Y-%m-%d"),
                "update_type": "RADV_MEMO",
                "title": "CMS Memo: Updated M.E.A.T. Documentation Requirements for 2026 RADV Audits",
                "summary": "CMS clarifies that M.E.A.T. elements must be specific to the encounter date. Problem lists without encounter-specific documentation will not be accepted.",
                "affected_hccs": ["ALL"],
                "impact_level": "HIGH",
                "implementation_date": "2026-04-01",
                "url": "https://www.cms.gov/memo/2026-radv-updates",
            },
            {
                "source": "CMS",
                "update_date": (
                    datetime.now() - timedelta(days=15)
                ).strftime("%Y-%m-%d"),
                "update_type": "MODEL_UPDATE",
                "title": "CMS-HCC Model V28 Coefficient Changes",
                "summary": "RAF coefficients updated for HCC 226 (CHF), HCC 280 (COPD), and diabetes complications. New weights effective payment year 2026.",
                "affected_hccs": [
                    "HCC 226",
                    "HCC 280",
                    "HCC 36",
                    "HCC 37",
                    "HCC 38",
                ],
                "impact_level": "MEDIUM",
                "implementation_date": "2026-01-01",
                "url": "https://www.cms.gov/files/model-v28-updates",
            },
            {
                "source": "AAPC",
                "update_date": (
                    datetime.now() - timedelta(days=7)
                ).strftime("%Y-%m-%d"),
                "update_type": "GUIDANCE",
                "title": "Best Practices: Documenting CKD Stages in Risk Adjustment",
                "summary": "New guidance on linking GFR values to CKD stage documentation. Providers must document specific stage (3, 4, or 5) and ensure consistency with lab values.",
                "affected_hccs": ["HCC 326", "HCC 327", "HCC 328", "HCC 329"],
                "impact_level": "MEDIUM",
                "implementation_date": "2026-03-01",
                "url": "https://www.aapc.com/blog/ckd-documentation-2026",
            },
        ]

        processed_updates = []
        for update in sample_updates:
            impact_analysis = self._analyze_regulatory_impact(update)
            full_update = {**update, **impact_analysis}

            if self._save_regulatory_update(full_update):
                processed_updates.append(full_update)

        return processed_updates

    def _analyze_regulatory_impact(self, update: Dict) -> Dict:
        """Use Claude to analyze regulatory impact and generate action items"""
        affected_str = (
            ", ".join(update["affected_hccs"])
            if isinstance(update["affected_hccs"], list)
            else str(update["affected_hccs"])
        )

        prompt = f"""You are a Medicare Advantage compliance expert analyzing regulatory updates.

Regulatory Update:
Title: {update['title']}
Source: {update['source']}
Summary: {update['summary']}
Affected HCCs: {affected_str}
Implementation Date: {update['implementation_date']}

Analyze this update and provide:
1. Specific action items for compliance teams
2. Changes to documentation requirements
3. Impact on existing HCC validations
4. Recommended timeline for implementation

Return ONLY valid JSON:
{{
    "action_items": ["Action 1", "Action 2", "Action 3"],
    "documentation_changes": "Summary of doc changes required",
    "validation_impact": "How this affects validation rates",
    "implementation_priority": "HIGH/MEDIUM/LOW",
    "estimated_effort_hours": 40
}}"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}],
            )

            result_text = (
                response.content[0].text.replace("```json", "").replace("```", "").strip()
            )
            analysis = json.loads(result_text)
            return analysis

        except Exception as e:
            return {
                "action_items": ["Review update and assess impact"],
                "documentation_changes": "To be determined",
                "validation_impact": "Under assessment",
                "implementation_priority": "MEDIUM",
                "estimated_effort_hours": 20,
            }

    def _save_regulatory_update(self, update: Dict) -> bool:
        """Save regulatory update to database. Returns True if inserted, False if duplicate."""
        param_placeholder = "%s" if self.db.db_type == "postgresql" else "?"

        # Skip duplicate (same title + update_date)
        check_query = f"""
        SELECT COUNT(*) as count FROM regulatory_updates
        WHERE title = {param_placeholder} AND update_date = {param_placeholder}
        """
        existing = self.db.execute_query(
            check_query,
            (update["title"], update["update_date"]),
            fetch="one",
        )
        if existing and (existing.get("count") or 0) > 0:
            return False

        affected_hccs = update["affected_hccs"]
        action_items = update.get("action_items", [])

        if not isinstance(affected_hccs, list):
            affected_hccs = [affected_hccs] if affected_hccs else []
        if not isinstance(action_items, list):
            action_items = [action_items] if action_items else []

        if self.db.db_type == "sqlite":
            affected_hccs = json.dumps(affected_hccs)
            action_items = json.dumps(action_items)

        query = f"""
        INSERT INTO regulatory_updates (
            source, update_date, update_type, title, summary,
            affected_hccs, impact_level, implementation_date,
            url, action_items, processed
        ) VALUES (
            {param_placeholder}, {param_placeholder}, {param_placeholder}, {param_placeholder}, {param_placeholder},
            {param_placeholder}, {param_placeholder}, {param_placeholder},
            {param_placeholder}, {param_placeholder}, FALSE
        )
        """

        self.db.execute_query(
            query,
            (
                update["source"],
                update["update_date"],
                update["update_type"],
                update["title"],
                update["summary"],
                affected_hccs,
                update["impact_level"],
                update["implementation_date"],
                update.get("url", ""),
                action_items,
            ),
            fetch="none",
        )
        return True

    def get_unprocessed_updates(self) -> List[Dict]:
        """Get regulatory updates that haven't been actioned yet"""
        query = """
        SELECT *
        FROM regulatory_updates
        WHERE processed = FALSE
        ORDER BY update_date DESC, impact_level DESC
        """

        updates = self.db.execute_query(query, fetch="all")

        if not updates:
            return []

        if self.db.db_type == "sqlite":
            for update in updates:
                ah = update.get("affected_hccs")
                update["affected_hccs"] = (
                    json.loads(ah) if isinstance(ah, str) and ah else []
                )
                ai = update.get("action_items")
                update["action_items"] = (
                    json.loads(ai) if isinstance(ai, str) and ai else []
                )

        return updates

    def mark_update_processed(self, update_id: int):
        """Mark regulatory update as processed"""
        param_placeholder = "%s" if self.db.db_type == "postgresql" else "?"

        query = f"""
        UPDATE regulatory_updates
        SET processed = TRUE
        WHERE update_id = {param_placeholder}
        """

        self.db.execute_query(query, (update_id,), fetch="none")

    def get_regulatory_dashboard(self) -> Dict:
        """Get regulatory intelligence dashboard metrics"""
        time_filter = (
            "update_date >= CURRENT_DATE - INTERVAL '90 days'"
            if self.db.db_type == "postgresql"
            else "update_date >= DATE('now', '-90 days')"
        )

        count_query = f"""
        SELECT
            impact_level,
            COUNT(*) as count
        FROM regulatory_updates
        WHERE {time_filter}
        GROUP BY impact_level
        """

        counts = self.db.execute_query(count_query, fetch="all")
        impact_breakdown = (
            {row["impact_level"]: row["count"] for row in counts} if counts else {}
        )

        unprocessed_query = """
        SELECT COUNT(*) as count
        FROM regulatory_updates
        WHERE processed = FALSE
        """
        unprocessed = self.db.execute_query(unprocessed_query, fetch="one")

        return {
            "total_updates_90d": sum(impact_breakdown.values()),
            "impact_breakdown": impact_breakdown,
            "unprocessed_updates": unprocessed.get("count", 0) or 0,
            "high_priority_pending": impact_breakdown.get("HIGH", 0),
        }


if __name__ == "__main__":
    intel = RegulatoryIntelligence()

    print("Scanning regulatory sources...")
    updates = intel.scan_regulatory_sources(days_back=30)

    print(f"\nFound {len(updates)} regulatory updates")
    for update in updates:
        print(f"\n   {update['title']}")
        print(f"   Impact: {update['impact_level']}")
        print(f"   Action Items: {len(update.get('action_items', []))}")

    dashboard = intel.get_regulatory_dashboard()
    print(f"\nDashboard:")
    print(f"   Total updates (90d): {dashboard['total_updates_90d']}")
    print(f"   Unprocessed: {dashboard['unprocessed_updates']}")
