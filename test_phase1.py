# test_phase1.py
"""
Phase 1 integration tests
"""
import os
import tempfile

import pytest

from database import DatabaseManager
from financial_calculator import FinancialImpactCalculator
from meat_validator import MEATValidator
from mock_audit_simulator import MockAuditSimulator


@pytest.fixture
def db():
    """Create test database with temp SQLite file (persists across connections)"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        db = DatabaseManager(db_type="sqlite", connection_string=db_path)
        db.initialize_schema()
        db.seed_demo_data()
        yield db
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_provider_scores(db):
    """Test provider scorecard query"""
    scores = db.get_provider_scores(lookback_months=12)
    assert not scores.empty
    assert 'validation_rate' in scores.columns
    assert scores['validation_rate'].min() >= 0
    assert scores['validation_rate'].max() <= 100


@pytest.mark.skip(reason="Requires ANTHROPIC_API_KEY and makes API call")
def test_meat_validator():
    """Test M.E.A.T. validation (integration - requires API key)"""
    validator = MEATValidator()

    result = validator.validate_hcc_documentation(
        hcc_code="HCC 226",
        diagnosis="Congestive Heart Failure",
        documentation="CHF: Patient reports dyspnea. BNP 350 reviewed. Stable on Lasix 40mg.",
        encounter_date="2026-01-15"
    )

    assert result['validation_status'] in ['PASS', 'FAIL', 'HUMAN_REVIEW']
    assert 0 <= result['confidence_score'] <= 100
    assert 0 <= result['meat_score'] <= 4


def test_mock_audit_simulator(db, monkeypatch):
    """Test mock audit simulation"""
    monkeypatch.setattr("mock_audit_simulator.get_db_manager", lambda: db)
    simulator = MockAuditSimulator()

    results = simulator.run_mock_audit(contract_size="medium_contract", year=2026)

    assert 'audit_summary' in results
    assert 'financial_impact' in results
    if results.get('financial_impact'):
        assert results['financial_impact'].get('error_rate', 0) >= 0


def test_financial_calculator(db, monkeypatch):
    """Test financial calculations"""
    monkeypatch.setattr("financial_calculator.get_db_manager", lambda: db)
    calc = FinancialImpactCalculator()

    exposure = calc.calculate_current_exposure(lookback_months=12)

    assert exposure['current_exposure'] >= 0
    assert 0 <= exposure['current_validation_rate'] <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
