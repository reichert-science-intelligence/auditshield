"""
Chart Selection AI - AI-powered medical record selection for RADV audits
Analyzes multiple encounters per enrollee and selects the best records for CMS submission.
"""
import json
from datetime import datetime

import pandas as pd

from database import get_db_manager


class ChartSelectionAI:
    """
    AI-powered medical record selection for RADV audits

    For each enrollee, analyzes multiple encounters and selects
    the "best" records to submit to CMS that will maximize validation rates
    """

    def __init__(self):
        self.db = get_db_manager()
        try:
            from app_config import get_anthropic_client
            self.client = get_anthropic_client()
        except ImportError:
            self.client = None
        self.model = "claude-sonnet-4-20250514"

    def score_all_charts_for_enrollee(self,
                                      audit_id: int,
                                      sample_id: int,
                                      enrollee_id: str,
                                      hccs_to_validate: list[str]) -> pd.DataFrame:
        """
        Score all available medical records for an enrollee

        Returns ranked DataFrame of records with recommendation scores
        """

        # Get all encounters for this enrollee from audit trail (patient_id = enrollee_id)
        param_placeholder = '%s' if self.db.db_type == 'postgresql' else '?'

        # Build HCC filter
        if self.db.db_type == 'postgresql':
            hcc_filter = f"hcc_code = ANY({param_placeholder})"
            params = (enrollee_id, hccs_to_validate)
        else:
            placeholders = ','.join(['?'] * len(hccs_to_validate))
            hcc_filter = f"hcc_code IN ({placeholders})"
            params = tuple([enrollee_id] + list(hccs_to_validate))

        query = f"""
        SELECT
            encounter_id,
            encounter_date,
            provider_id,
            hcc_code,
            hcc_description,
            hcc_category,
            raf_weight,
            meat_monitor,
            meat_evaluate,
            meat_assess,
            meat_treat,
            meat_score,
            validation_status,
            confidence_score,
            documentation_text
        FROM hcc_audit_trail
        WHERE patient_id = {param_placeholder}
        AND {hcc_filter}
        ORDER BY encounter_date DESC
        """

        encounters = self.db.execute_query(query, params, fetch="all")

        if not encounters:
            return pd.DataFrame()

        # Group by encounter to analyze complete visits
        encounter_groups = {}
        for enc in encounters:
            enc_id = enc['encounter_id']
            if enc_id not in encounter_groups:
                encounter_groups[enc_id] = {
                    'encounter_id': enc_id,
                    'encounter_date': enc['encounter_date'],
                    'provider_id': enc['provider_id'],
                    'hccs': [],
                    'documentation': enc['documentation_text']
                }
            encounter_groups[enc_id]['hccs'].append({
                'hcc_code': enc['hcc_code'],
                'hcc_description': enc['hcc_description'],
                'meat_score': enc['meat_score'],
                'validation_status': enc['validation_status'],
                'confidence_score': enc['confidence_score']
            })

        # Score each encounter
        scored_records = []
        for enc_id, enc_data in encounter_groups.items():
            score = self._score_single_encounter(enc_data, hccs_to_validate)
            score['enrollee_id'] = enrollee_id
            scored_records.append(score)

        # Convert to DataFrame and rank
        df = pd.DataFrame(scored_records)
        df = df.sort_values('overall_score', ascending=False)
        df['recommendation_rank'] = range(1, len(df) + 1)

        # Store scores in database
        for _, row in df.iterrows():
            self._save_chart_score(audit_id, sample_id, row)

        return df

    def _score_single_encounter(self, encounter_data: dict, required_hccs: list[str]) -> dict:
        """
        Score a single encounter using multiple criteria

        Scoring factors:
        1. M.E.A.T. completeness (0-40 points)
        2. Documentation quality (0-30 points)
        3. HCC coverage (0-20 points)
        4. Provider reliability (0-10 points)
        5. Encounter recency (0-5 points)
        """

        scores = {
            'encounter_id': encounter_data['encounter_id'],
            'encounter_date': encounter_data['encounter_date'],
            'provider_id': encounter_data['provider_id']
        }

        # Factor 1: M.E.A.T. Completeness (0-40 points)
        hcc_meat_scores = [hcc['meat_score'] for hcc in encounter_data['hccs']]
        avg_meat_score = sum(hcc_meat_scores) / len(hcc_meat_scores) if hcc_meat_scores else 0
        scores['meat_score'] = (avg_meat_score / 4) * 40  # Normalize to 0-40

        # Factor 2: Documentation Quality via AI (0-30 points)
        doc_quality = self._assess_documentation_quality(
            encounter_data['documentation'],
            encounter_data['hccs']
        )
        scores['documentation_quality_score'] = doc_quality

        # Factor 3: HCC Coverage (0-20 points)
        hccs_present = [hcc['hcc_code'] for hcc in encounter_data['hccs']]
        coverage_pct = len(set(hccs_present) & set(required_hccs)) / len(required_hccs) if required_hccs else 0
        scores['completeness_score'] = coverage_pct * 20

        # Factor 4: Provider Reliability (0-10 points)
        provider_score = self._get_provider_reliability_score(encounter_data['provider_id'])
        scores['provider_reliability_score'] = provider_score

        # Factor 5: Encounter Recency (bonus points, 0-5)
        days_old = (datetime.now() - datetime.strptime(str(encounter_data['encounter_date']), '%Y-%m-%d')).days
        recency_score = max(0, 5 - (days_old / 365))  # Newer is better
        scores['encounter_recency_score'] = recency_score

        # Calculate overall score (max 105 points, normalized to 100)
        scores['overall_score'] = min(100, (
            scores['meat_score'] +
            scores['documentation_quality_score'] +
            scores['completeness_score'] +
            scores['provider_reliability_score'] +
            scores['encounter_recency_score']
        ))

        # AI recommendation
        if scores['overall_score'] >= 85:
            scores['recommendation'] = 'SUBMIT_FIRST'
            scores['confidence_level'] = 95
        elif scores['overall_score'] >= 70:
            scores['recommendation'] = 'SUBMIT_BACKUP'
            scores['confidence_level'] = 80
        else:
            scores['recommendation'] = 'DO_NOT_SUBMIT'
            scores['confidence_level'] = 60

        return scores

    def _assess_documentation_quality(self, documentation: str | None, hccs: list[dict]) -> float:
        """
        Use Claude to assess documentation quality

        Returns score 0-30
        """
        if not self.client:
            return 15.0  # Default when Anthropic not available

        documentation = documentation or ""
        hcc_list = [f"{hcc['hcc_code']}: {hcc['hcc_description']}" for hcc in hccs]

        prompt = f"""You are a medical coder performing RADV audit chart review.

Assess this documentation for CMS RADV submission quality.

HCCs to validate:
{chr(10).join(hcc_list)}

Documentation:
{documentation}

Rate the documentation quality on a 0-30 point scale:
- Clarity and specificity (0-10 points)
- Linkage between diagnoses and complications (0-10 points)
- Absence of ambiguity or contradictions (0-10 points)

Return ONLY a JSON object:
{{
    "clarity_score": 8,
    "linkage_score": 7,
    "consistency_score": 9,
    "total_score": 24,
    "strengths": ["Clear symptom documentation"],
    "weaknesses": ["Missing lab values"]
}}"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            result_text = response.content[0].text
            # Extract JSON from response (handle markdown code blocks)
            text = result_text.replace('```json', '').replace('```', '').strip()
            start = text.find('{')
            end = text.rfind('}') + 1
            if start >= 0 and end > start:
                result = json.loads(text[start:end])
            else:
                result = json.loads(text)

            return min(30, max(0, float(result.get('total_score', 15))))

        except Exception as e:
            print(f"AI scoring error: {e}")
            return 15.0  # Default middle score on error

    def _get_provider_reliability_score(self, provider_id: str) -> float:
        """
        Get provider's historical validation rate

        Returns score 0-10
        """

        param_placeholder = '%s' if self.db.db_type == 'postgresql' else '?'

        query = f"""
        SELECT validation_rate
        FROM provider_meat_scores
        WHERE provider_id = {param_placeholder}
        """

        result = self.db.execute_query(query, (provider_id,), fetch="one")

        if not result or result.get('validation_rate') is None:
            return 5.0  # Default middle score

        # Convert validation rate (0-100) to score (0-10)
        return (result['validation_rate'] / 100) * 10

    def _save_chart_score(self, audit_id: int, sample_id: int, score_data: pd.Series):
        """Save chart selection score to database"""

        param_placeholder = '%s' if self.db.db_type == 'postgresql' else '?'

        # Check if record exists (use provider_id for uniqueness when same-day encounters)
        check_query = f"""
        SELECT record_id
        FROM audit_medical_records
        WHERE audit_id = {param_placeholder}
        AND sample_id = {param_placeholder}
        AND enrollee_id = {param_placeholder}
        AND encounter_date = {param_placeholder}
        AND provider_id = {param_placeholder}
        """

        existing = self.db.execute_query(
            check_query,
            (audit_id, sample_id, score_data.get('enrollee_id', 'UNKNOWN'),
             score_data['encounter_date'], score_data['provider_id']),
            fetch="one"
        )

        if existing:
            record_id = existing['record_id']
        else:
            # Create record - use same connection for SQLite last_insert_rowid
            insert_record = f"""
            INSERT INTO audit_medical_records (
                sample_id, audit_id, enrollee_id, encounter_date,
                provider_id, record_quality_score, ai_recommendation_rank
            ) VALUES (
                {param_placeholder}, {param_placeholder}, {param_placeholder}, {param_placeholder},
                {param_placeholder}, {param_placeholder}, {param_placeholder}
            )
            """
            insert_params = (
                sample_id, audit_id, score_data.get('enrollee_id', 'UNKNOWN'),
                score_data['encounter_date'], score_data['provider_id'],
                score_data['overall_score'], score_data['recommendation_rank']
            )

            if self.db.db_type == 'postgresql':
                insert_record += " RETURNING record_id"
                result = self.db.execute_query(
                    insert_record, insert_params, fetch="one"
                )
                record_id = result['record_id']
            else:
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(insert_record, insert_params)
                    conn.commit()
                    cursor.execute("SELECT last_insert_rowid()")
                    record_id = cursor.fetchone()[0]

        # Save score to chart_selection_scores
        score_query = f"""
        INSERT INTO chart_selection_scores (
            record_id, sample_id, overall_score, meat_score,
            documentation_quality_score, completeness_score,
            provider_reliability_score, encounter_recency_score,
            recommendation, confidence_level
        ) VALUES (
            {param_placeholder}, {param_placeholder}, {param_placeholder}, {param_placeholder},
            {param_placeholder}, {param_placeholder}, {param_placeholder}, {param_placeholder},
            {param_placeholder}, {param_placeholder}
        )
        """

        self.db.execute_query(
            score_query,
            (record_id, sample_id, score_data['overall_score'], score_data['meat_score'],
             score_data['documentation_quality_score'], score_data['completeness_score'],
             score_data['provider_reliability_score'], score_data['encounter_recency_score'],
             score_data['recommendation'], score_data['confidence_level']),
            fetch="none"
        )

    def get_submission_recommendations(self, audit_id: int) -> pd.DataFrame:
        """
        Get top-ranked chart recommendations for all enrollees in audit

        Returns DataFrame with best record for each enrollee
        """

        param_placeholder = '%s' if self.db.db_type == 'postgresql' else '?'

        query = f"""
        SELECT
            amr.sample_id,
            ase.enrollee_id,
            ase.enrollee_name,
            amr.encounter_date,
            amr.provider_id,
            css.overall_score,
            css.recommendation,
            css.confidence_level,
            amr.ai_recommendation_rank
        FROM audit_medical_records amr
        JOIN chart_selection_scores css ON amr.record_id = css.record_id
        JOIN audit_sample_enrollees ase ON amr.sample_id = ase.sample_id
        WHERE amr.audit_id = {param_placeholder}
        AND amr.ai_recommendation_rank = 1
        ORDER BY css.overall_score DESC
        """

        results = self.db.execute_query(query, (audit_id,), fetch="all")

        if not results:
            return pd.DataFrame()

        return pd.DataFrame(results)


if __name__ == "__main__":
    selector = ChartSelectionAI()

    # Test with demo data
    print("Chart Selection AI initialized")
    print("Ready to score medical records for RADV submission")
