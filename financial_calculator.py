# financial_calculator.py
"""
Feature 1.3: Financial Impact Calculator
Real-time financial risk calculation, remediation ROI, and scenario analysis.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from database import get_db_manager


class FinancialImpactCalculator:
    """
    Real-time financial risk calculation and forecasting

    Calculates:
    1. Current exposure from unvalidated HCCs
    2. Projected annual impact at current validation rates
    3. ROI from remediation efforts
    4. Star Rating financial impact from RADV failures
    """

    def __init__(self):
        self.db = get_db_manager()

        # CMS payment rates (2026 estimates)
        self.base_rate = 1142.50
        self.quality_bonus_rates = {
            5.0: 1.05,  # 5-star = 5% bonus
            4.5: 1.03,  # 4.5-star = 3% bonus
            4.0: 1.00,  # 4-star = no bonus
            3.5: 0.98,  # 3.5-star = 2% penalty
            3.0: 0.95   # 3-star = 5% penalty
        }

        # Cost assumptions
        self.coder_hourly_rate = 75.00
        self.minutes_per_chart_review = 15
        self.training_cost_per_provider = 500.00

    def calculate_current_exposure(self,
                                   contract_id: Optional[str] = None,
                                   lookback_months: int = 12) -> Dict:
        """
        Calculate current financial exposure from validation failures

        Returns real-time risk metrics
        """

        cutoff_date = datetime.now() - timedelta(days=lookback_months * 30)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d')

        ph = '%s' if self.db.db_type == 'postgresql' else '?'

        # Get all failed HCCs
        query = f"""
        SELECT
            SUM(raf_weight) as total_failed_raf,
            COUNT(*) as total_failed_hccs,
            COUNT(DISTINCT provider_id) as providers_with_failures,
            COUNT(DISTINCT patient_id) as patients_affected
        FROM hcc_audit_trail
        WHERE validation_status = 'FAIL'
        AND encounter_date >= {ph}
        """

        result = self.db.execute_query(query, (cutoff_str,), fetch="one")
        result = result or {}

        failed_raf = result.get('total_failed_raf') or 0
        current_exposure = float(failed_raf) * self.base_rate

        # Get validation rate for projection
        rate_query = f"""
        SELECT
            COUNT(*) as total_hccs,
            SUM(CASE WHEN validation_status = 'PASS' THEN 1 ELSE 0 END) as passed_hccs
        FROM hcc_audit_trail
        WHERE encounter_date >= {ph}
        """

        rate_result = self.db.execute_query(rate_query, (cutoff_str,), fetch="one")
        rate_result = rate_result or {}

        total_hccs = rate_result.get('total_hccs') or 0
        passed_hccs = rate_result.get('passed_hccs') or 0

        current_validation_rate = (passed_hccs / total_hccs * 100) if total_hccs > 0 else 0

        # Annualized projection
        annualized_exposure = current_exposure * (12 / lookback_months)

        return {
            'current_exposure': round(current_exposure, 2),
            'annualized_exposure': round(annualized_exposure, 2),
            'total_failed_hccs': result.get('total_failed_hccs', 0),
            'total_failed_raf': round(float(failed_raf), 3),
            'providers_affected': result.get('providers_with_failures', 0),
            'patients_affected': result.get('patients_affected', 0),
            'current_validation_rate': round(current_validation_rate, 2),
            'lookback_period_months': lookback_months
        }

    def calculate_remediation_roi(self,
                                  provider_ids: Optional[List[str]] = None,
                                  target_validation_rate: float = 95.0) -> Dict:
        """
        Calculate ROI from investing in provider education and auditing

        Compares cost of remediation vs. avoided penalties
        """

        # Get current provider scores
        if provider_ids:
            ph = '%s' if self.db.db_type == 'postgresql' else '?'
            placeholders = ','.join([ph] * len(provider_ids))

            query = f"""
            SELECT provider_id, validation_rate, financial_risk_estimate, risk_tier
            FROM provider_meat_scores
            WHERE provider_id IN ({placeholders})
            """
            providers = self.db.execute_query(query, tuple(provider_ids), fetch="all")
        else:
            ph = '%s' if self.db.db_type == 'postgresql' else '?'

            query = f"""
            SELECT provider_id, validation_rate, financial_risk_estimate, risk_tier
            FROM provider_meat_scores
            WHERE validation_rate < {ph}
            """
            providers = self.db.execute_query(query, (target_validation_rate,), fetch="all")

        if not providers:
            return {
                'total_investment': 0,
                'training_cost': 0,
                'audit_cost': 0,
                'current_risk': 0,
                'post_remediation_risk': 0,
                'total_savings': 0,
                'net_roi': 0,
                'roi_percentage': 0,
                'providers_remediated': 0,
                'tier_breakdown': {},
                'payback_period_months': float('inf')
            }

        provider_df = pd.DataFrame(providers)

        # Calculate costs
        num_providers = len(provider_df)

        # Training costs
        training_cost = num_providers * self.training_cost_per_provider

        # Pre-bill audit costs (estimate 20% of charts need review)
        total_risk = provider_df['financial_risk_estimate'].fillna(0).sum()
        total_hccs_to_review = (total_risk / self.base_rate) * 0.20
        review_hours = (total_hccs_to_review * self.minutes_per_chart_review) / 60
        audit_cost = review_hours * self.coder_hourly_rate

        total_investment = training_cost + audit_cost

        # Calculate savings - assume remediation brings providers toward target rate
        avg_current_rate = provider_df['validation_rate'].fillna(0).mean()
        improvement_factor = (target_validation_rate / avg_current_rate) if avg_current_rate > 0 else 1

        post_remediation_risk = total_risk / improvement_factor
        total_savings = total_risk - post_remediation_risk

        net_roi = total_savings - total_investment
        roi_percentage = (net_roi / total_investment * 100) if total_investment > 0 else 0

        # Breakdown by provider tier
        tier_breakdown = {}
        if not provider_df.empty and 'risk_tier' in provider_df.columns:
            agg_df = provider_df.groupby('risk_tier').agg(
                provider_count=('provider_id', 'count'),
                tier_risk=('financial_risk_estimate', 'sum')
            )
            tier_breakdown = agg_df.to_dict('index')

        payback = (total_investment / (total_savings / 12)) if total_savings > 0 else float('inf')

        return {
            'total_investment': round(float(total_investment), 2),
            'training_cost': round(float(training_cost), 2),
            'audit_cost': round(float(audit_cost), 2),
            'current_risk': round(float(total_risk), 2),
            'post_remediation_risk': round(float(post_remediation_risk), 2),
            'total_savings': round(float(total_savings), 2),
            'net_roi': round(float(net_roi), 2),
            'roi_percentage': round(float(roi_percentage), 1),
            'providers_remediated': num_providers,
            'tier_breakdown': tier_breakdown,
            'payback_period_months': round(float(payback), 1) if payback != float('inf') else payback
        }

    def calculate_star_rating_impact(self,
                                    current_star_rating: float,
                                    radv_error_rate: float,
                                    total_members: int) -> Dict:
        """
        Calculate how RADV failures could impact Star Ratings and revenue

        RADV failures can trigger compliance audits that affect Star Ratings
        """

        # RADV error rates can trigger downgrades
        if radv_error_rate >= 10:
            star_downgrade = 0.5
        elif radv_error_rate >= 5:
            star_downgrade = 0.0  # Monitored but not downgraded
        else:
            star_downgrade = 0.0

        projected_star_rating = max(3.0, current_star_rating - star_downgrade)

        # Calculate revenue impact
        current_bonus = self.quality_bonus_rates.get(current_star_rating, 1.0)
        projected_bonus = self.quality_bonus_rates.get(projected_star_rating, 1.0)

        # Average RAF per member (estimate)
        avg_raf_per_member = 1.05

        current_revenue = total_members * avg_raf_per_member * self.base_rate * current_bonus
        projected_revenue = total_members * avg_raf_per_member * self.base_rate * projected_bonus

        revenue_impact = current_revenue - projected_revenue

        return {
            'current_star_rating': current_star_rating,
            'projected_star_rating': projected_star_rating,
            'star_downgrade': star_downgrade,
            'radv_error_rate': radv_error_rate,
            'current_bonus_multiplier': current_bonus,
            'projected_bonus_multiplier': projected_bonus,
            'current_annual_revenue': round(float(current_revenue), 2),
            'projected_annual_revenue': round(float(projected_revenue), 2),
            'annual_revenue_impact': round(float(revenue_impact), 2),
            'total_members': total_members
        }

    def scenario_analysis(self,
                         scenarios: List[Dict]) -> pd.DataFrame:
        """
        Run multiple what-if scenarios

        Args:
            scenarios: List of dicts with keys:
                - name: str
                - validation_rate: float
                - remediation_investment: float

        Returns DataFrame comparing scenarios
        """

        results = []

        # Get baseline metrics
        baseline = self.calculate_current_exposure(lookback_months=12)

        for scenario in scenarios:
            name = scenario['name']
            target_rate = scenario['validation_rate']
            investment = scenario.get('remediation_investment', 0)

            # Calculate impact of reaching target rate
            current_rate = baseline['current_validation_rate']
            rate_improvement = target_rate - current_rate

            # Estimate risk reduction
            risk_reduction_factor = (rate_improvement / current_rate) if current_rate > 0 else 0
            risk_reduction = baseline['current_exposure'] * risk_reduction_factor

            net_impact = risk_reduction - investment
            roi_pct = (net_impact / investment * 100) if investment > 0 else 0

            results.append({
                'scenario': name,
                'target_validation_rate': target_rate,
                'investment_required': investment,
                'risk_reduction': risk_reduction,
                'net_impact': net_impact,
                'roi_percentage': roi_pct
            })

        return pd.DataFrame(results)

    def generate_executive_summary(self,
                                   contract_id: Optional[str] = None,
                                   lookback_months: int = 12) -> Dict:
        """
        Generate comprehensive financial summary for executive reporting
        """

        exposure = self.calculate_current_exposure(contract_id, lookback_months)

        # Get provider-level aggregations
        provider_query = """
        SELECT risk_tier, COUNT(*) as provider_count, SUM(financial_risk_estimate) as tier_risk
        FROM provider_meat_scores
        GROUP BY risk_tier
        """
        tier_data = self.db.execute_query(provider_query, fetch="all")
        tier_df = pd.DataFrame(tier_data) if tier_data else pd.DataFrame()

        # ROI calculation for RED tier providers
        red_providers_query = "SELECT provider_id FROM provider_meat_scores WHERE risk_tier = 'RED'"
        red_results = self.db.execute_query(red_providers_query, fetch="all")
        red_provider_ids = [r['provider_id'] for r in (red_results or [])]

        if red_provider_ids:
            roi = self.calculate_remediation_roi(red_provider_ids, target_validation_rate=90.0)
        else:
            roi = {'net_roi': 0, 'roi_percentage': 0, 'total_investment': 0}

        return {
            'summary_date': datetime.now().strftime('%Y-%m-%d'),
            'lookback_period_months': lookback_months,
            'current_exposure': exposure,
            'tier_breakdown': tier_df.to_dict('records') if not tier_df.empty else [],
            'recommended_remediation': roi,
            'key_metrics': {
                'total_at_risk': exposure['annualized_exposure'],
                'providers_needing_action': len(red_provider_ids),
                'potential_roi': roi.get('roi_percentage', 0),
                'recommended_investment': roi.get('total_investment', 0)
            }
        }


# ==================== TESTING UTILITY ====================

if __name__ == "__main__":
    calc = FinancialImpactCalculator()

    print("FINANCIAL IMPACT ANALYSIS")
    print("=" * 60)

    # Current exposure
    print("\nCurrent Exposure")
    exposure = calc.calculate_current_exposure(lookback_months=12)
    print(f"Current Risk: ${exposure['current_exposure']:,.2f}")
    print(f"Annualized: ${exposure['annualized_exposure']:,.2f}")
    print(f"Validation Rate: {exposure['current_validation_rate']}%")

    # ROI Analysis
    print("\nRemediation ROI")
    roi = calc.calculate_remediation_roi(target_validation_rate=95.0)
    print(f"Investment Required: ${roi['total_investment']:,.2f}")
    print(f"Expected Savings: ${roi['total_savings']:,.2f}")
    print(f"Net ROI: ${roi['net_roi']:,.2f}")
    print(f"ROI Percentage: {roi['roi_percentage']}%")
    pb = roi['payback_period_months']
    print(f"Payback Period: {pb} months" if pb != float('inf') else "Payback Period: N/A")

    # Scenario Analysis
    print("\nScenario Analysis")
    scenarios = [
        {'name': 'Status Quo', 'validation_rate': exposure['current_validation_rate'], 'remediation_investment': 0},
        {'name': 'Target 90%', 'validation_rate': 90.0, 'remediation_investment': 50000},
        {'name': 'Target 95%', 'validation_rate': 95.0, 'remediation_investment': 100000},
    ]

    scenario_results = calc.scenario_analysis(scenarios)
    print(scenario_results.to_string(index=False))
