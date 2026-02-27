"""
Education Automation - Targeted Probe & Educate (TPE) automation
Auto-identifies providers needing education, generates training materials,
schedules sessions, and measures effectiveness.
"""
import json
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from database import get_db_manager


class EducationAutomation:
    """
    Targeted Probe & Educate (TPE) automation

    Functions:
    1. Auto-identify providers needing education
    2. Generate customized training materials
    3. Schedule and track education sessions
    4. Measure pre/post training effectiveness
    """

    def __init__(self):
        self.db = get_db_manager()
        try:
            from app_config import get_anthropic_client
            self.client = get_anthropic_client()
        except ImportError:
            self.client = None
        self.model = "claude-sonnet-4-20250514"

    def identify_providers_for_tpe(self,
                                   min_failures: int = 5,
                                   lookback_months: int = 6) -> pd.DataFrame:
        """
        Identify providers who would benefit from TPE

        CMS TPE criteria:
        - Providers with consistent documentation patterns leading to failures
        - Focus on high-volume providers with fixable issues
        """

        param_placeholder = '%s' if self.db.db_type == 'postgresql' else '?'

        cutoff_date = (datetime.now() - timedelta(days=lookback_months * 30)).strftime('%Y-%m-%d')

        query = f"""
        SELECT
            pms.provider_id,
            pms.provider_name,
            pms.specialty,
            pms.validation_rate,
            pms.risk_tier,
            pms.financial_risk_estimate,
            fp.failure_category,
            fp.occurrence_count,
            fp.hcc_category
        FROM provider_meat_scores pms
        JOIN failure_patterns fp ON pms.provider_id = fp.provider_id
        WHERE pms.validation_rate < 90
        AND fp.occurrence_count >= {param_placeholder}
        AND fp.last_occurrence >= {param_placeholder}
        ORDER BY fp.occurrence_count DESC
        """

        results = self.db.execute_query(query, (min_failures, cutoff_date), fetch="all")

        if not results:
            return pd.DataFrame()

        df = pd.DataFrame(results)

        # Group by provider to get their top issues
        provider_issues = df.groupby('provider_id').agg({
            'provider_name': 'first',
            'specialty': 'first',
            'validation_rate': 'first',
            'risk_tier': 'first',
            'financial_risk_estimate': 'first',
            'failure_category': lambda x: list(x)[:3],  # Top 3 issues
            'hcc_category': lambda x: list(set(x))  # Unique HCC categories
        }).reset_index()

        return provider_issues

    def create_education_session(self,
                                 provider_id: str,
                                 focus_areas: List[str],
                                 scheduled_date: str,
                                 educator: Optional[str] = None) -> int:
        """
        Schedule a TPE education session for a provider

        Returns session_id
        """

        param_placeholder = '%s' if self.db.db_type == 'postgresql' else '?'

        # Get provider's current validation rate
        provider_query = f"""
        SELECT validation_rate
        FROM provider_meat_scores
        WHERE provider_id = {param_placeholder}
        """

        provider = self.db.execute_query(provider_query, (provider_id,), fetch="one")
        pre_rate = provider['validation_rate'] if provider and provider.get('validation_rate') is not None else 0.0

        # Determine session type based on severity
        if pre_rate < 70:
            session_type = 'INTENSIVE_1ON1'
        elif pre_rate < 85:
            session_type = 'STANDARD_TRAINING'
        else:
            session_type = 'REFRESHER'

        # Prepare focus_areas for insert (array in PostgreSQL, JSON in SQLite)
        focus_areas_param = json.dumps(focus_areas) if self.db.db_type == 'sqlite' else focus_areas

        insert_query = f"""
        INSERT INTO education_sessions (
            provider_id, session_type, focus_areas, scheduled_date,
            educator_assigned, pre_session_validation_rate
        ) VALUES (
            {param_placeholder}, {param_placeholder}, {param_placeholder}, {param_placeholder},
            {param_placeholder}, {param_placeholder}
        )
        """
        insert_params = (provider_id, session_type, focus_areas_param, scheduled_date, educator, pre_rate)

        if self.db.db_type == 'postgresql':
            insert_query += " RETURNING session_id"
            result = self.db.execute_query(insert_query, insert_params, fetch="one")
            session_id = result['session_id']
        else:
            # SQLite: must get last_insert_rowid() on same connection as INSERT
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(insert_query, insert_params)
                conn.commit()
                cursor.execute("SELECT last_insert_rowid()")
                session_id = cursor.fetchone()[0]

        # Generate and assign materials
        self._assign_materials(session_id, provider_id, focus_areas)

        return session_id

    def _assign_materials(self, session_id: int, provider_id: str, focus_areas: List[str]):
        """
        Auto-assign relevant education materials based on focus areas
        """

        param_placeholder = '%s' if self.db.db_type == 'postgresql' else '?'

        if focus_areas:
            placeholders = ','.join([param_placeholder] * len(focus_areas))
            materials_query = f"""
            SELECT material_id, material_name, file_path
            FROM education_materials
            WHERE category IN ({placeholders})
            ORDER BY effectiveness_score DESC NULLS LAST
            LIMIT 5
            """
            if self.db.db_type == 'sqlite':
                materials_query = materials_query.replace("NULLS LAST", "")
            materials = self.db.execute_query(materials_query, tuple(focus_areas), fetch="all")
        else:
            materials_query = """
            SELECT material_id, material_name, file_path
            FROM education_materials
            ORDER BY effectiveness_score DESC
            LIMIT 5
            """
            materials = self.db.execute_query(materials_query, fetch="all")

        if materials:
            material_list = [m['material_name'] for m in materials]
            material_list_param = json.dumps(material_list) if self.db.db_type == 'sqlite' else material_list

            update_query = f"""
            UPDATE education_sessions
            SET materials_list = {param_placeholder},
                materials_sent = TRUE
            WHERE session_id = {param_placeholder}
            """

            self.db.execute_query(update_query, (material_list_param, session_id), fetch="none")

    def generate_customized_training_content(self,
                                            provider_id: str,
                                            failure_patterns: List[str]) -> Dict:
        """
        Use AI to generate personalized training content

        Creates custom examples and explanations tailored to provider's specific gaps
        """

        if not self.client:
            return {
                'explanation': 'Training content generation requires Anthropic API.',
                'corrected_examples': [],
                'checklist': ['Review M.E.A.T. framework', 'Document treatment plans']
            }

        param_placeholder = '%s' if self.db.db_type == 'postgresql' else '?'

        examples_query = f"""
        SELECT
            hcc_code,
            hcc_description,
            documentation_text,
            failure_reason,
            meat_monitor,
            meat_evaluate,
            meat_assess,
            meat_treat
        FROM hcc_audit_trail
        WHERE provider_id = {param_placeholder}
        AND validation_status = 'FAIL'
        ORDER BY encounter_date DESC
        LIMIT 5
        """

        examples = self.db.execute_query(examples_query, (provider_id,), fetch="all")

        if not examples:
            examples_text = "No specific examples available"
        else:
            examples_text = "\n\n".join([
                f"HCC {ex['hcc_code']} - {ex['hcc_description']}\n"
                f"Documentation: {ex['documentation_text'] or '(none)'}\n"
                f"Failure Reason: {ex['failure_reason']}\n"
                f"M.E.A.T. Present: M={ex['meat_monitor']}, E={ex['meat_evaluate']}, "
                f"A={ex['meat_assess']}, T={ex['meat_treat']}"
                for ex in examples
            ])

        prompt = f"""You are a medical coding educator creating personalized training materials.

Provider's Top Failure Patterns:
{chr(10).join(f'- {pattern}' for pattern in failure_patterns)}

Recent Failed Documentation Examples:
{examples_text}

Create a customized training guide with:
1. Explanation of the specific documentation gaps
2. 3 corrected examples showing proper M.E.A.T. documentation
3. Quick reference checklist for this provider

Format as JSON:
{{
    "explanation": "You're primarily missing the 'Treat' element...",
    "corrected_examples": [
        {{"hcc": "HCC 226", "bad": "CHF stable", "good": "CHF stable on Lasix 40mg daily"}},
        ...
    ],
    "checklist": ["Document current medications", "Note recent labs", ...]
}}"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            result_text = response.content[0].text.replace('```json', '').replace('```', '').strip()
            start = result_text.find('{')
            end = result_text.rfind('}') + 1
            if start >= 0 and end > start:
                training_content = json.loads(result_text[start:end])
            else:
                training_content = json.loads(result_text)

            return training_content

        except Exception as e:
            print(f"Training generation error: {e}")
            return {
                'explanation': 'Training content generation in progress',
                'corrected_examples': [],
                'checklist': ['Review M.E.A.T. framework', 'Document treatment plans']
            }

    def complete_education_session(self,
                                  session_id: int,
                                  attendance_status: str,
                                  notes: Optional[str] = None):
        """
        Mark education session as completed and trigger follow-up
        """

        param_placeholder = '%s' if self.db.db_type == 'postgresql' else '?'

        if self.db.db_type == 'postgresql':
            update_query = f"""
            UPDATE education_sessions
            SET session_status = 'COMPLETED',
                completed_date = CURRENT_DATE,
                attendance_status = {param_placeholder},
                session_notes = {param_placeholder},
                followup_required = TRUE,
                followup_date = CURRENT_DATE + INTERVAL '30 days'
            WHERE session_id = {param_placeholder}
            """
        else:
            update_query = f"""
            UPDATE education_sessions
            SET session_status = 'COMPLETED',
                completed_date = DATE('now'),
                attendance_status = {param_placeholder},
                session_notes = {param_placeholder},
                followup_required = 1,
                followup_date = DATE('now', '+30 days')
            WHERE session_id = {param_placeholder}
            """

        self.db.execute_query(update_query, (attendance_status, notes, session_id), fetch="none")

    def measure_training_effectiveness(self, session_id: int) -> Dict:
        """
        Measure post-training validation rate improvement

        Compares pre/post session HCC validation rates
        """

        param_placeholder = '%s' if self.db.db_type == 'postgresql' else '?'

        session_query = f"""
        SELECT
            provider_id,
            pre_session_validation_rate,
            completed_date,
            focus_areas
        FROM education_sessions
        WHERE session_id = {param_placeholder}
        """

        session = self.db.execute_query(session_query, (session_id,), fetch="one")

        if not session or not session['completed_date']:
            return {'status': 'Session not completed'}

        # Calculate post-session validation rate (encounters 30+ days after training)
        post_start_date = (
            datetime.strptime(str(session['completed_date']), '%Y-%m-%d') + timedelta(days=30)
        ).strftime('%Y-%m-%d')

        date_expr = "CURRENT_DATE" if self.db.db_type == 'postgresql' else "DATE('now')"
        post_rate_query = f"""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN validation_status = 'PASS' THEN 1 ELSE 0 END) as passed
        FROM hcc_audit_trail
        WHERE provider_id = {param_placeholder}
        AND encounter_date >= {param_placeholder}
        AND encounter_date <= {date_expr}
        """

        post_stats = self.db.execute_query(
            post_rate_query, (session['provider_id'], post_start_date), fetch="one"
        )

        if not post_stats or post_stats.get('total', 0) == 0:
            return {'status': 'Insufficient post-training data'}

        passed = post_stats.get('passed') or 0
        total = post_stats['total']
        post_rate = (passed / total * 100) if total > 0 else 0

        pre_rate = session.get('pre_session_validation_rate') or 0
        improvement = post_rate - pre_rate

        # Update session with post-training score
        update_query = f"""
        UPDATE education_sessions
        SET post_session_validation_rate = {param_placeholder}
        WHERE session_id = {param_placeholder}
        """

        self.db.execute_query(update_query, (post_rate, session_id), fetch="none")

        improvement_pct = (improvement / pre_rate * 100) if pre_rate > 0 else 0

        return {
            'session_id': session_id,
            'provider_id': session['provider_id'],
            'pre_session_rate': pre_rate,
            'post_session_rate': post_rate,
            'improvement': improvement,
            'improvement_pct': improvement_pct,
            'effectiveness_rating': (
                'HIGHLY_EFFECTIVE' if improvement > 10
                else 'EFFECTIVE' if improvement > 5
                else 'NEEDS_FOLLOWUP'
            )
        }

    def get_education_dashboard(self) -> Dict:
        """
        Get overview of all education activities

        Returns metrics for management reporting
        """

        date_expr = "CURRENT_DATE" if self.db.db_type == 'postgresql' else "DATE('now')"

        session_stats_query = """
        SELECT
            session_status,
            COUNT(*) as count
        FROM education_sessions
        GROUP BY session_status
        """

        session_stats = self.db.execute_query(session_stats_query, fetch="all")
        status_breakdown = {row['session_status']: row['count'] for row in session_stats}

        effectiveness_query = """
        SELECT
            AVG(post_session_validation_rate - pre_session_validation_rate) as avg_improvement,
            COUNT(*) as completed_sessions
        FROM education_sessions
        WHERE session_status = 'COMPLETED'
        AND post_session_validation_rate IS NOT NULL
        """

        effectiveness = self.db.execute_query(effectiveness_query, fetch="one")

        upcoming_query = f"""
        SELECT COUNT(*) as upcoming
        FROM education_sessions
        WHERE scheduled_date >= {date_expr}
        AND session_status = 'SCHEDULED'
        """

        upcoming = self.db.execute_query(upcoming_query, fetch="one")

        avg_improvement = effectiveness.get('avg_improvement') if effectiveness else None
        completed_sessions = effectiveness.get('completed_sessions', 0) if effectiveness else 0
        upcoming_count = upcoming.get('upcoming', 0) if upcoming else 0

        return {
            'total_sessions': sum(status_breakdown.values()),
            'status_breakdown': status_breakdown,
            'avg_improvement': round(avg_improvement, 2) if avg_improvement is not None else 0,
            'completed_sessions': completed_sessions,
            'upcoming_sessions': upcoming_count
        }


if __name__ == "__main__":
    educator = EducationAutomation()

    # Identify providers for TPE
    providers = educator.identify_providers_for_tpe()
    print(f"Found {len(providers)} providers needing education")

    if not providers.empty:
        print("\nTop providers for TPE:")
        print(providers[['provider_name', 'validation_rate', 'risk_tier']].head())
