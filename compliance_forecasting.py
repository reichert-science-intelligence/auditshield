"""
Compliance Forecasting - Predictive analytics for validation trends
Forecast future validation rates, predict RADV error rates, scenario planning
"""
import json
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime, timedelta

from database import get_db_manager
from sklearn.linear_model import LinearRegression


class ComplianceForecaster:
    """
    Predictive analytics for compliance trends

    Features:
    1. Forecast future validation rates
    2. Predict RADV error rates
    3. Identify trend reversals early
    4. Scenario planning
    """

    def __init__(self):
        self.db = get_db_manager()

    def generate_forecast(
        self,
        forecast_periods: int = 12,
        confidence_level: float = 0.95,
    ) -> Dict:
        """
        Generate compliance forecast for next N months

        Uses historical validation rates to predict future performance
        """
        historical_data = self._get_historical_metrics(lookback_months=24)

        if historical_data.empty or len(historical_data) < 6:
            return {"error": "Insufficient historical data"}

        # Prepare features
        X = np.array(range(len(historical_data))).reshape(-1, 1)
        y_validation = historical_data["validation_rate"].values
        y_error = historical_data["error_rate"].values

        # Fit models
        model_validation = LinearRegression()
        model_validation.fit(X, y_validation)

        model_error = LinearRegression()
        model_error.fit(X, y_error)

        # Generate forecasts
        n_historical = len(historical_data)
        future_X = np.array(
            range(n_historical, n_historical + forecast_periods)
        ).reshape(-1, 1)

        forecast_validation = model_validation.predict(future_X)
        forecast_error = model_error.predict(future_X)

        # Calculate confidence intervals
        residuals_validation = y_validation - model_validation.predict(X)
        std_validation = np.std(residuals_validation) or 1e-6

        z_score = 1.96 if confidence_level == 0.95 else 2.576
        margin = z_score * std_validation

        # Build forecast dataframe
        forecast_dates = [
            (datetime.now() + timedelta(days=30 * i)).strftime("%Y-%m-%d")
            for i in range(1, forecast_periods + 1)
        ]

        forecasts = []
        for i, date in enumerate(forecast_dates):
            forecast_record = {
                "forecast_date": date,
                "forecast_period": f"Month +{i + 1}",
                "predicted_validation_rate": round(float(forecast_validation[i]), 2),
                "predicted_error_rate": round(float(forecast_error[i]), 2),
                "confidence_interval_low": round(
                    float(forecast_validation[i]) - margin, 2
                ),
                "confidence_interval_high": round(
                    float(forecast_validation[i]) + margin, 2
                ),
                "trend_direction": self._determine_trend(
                    forecast_validation, i
                ),
            }

            financial_impact = self._calculate_predicted_impact(
                float(forecast_error[i])
            )
            forecast_record["predicted_financial_impact"] = round(
                financial_impact, 2
            )

            forecast_record["key_drivers"] = self._identify_trend_drivers(
                historical_data
            )

            forecasts.append(forecast_record)
            self._save_forecast(forecast_record)

        return {
            "forecasts": forecasts,
            "model_accuracy": round(
                model_validation.score(X, y_validation) * 100, 2
            ),
            "trend_summary": self._generate_trend_summary(forecasts),
        }

    def _get_historical_metrics(self, lookback_months: int) -> pd.DataFrame:
        """Get historical validation metrics by month"""
        cutoff_date = (
            datetime.now() - timedelta(days=lookback_months * 30)
        ).strftime("%Y-%m-%d")

        param_placeholder = "%s" if self.db.db_type == "postgresql" else "?"

        if self.db.db_type == "postgresql":
            query = f"""
            SELECT
                DATE_TRUNC('month', encounter_date)::date as month,
                COUNT(*) as total_hccs,
                SUM(CASE WHEN validation_status = 'PASS' THEN 1 ELSE 0 END) as passed_hccs,
                ROUND(100.0 * SUM(CASE WHEN validation_status = 'PASS' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) as validation_rate,
                ROUND(100.0 * SUM(CASE WHEN validation_status = 'FAIL' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) as error_rate
            FROM hcc_audit_trail
            WHERE encounter_date >= {param_placeholder}
            GROUP BY DATE_TRUNC('month', encounter_date)
            ORDER BY month
            """
        else:
            query = f"""
            SELECT
                strftime('%Y-%m', encounter_date) as month,
                COUNT(*) as total_hccs,
                SUM(CASE WHEN validation_status = 'PASS' THEN 1 ELSE 0 END) as passed_hccs,
                ROUND(100.0 * SUM(CASE WHEN validation_status = 'PASS' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) as validation_rate,
                ROUND(100.0 * SUM(CASE WHEN validation_status = 'FAIL' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) as error_rate
            FROM hcc_audit_trail
            WHERE encounter_date >= {param_placeholder}
            GROUP BY strftime('%Y-%m', encounter_date)
            ORDER BY month
            """

        results = self.db.execute_query(query, (cutoff_date,), fetch="all")

        if not results:
            return pd.DataFrame()

        return pd.DataFrame(results)

    def _determine_trend(
        self, forecast_values: np.ndarray, current_index: int
    ) -> str:
        """Determine if trend is improving, declining, or stable"""
        if current_index == 0:
            return "INITIAL"

        current = forecast_values[current_index]
        previous = forecast_values[current_index - 1]
        change = current - previous

        if change > 1:
            return "IMPROVING"
        elif change < -1:
            return "DECLINING"
        else:
            return "STABLE"

    def _calculate_predicted_impact(self, error_rate: float) -> float:
        """Calculate predicted financial impact from error rate"""
        avg_contract_payment = 5_000_000
        return (error_rate / 100) * avg_contract_payment

    def _identify_trend_drivers(
        self, historical_data: pd.DataFrame
    ) -> List[str]:
        """Identify factors driving the trend"""
        drivers = []
        recent_data = historical_data.tail(3)

        if len(recent_data) >= 2:
            rates = recent_data["validation_rate"].dropna()
            if len(rates) >= 2:
                trend = rates.diff().mean()
                if trend > 0:
                    drivers.append("Improving provider training")
                elif trend < 0:
                    drivers.append("Documentation quality declining")
                else:
                    drivers.append("Stable performance")

        if len(recent_data) >= 3:
            volatility = recent_data["validation_rate"].std()
            if pd.notna(volatility) and volatility > 5:
                drivers.append("High variability in coding quality")

        return drivers if drivers else ["Insufficient data for drivers"]

    def _generate_trend_summary(self, forecasts: List[Dict]) -> Dict:
        """Generate executive summary of forecast trends"""
        first_forecast = forecasts[0]
        last_forecast = forecasts[-1]

        validation_change = (
            last_forecast["predicted_validation_rate"]
            - first_forecast["predicted_validation_rate"]
        )
        error_change = (
            last_forecast["predicted_error_rate"]
            - first_forecast["predicted_error_rate"]
        )

        last_error = last_forecast["predicted_error_rate"]
        if last_error > 5:
            breach_risk = "HIGH"
        elif last_error > 3:
            breach_risk = "MEDIUM"
        else:
            breach_risk = "LOW"

        return {
            "forecast_horizon_months": len(forecasts),
            "validation_rate_trajectory": (
                "IMPROVING"
                if validation_change > 0
                else "DECLINING"
                if validation_change < 0
                else "STABLE"
            ),
            "validation_rate_change": round(validation_change, 2),
            "error_rate_change": round(error_change, 2),
            "breach_risk": breach_risk,
        }

    def _save_forecast(self, forecast_record: Dict):
        """Save forecast to database"""
        param_placeholder = "%s" if self.db.db_type == "postgresql" else "?"

        key_drivers = forecast_record["key_drivers"]
        if self.db.db_type == "sqlite":
            key_drivers = json.dumps(key_drivers)

        query = f"""
        INSERT INTO compliance_forecasts (
            forecast_date, forecast_period, predicted_validation_rate,
            predicted_error_rate, predicted_financial_impact,
            confidence_interval_low, confidence_interval_high,
            trend_direction, key_drivers, forecast_model_version
        ) VALUES (
            {param_placeholder}, {param_placeholder}, {param_placeholder},
            {param_placeholder}, {param_placeholder}, {param_placeholder},
            {param_placeholder}, {param_placeholder}, {param_placeholder}, 'v1.0'
        )
        """

        self.db.execute_query(
            query,
            (
                forecast_record["forecast_date"],
                forecast_record["forecast_period"],
                forecast_record["predicted_validation_rate"],
                forecast_record["predicted_error_rate"],
                forecast_record["predicted_financial_impact"],
                forecast_record["confidence_interval_low"],
                forecast_record["confidence_interval_high"],
                forecast_record["trend_direction"],
                key_drivers,
            ),
            fetch="none",
        )

    def get_forecast_dashboard(self) -> Dict:
        """Get latest forecast for dashboard display"""
        if self.db.db_type == "postgresql":
            query = """
            SELECT *
            FROM compliance_forecasts
            WHERE created_at = (SELECT MAX(created_at) FROM compliance_forecasts)
            ORDER BY forecast_date
            LIMIT 12
            """
        else:
            query = """
            SELECT *
            FROM compliance_forecasts
            WHERE created_at = (SELECT MAX(created_at) FROM compliance_forecasts)
            ORDER BY forecast_date
            LIMIT 12
            """

        forecasts = self.db.execute_query(query, fetch="all")

        if not forecasts:
            return {"status": "NO_FORECAST_AVAILABLE"}

        return {
            "latest_forecast_date": forecasts[0].get("created_at"),
            "forecast_periods": len(forecasts),
            "forecasts": forecasts,
        }


if __name__ == "__main__":
    forecaster = ComplianceForecaster()

    print("Generating Compliance Forecast...")
    forecast = forecaster.generate_forecast(forecast_periods=12)

    if "error" not in forecast:
        print("\nForecast Summary:")
        print(f"   Model Accuracy: {forecast['model_accuracy']}%")
        print(
            f"   Trajectory: {forecast['trend_summary']['validation_rate_trajectory']}"
        )
        print(
            f"   Validation Rate Change: {forecast['trend_summary']['validation_rate_change']:+.2f}%"
        )
        print(f"   Breach Risk: {forecast['trend_summary']['breach_risk']}")

        print("\nNext 3 Months Forecast:")
        for f in forecast["forecasts"][:3]:
            print(
                f"   {f['forecast_period']}: {f['predicted_validation_rate']:.1f}% validation ({f['trend_direction']})"
            )
    else:
        print(f"   Error: {forecast['error']}")
