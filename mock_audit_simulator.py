# mock_audit_simulator.py
"""
Feature 1.2: Mock Audit Simulator
Simulates CMS RADV audit process to predict sample selection, HCC failures, and financial impact.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta

from database import get_db_manager


class MockAuditSimulator:
    """
    Simulates CMS RADV audit process to predict:
    1. Which enrollees would be selected in a sample
    2. Which HCCs are most likely to fail
    3. Estimated error rate and financial extrapolation
    """

    def __init__(self):
        self.db = get_db_manager()

        # CMS RADV parameters (2026 estimates)
        self.sample_sizes = {
            'small_contract': 35,    # <10,000 enrollees
            'medium_contract': 100,  # 10,000-50,000 enrollees
            'large_contract': 200    # >50,000 enrollees
        }

        self.cms_base_rate = 1142.50  # 2026 Medicare Advantage base rate

        # CMS targeting factors (based on published methodology)
        self.targeting_weights = {
            'high_raf_outlier': 0.30,      # 30% weight to high RAF outliers
            'condition_density': 0.25,     # 25% weight to many HCCs per enrollee
            'payment_growth': 0.20,         # 20% weight to year-over-year growth
            'high_risk_hccs': 0.15,        # 15% weight to top 10 HCC categories
            'provider_risk': 0.10          # 10% weight to high-risk providers
        }

    def run_mock_audit(self,
                       contract_id: str = "DEFAULT",
                       contract_size: str = "medium_contract",
                       year: int = 2026) -> Dict:
        """
        Execute complete mock audit simulation

        Returns:
            {
                'sample_enrollees': DataFrame of selected enrollees,
                'predicted_failures': DataFrame of likely failures,
                'error_rate_estimate': float,
                'financial_impact': dict,
                'audit_summary': dict
            }
        """

        # Step 1: Get all enrollees and their HCCs
        enrollees = self._get_enrollee_population(contract_id, year)

        if enrollees.empty:
            return {
                'sample_enrollees': pd.DataFrame(),
                'predicted_failures': pd.DataFrame(),
                'error_rate_estimate': 0.0,
                'financial_impact': {},
                'audit_summary': {'error': 'No enrollee data found'}
            }

        # Step 2: Calculate targeting scores
        enrollees = self._calculate_targeting_scores(enrollees)

        # Step 3: Select sample using CMS algorithm
        sample_size = self.sample_sizes[contract_size]
        sample_enrollees = self._select_cms_sample(enrollees, sample_size)

        # Step 4: Predict which HCCs will fail validation
        predicted_failures = self._predict_hcc_failures(sample_enrollees)

        # Step 5: Calculate error rate and financial impact
        error_rate = self._calculate_error_rate(predicted_failures)
        financial_impact = self._calculate_financial_impact(
            error_rate,
            enrollees,
            predicted_failures
        )

        # Step 6: Generate audit summary
        audit_summary = self._generate_audit_summary(
            sample_enrollees,
            predicted_failures,
            error_rate,
            financial_impact
        )

        return {
            'sample_enrollees': sample_enrollees,
            'predicted_failures': predicted_failures,
            'error_rate_estimate': error_rate,
            'financial_impact': financial_impact,
            'audit_summary': audit_summary
        }

    def _get_enrollee_population(self, contract_id: str, year: int) -> pd.DataFrame:
        """
        Build enrollee population from HCC audit trail

        Aggregates all HCCs per patient-provider to create enrollee-level view
        """

        # Get all HCCs from the past year
        start_date = f"{year - 1}-01-01"
        end_date = f"{year - 1}-12-31"

        ph = '%s' if self.db.db_type == 'postgresql' else '?'

        if self.db.db_type == 'postgresql':
            query = f"""
            SELECT
                patient_id,
                provider_id,
                COUNT(DISTINCT hcc_code) as hcc_count,
                SUM(raf_weight) as total_raf,
                SUM(CASE WHEN validation_status = 'FAIL' THEN 1 ELSE 0 END) as failed_hccs,
                ARRAY_AGG(DISTINCT hcc_category) as hcc_categories,
                ARRAY_AGG(DISTINCT hcc_code) as hcc_list,
                AVG(confidence_score) as avg_confidence,
                MIN(encounter_date) as first_encounter,
                MAX(encounter_date) as last_encounter
            FROM hcc_audit_trail
            WHERE encounter_date >= {ph}
            AND encounter_date <= {ph}
            GROUP BY patient_id, provider_id
            HAVING COUNT(DISTINCT hcc_code) >= 1
            """
        else:
            query = f"""
            SELECT
                patient_id,
                provider_id,
                COUNT(DISTINCT hcc_code) as hcc_count,
                SUM(raf_weight) as total_raf,
                SUM(CASE WHEN validation_status = 'FAIL' THEN 1 ELSE 0 END) as failed_hccs,
                GROUP_CONCAT(DISTINCT hcc_category) as hcc_categories,
                GROUP_CONCAT(DISTINCT hcc_code) as hcc_list,
                AVG(confidence_score) as avg_confidence,
                MIN(encounter_date) as first_encounter,
                MAX(encounter_date) as last_encounter
            FROM hcc_audit_trail
            WHERE encounter_date >= {ph}
            AND encounter_date <= {ph}
            GROUP BY patient_id, provider_id
            HAVING COUNT(DISTINCT hcc_code) >= 1
            """

        results = self.db.execute_query(query, (start_date, end_date), fetch="all")

        if not results:
            return pd.DataFrame()

        df = pd.DataFrame(results)

        # Handle array/concat differences
        if self.db.db_type == 'sqlite':
            df['hcc_categories'] = df['hcc_categories'].apply(
                lambda x: x.split(',') if isinstance(x, str) else (x or [])
            )
            df['hcc_list'] = df['hcc_list'].apply(
                lambda x: x.split(',') if isinstance(x, str) else (x or [])
            )
        elif 'hcc_categories' in df.columns:
            df['hcc_categories'] = df['hcc_categories'].apply(
                lambda x: list(x) if hasattr(x, '__iter__') and not isinstance(x, str) else (x or [])
            )

        return df

    def _calculate_targeting_scores(self, enrollees: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate CMS targeting probability using published factors

        Higher scores = more likely to be selected in audit sample
        """

        # Factor 1: High RAF outliers (>75th percentile)
        raf_75th = enrollees['total_raf'].quantile(0.75)
        enrollees['high_raf_score'] = (
            (enrollees['total_raf'] > raf_75th).astype(int) *
            self.targeting_weights['high_raf_outlier']
        )

        # Factor 2: Condition density (>5 HCCs per enrollee)
        enrollees['condition_density_score'] = (
            (enrollees['hcc_count'] >= 5).astype(int) *
            self.targeting_weights['condition_density']
        )

        # Factor 3: High-risk HCC categories (from Top 10 list)
        high_risk_categories = [
            'Diabetes with Complications',
            'Congestive Heart Failure',
            'COPD',
            'Chronic Kidney Disease',
            'Active Cancers'
        ]

        def has_high_risk_hcc(categories):
            if categories is None:
                return 0
            if isinstance(categories, str):
                if not categories.strip():
                    return 0
                categories = [c.strip() for c in categories.split(',')]
            elif hasattr(categories, '__iter__') and not isinstance(categories, str):
                categories = [str(c).strip() for c in categories if c is not None and str(c) not in ('nan', '')]
            else:
                return 0
            if not categories:
                return 0
            return 1 if any(cat in high_risk_categories for cat in categories) else 0

        enrollees['high_risk_score'] = (
            enrollees['hcc_categories'].apply(has_high_risk_hcc) *
            self.targeting_weights['high_risk_hccs']
        )

        # Factor 4: Provider risk (enrollee has HCCs from RED tier providers)
        red_providers = self.db.execute_query(
            "SELECT provider_id FROM provider_meat_scores WHERE risk_tier = 'RED'",
            fetch="all"
        )
        red_provider_ids = [p['provider_id'] for p in (red_providers or [])]

        def has_red_provider(provider_id):
            return provider_id in red_provider_ids

        enrollees['provider_risk_score'] = (
            enrollees['provider_id'].apply(has_red_provider).astype(int) *
            self.targeting_weights['provider_risk']
        )

        # Factor 5: Payment growth (simulated - in production would compare Y-o-Y)
        np.random.seed(hash(datetime.now().date()) % 2**32)
        enrollees['payment_growth_score'] = np.random.uniform(
            0, self.targeting_weights['payment_growth'], len(enrollees)
        )

        # Calculate composite targeting score
        enrollees['targeting_score'] = (
            enrollees['high_raf_score'] +
            enrollees['condition_density_score'] +
            enrollees['high_risk_score'] +
            enrollees['provider_risk_score'] +
            enrollees['payment_growth_score']
        )

        # Normalize to 0-100 scale
        max_score = enrollees['targeting_score'].max()
        if max_score > 0:
            enrollees['targeting_score'] = enrollees['targeting_score'] / max_score * 100

        return enrollees

    def _select_cms_sample(self,
                          enrollees: pd.DataFrame,
                          sample_size: int) -> pd.DataFrame:
        """
        Select enrollees using weighted random sampling

        CMS uses a combination of random and targeted sampling
        """

        if len(enrollees) < sample_size:
            return enrollees.copy()

        # CMS typically uses 70% weighted + 30% pure random
        weighted_sample_size = int(sample_size * 0.70)
        random_sample_size = sample_size - weighted_sample_size

        # Weighted sample (higher targeting score = higher probability)
        weights = enrollees['targeting_score'] / enrollees['targeting_score'].sum()
        weighted_sample = enrollees.sample(
            n=weighted_sample_size,
            weights=weights,
            replace=False
        ).copy()
        weighted_sample['sample_type'] = 'Targeted'

        # Pure random sample from remaining enrollees
        remaining = enrollees[~enrollees.index.isin(weighted_sample.index)]
        random_sample = remaining.sample(
            n=min(random_sample_size, len(remaining)),
            replace=False
        ).copy()
        random_sample['sample_type'] = 'Random'

        # Combine samples
        sample = pd.concat([weighted_sample, random_sample])
        sample = sample.sort_values('targeting_score', ascending=False)

        return sample

    def _predict_hcc_failures(self, sample_enrollees: pd.DataFrame) -> pd.DataFrame:
        """
        Predict which HCCs will fail validation for sampled enrollees

        Uses existing validation_status and confidence_score data
        """

        if sample_enrollees.empty:
            return pd.DataFrame()

        # Get all HCCs for sampled patients
        patient_ids = sample_enrollees['patient_id'].unique().tolist()

        ph = '%s' if self.db.db_type == 'postgresql' else '?'
        placeholders = ','.join([ph] * len(patient_ids))

        query = f"""
        SELECT
            patient_id,
            provider_id,
            hcc_code,
            hcc_description,
            hcc_category,
            raf_weight,
            validation_status,
            failure_reason,
            confidence_score,
            meat_score,
            documentation_text
        FROM hcc_audit_trail
        WHERE patient_id IN ({placeholders})
        AND validation_status IN ('FAIL', 'HUMAN_REVIEW')
        ORDER BY patient_id, raf_weight DESC
        """

        failures = self.db.execute_query(query, tuple(patient_ids), fetch="all")

        if not failures:
            return pd.DataFrame()

        failure_df = pd.DataFrame(failures)

        # Add failure probability (based on confidence score)
        failure_df['failure_probability'] = (
            100 - failure_df['confidence_score'].fillna(50)
        )

        return failure_df

    def _calculate_error_rate(self, predicted_failures: pd.DataFrame) -> float:
        """
        Calculate predicted RADV error rate

        Error Rate = (Failed RAF / Total RAF) * 100
        """

        if predicted_failures.empty:
            return 0.0

        patient_ids = predicted_failures['patient_id'].unique().tolist()

        ph = '%s' if self.db.db_type == 'postgresql' else '?'
        placeholders = ','.join([ph] * len(patient_ids))

        total_query = f"""
        SELECT SUM(raf_weight) as total_raf
        FROM hcc_audit_trail
        WHERE patient_id IN ({placeholders})
        """

        total_result = self.db.execute_query(
            total_query,
            tuple(patient_ids),
            fetch="one"
        )

        total_raf = (total_result or {}).get('total_raf') or 0
        failed_raf = predicted_failures['raf_weight'].sum()

        if total_raf == 0:
            return 0.0

        error_rate = (failed_raf / total_raf) * 100

        return round(float(error_rate), 2)

    def _calculate_financial_impact(self,
                                   error_rate: float,
                                   enrollees: pd.DataFrame,
                                   predicted_failures: pd.DataFrame) -> Dict:
        """
        Calculate estimated CMS extrapolation and penalty

        CMS extrapolates sample error rate to entire contract
        """

        # Total contract payment (all enrollees)
        total_contract_raf = enrollees['total_raf'].sum()
        total_contract_payment = total_contract_raf * self.cms_base_rate

        # Extrapolated overpayment
        extrapolated_overpayment = total_contract_payment * (error_rate / 100)

        # Sample-specific failed payment
        sample_failed_payment = (
            predicted_failures['raf_weight'].sum() * self.cms_base_rate
            if not predicted_failures.empty else 0
        )

        # CMS thresholds
        material_weakness_threshold = 0.05   # 5% error rate
        significant_deficiency_threshold = 0.10  # 10% error rate

        if error_rate >= significant_deficiency_threshold * 100:
            penalty_multiplier = 1.25  # 25% penalty
            severity = 'CRITICAL'
        elif error_rate >= material_weakness_threshold * 100:
            penalty_multiplier = 1.10  # 10% penalty
            severity = 'HIGH'
        else:
            penalty_multiplier = 1.0
            severity = 'LOW'

        total_penalty = extrapolated_overpayment * penalty_multiplier

        return {
            'error_rate': error_rate,
            'total_contract_payment': round(float(total_contract_payment), 2),
            'extrapolated_overpayment': round(float(extrapolated_overpayment), 2),
            'sample_failed_payment': round(float(sample_failed_payment), 2),
            'penalty_multiplier': penalty_multiplier,
            'total_penalty': round(float(total_penalty), 2),
            'severity': severity,
            'cms_thresholds': {
                'material_weakness': material_weakness_threshold * 100,
                'significant_deficiency': significant_deficiency_threshold * 100
            }
        }

    def _generate_audit_summary(self,
                               sample_enrollees: pd.DataFrame,
                               predicted_failures: pd.DataFrame,
                               error_rate: float,
                               financial_impact: Dict) -> Dict:
        """Generate executive summary of mock audit results"""

        if not predicted_failures.empty:
            top_categories = (
                predicted_failures.groupby('hcc_category')['raf_weight']
                .sum()
                .sort_values(ascending=False)
                .head(5)
                .to_dict()
            )

            top_providers = (
                predicted_failures.groupby('provider_id')
                .size()
                .sort_values(ascending=False)
                .head(5)
                .to_dict()
            )
        else:
            top_categories = {}
            top_providers = {}

        return {
            'audit_date': datetime.now().strftime('%Y-%m-%d'),
            'sample_size': len(sample_enrollees),
            'total_hccs_in_sample': int(sample_enrollees['hcc_count'].sum()),
            'predicted_failures': len(predicted_failures),
            'error_rate': error_rate,
            'severity': financial_impact['severity'],
            'estimated_penalty': financial_impact['total_penalty'],
            'top_failure_categories': top_categories,
            'top_failure_providers': top_providers,
            'recommendations': self._generate_recommendations(
                error_rate,
                predicted_failures
            )
        }

    def _generate_recommendations(self,
                                 error_rate: float,
                                 predicted_failures: pd.DataFrame) -> List[str]:
        """Generate actionable recommendations based on audit results"""

        recommendations = []

        if error_rate >= 10:
            recommendations.append(
                "CRITICAL: Implement immediate pre-bill audit for all HCC submissions"
            )
            recommendations.append(
                "Place all RED tier providers on mandatory documentation training"
            )
        elif error_rate >= 5:
            recommendations.append(
                "HIGH RISK: Increase spot-check audit frequency to 25% of claims"
            )
            recommendations.append(
                "Focus remediation on top 3 failure categories"
            )
        else:
            recommendations.append(
                "Continue current monitoring with quarterly spot checks"
            )

        if not predicted_failures.empty:
            # Category-specific recommendations
            top_category = (
                predicted_failures.groupby('hcc_category')
                .size()
                .idxmax()
            )
            recommendations.append(
                f"Targeted training needed for: {top_category}"
            )

            # M.E.A.T. specific recommendations
            if 'meat_score' in predicted_failures.columns:
                avg_meat_score = predicted_failures['meat_score'].mean()
                if avg_meat_score < 2:
                    recommendations.append(
                        "Deploy EMR hard-stops requiring at least 2 M.E.A.T. elements"
                    )

        return recommendations


# ==================== TESTING UTILITY ====================

if __name__ == "__main__":
    simulator = MockAuditSimulator()

    print("Running Mock RADV Audit Simulation...")
    print("=" * 60)

    results = simulator.run_mock_audit(
        contract_id="DEFAULT",
        contract_size="medium_contract",
        year=2026
    )

    print("\nAUDIT SUMMARY")
    print("=" * 60)
    summary = results['audit_summary']
    for key, value in summary.items():
        if key != 'recommendations':
            print(f"{key}: {value}")

    print("\nRECOMMENDATIONS")
    print("=" * 60)
    for rec in summary.get('recommendations', []):
        print(f"• {rec}")

    print("\nFINANCIAL IMPACT")
    print("=" * 60)
    financial = results.get('financial_impact', {})
    if financial:
        print(f"Error Rate: {financial.get('error_rate', 0)}%")
        print(f"Total Contract Payment: ${financial.get('total_contract_payment', 0):,.2f}")
        print(f"Extrapolated Overpayment: ${financial.get('extrapolated_overpayment', 0):,.2f}")
        print(f"Total Penalty: ${financial.get('total_penalty', 0):,.2f}")
        print(f"Severity: {financial.get('severity', 'N/A')}")
