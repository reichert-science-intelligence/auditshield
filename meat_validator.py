# meat_validator.py
import json
import re
from typing import Dict, List, Optional
from datetime import datetime

from app_config import get_anthropic_client
from database import get_db_manager


class MEATValidator:
    """
    Validates HCC documentation against M.E.A.T. criteria using Claude
    with self-correcting validation loops
    """

    def __init__(self, api_key: Optional[str] = None):
        self.client = get_anthropic_client(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"

        # Top 10 High-Impact HCC categories from your document
        self.high_impact_hccs = {
            'HCC 36-38': 'Diabetes with Complications',
            'HCC 226': 'Congestive Heart Failure',
            'HCC 280': 'COPD',
            'HCC 326-329': 'Chronic Kidney Disease',
            'HCC 155': 'Major Depressive Disorder',
            'HCC 264': 'Vascular Disease/PVD',
            'HCC 22': 'Morbid Obesity',
            'HCC 238': 'Specified Heart Arrhythmias',
            'HCC 92': 'Rheumatoid Arthritis',
            'HCC 17-21': 'Active Cancers'
        }

    def validate_hcc_documentation(self,
                                   hcc_code: str,
                                   diagnosis: str,
                                   documentation: str,
                                   encounter_date: str) -> Dict:
        """
        Core validation function with self-correcting loops

        Returns:
            {
                'meat_elements': {...},
                'validation_status': 'PASS'/'FAIL'/'HUMAN_REVIEW',
                'confidence_score': 85,
                'failure_reason': 'Missing Treat element',
                'recommendations': 'Add medication or treatment plan',
                'hcc_category': 'Diabetes with Complications'
            }
        """

        # Determine HCC category
        hcc_category = self._categorize_hcc(hcc_code, diagnosis)

        # First pass validation
        validation_result = self._run_validation_prompt(
            hcc_code, diagnosis, documentation, encounter_date
        )

        # Self-correction loop: If low confidence, run second opinion
        if validation_result['confidence_score'] < 75:
            second_opinion = self._run_validation_prompt(
                hcc_code, diagnosis, documentation, encounter_date,
                is_second_pass=True,
                first_result=validation_result
            )

            # Compare results and flag discrepancies
            if second_opinion['validation_status'] != validation_result['validation_status']:
                validation_result['validation_status'] = 'HUMAN_REVIEW'
                validation_result['review_reason'] = 'AI model disagreement on validation'
            else:
                # Use higher confidence result
                if second_opinion['confidence_score'] > validation_result['confidence_score']:
                    validation_result = second_opinion

        validation_result['hcc_category'] = hcc_category
        validation_result['is_high_impact'] = self._is_high_impact_hcc(hcc_code)

        return validation_result

    def _run_validation_prompt(self,
                              hcc_code: str,
                              diagnosis: str,
                              documentation: str,
                              encounter_date: str,
                              is_second_pass: bool = False,
                              first_result: Optional[Dict] = None) -> Dict:
        """Execute Claude validation with structured output"""

        system_prompt = """You are a certified risk adjustment coder (CRC) performing CMS RADV audit validation.

Your task is to determine if this HCC code would survive a CMS audit based on M.E.A.T. criteria:
- Monitor: Signs/symptoms, lab tracking, disease progression
- Evaluate: Test result interpretation, clinical data review
- Assess: Clinical judgment, counseling, decision-making
- Treat: Medications, referrals, procedures, treatment plan

CRITICAL RULES:
1. Problem lists or past medical history alone = FAIL
2. "History of" cancer = FAIL (unless active treatment/surveillance)
3. Unspecified diagnoses without complications = FAIL for complication HCCs
4. At least ONE M.E.A.T. element with specific evidence = PASS
5. Generic statements like "chronic conditions stable" without specifics = FAIL

Return ONLY valid JSON, no markdown formatting."""

        if is_second_pass:
            user_prompt = f"""SECOND OPINION REVIEW:

The first reviewer assessed this as {first_result['validation_status']} with {first_result['confidence_score']}% confidence.
Please independently re-evaluate:

HCC Code: {hcc_code}
Diagnosis: {diagnosis}
Encounter Date: {encounter_date}

Clinical Documentation:
{documentation}

Provide your independent assessment in this exact JSON format:
{{
    "meat_elements": {{
        "monitor": {{"present": true/false, "evidence": "exact quote from documentation or null"}},
        "evaluate": {{"present": true/false, "evidence": "exact quote or null"}},
        "assess": {{"present": true/false, "evidence": "exact quote or null"}},
        "treat": {{"present": true/false, "evidence": "exact quote or null"}}
    }},
    "validation_status": "PASS/FAIL",
    "confidence_score": 85,
    "failure_reason": "specific reason or null",
    "recommendations": "specific documentation improvements needed"
}}"""
        else:
            user_prompt = f"""HCC Code: {hcc_code}
Diagnosis: {diagnosis}
Encounter Date: {encounter_date}

Clinical Documentation:
{documentation}

Analyze this documentation and provide your assessment in this exact JSON format:
{{
    "meat_elements": {{
        "monitor": {{"present": true/false, "evidence": "exact quote from documentation or null"}},
        "evaluate": {{"present": true/false, "evidence": "exact quote or null"}},
        "assess": {{"present": true/false, "evidence": "exact quote or null"}},
        "treat": {{"present": true/false, "evidence": "exact quote or null"}}
    }},
    "validation_status": "PASS/FAIL",
    "confidence_score": 85,
    "failure_reason": "specific reason or null",
    "recommendations": "specific documentation improvements needed"
}}"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )

            # Extract JSON from response
            response_text = response.content[0].text

            # Clean markdown formatting if present
            response_text = re.sub(r'```json\n?', '', response_text)
            response_text = re.sub(r'```\n?', '', response_text)

            result = json.loads(response_text)

            # Calculate M.E.A.T. score (0-4)
            meat_score = sum(
                1 for element in result['meat_elements'].values()
                if element['present']
            )
            result['meat_score'] = meat_score

            return result

        except json.JSONDecodeError as e:
            # Fallback to HUMAN_REVIEW if parsing fails
            return {
                'meat_elements': {
                    'monitor': {'present': False, 'evidence': None},
                    'evaluate': {'present': False, 'evidence': None},
                    'assess': {'present': False, 'evidence': None},
                    'treat': {'present': False, 'evidence': None}
                },
                'validation_status': 'HUMAN_REVIEW',
                'confidence_score': 0,
                'failure_reason': f'AI parsing error: {str(e)}',
                'recommendations': 'Manual review required',
                'meat_score': 0
            }

    def _categorize_hcc(self, hcc_code: str, diagnosis: str) -> str:
        """Map HCC code to category from Top 10 list"""

        # Extract numeric code
        match = re.search(r'\d+', hcc_code)
        numeric_code = int(match.group()) if match else 0

        # Mapping logic based on your document
        if 36 <= numeric_code <= 38:
            return 'Diabetes with Complications'
        elif numeric_code == 226:
            return 'Congestive Heart Failure'
        elif numeric_code == 280:
            return 'COPD'
        elif 326 <= numeric_code <= 329:
            return 'Chronic Kidney Disease'
        elif numeric_code == 155:
            return 'Major Depressive Disorder'
        elif numeric_code == 264:
            return 'Vascular Disease/PVD'
        elif numeric_code == 22:
            return 'Morbid Obesity'
        elif numeric_code == 238:
            return 'Specified Heart Arrhythmias'
        elif numeric_code == 92:
            return 'Rheumatoid Arthritis'
        elif 17 <= numeric_code <= 21:
            return 'Active Cancers'
        else:
            return 'Other HCC'

    def _is_high_impact_hcc(self, hcc_code: str) -> bool:
        """Check if HCC is in Top 10 high-impact list"""
        match = re.search(r'\d+', hcc_code)
        numeric_code = int(match.group()) if match else 0

        high_impact_ranges = [
            (36, 38), (17, 21), (326, 329)
        ]
        high_impact_singles = [226, 280, 155, 264, 22, 238, 92]

        return (numeric_code in high_impact_singles or
                any(start <= numeric_code <= end for start, end in high_impact_ranges))

    def batch_validate_provider(self,
                                provider_id: str,
                                lookback_months: int = 12) -> Dict:
        """
        Validate all HCCs for a provider and calculate scorecard metrics

        Uses get_db_manager() for database access. After processing all
        validations, updates provider scores in the database.
        """

        db = get_db_manager()
        hccs = db.get_provider_hccs(provider_id, lookback_months)

        results = []
        for hcc in hccs:
            # Map DB fields to validator args (hcc_description -> diagnosis, documentation_text -> documentation)
            diagnosis = hcc.get('hcc_description') or hcc.get('diagnosis', '')
            documentation = hcc.get('documentation_text') or hcc.get('documentation', '')
            encounter_date = hcc.get('encounter_date')
            if hasattr(encounter_date, 'isoformat'):
                encounter_date = encounter_date.isoformat()
            else:
                encounter_date = str(encounter_date) if encounter_date else ''

            validation = self.validate_hcc_documentation(
                hcc['hcc_code'],
                diagnosis,
                documentation,
                encounter_date
            )
            results.append({
                **hcc,
                **validation
            })

            # Persist validation results to audit trail (for re-validation)
            if hcc.get('audit_id') and validation.get('validation_status'):
                db.update_hcc_audit(hcc['audit_id'], validation)

        # Calculate metrics
        total_hccs = len(results)
        validated_hccs = sum(1 for r in results if r['validation_status'] == 'PASS')
        validation_rate = (validated_hccs / total_hccs * 100) if total_hccs > 0 else 0

        # Financial risk calculation
        cms_base_rate = 1142.50  # 2026 estimate
        failed_raf = sum(
            r.get('raf_weight', 0) for r in results
            if r['validation_status'] == 'FAIL'
        )
        financial_risk = failed_raf * cms_base_rate

        # Failure pattern analysis
        failure_patterns = {}
        for r in results:
            if r.get('failure_reason'):
                key = r['failure_reason']
                if key not in failure_patterns:
                    failure_patterns[key] = {
                        'count': 0,
                        'hcc_examples': [],
                        'categories': set()
                    }
                failure_patterns[key]['count'] += 1
                failure_patterns[key]['hcc_examples'].append(r['hcc_code'])
                failure_patterns[key]['categories'].add(r.get('hcc_category', ''))

        # Convert sets to lists for JSON serialization
        for pattern in failure_patterns.values():
            pattern['categories'] = list(pattern['categories'])

        # Determine risk tier
        if validation_rate >= 90:
            risk_tier = 'GREEN'
        elif validation_rate >= 80:
            risk_tier = 'YELLOW'
        else:
            risk_tier = 'RED'

        scorecard_results = {
            'provider_id': provider_id,
            'total_hccs_submitted': total_hccs,
            'total_hccs_validated': validated_hccs,
            'validation_rate': round(validation_rate, 2),
            'financial_risk_estimate': round(financial_risk, 2),
            'risk_tier': risk_tier,
            'failure_patterns': failure_patterns,
            'detailed_results': results,
            'calculated_at': datetime.now().isoformat()
        }

        # Update the database with recalculated provider scores
        db.update_provider_scores(provider_id, lookback_months)

        return scorecard_results
