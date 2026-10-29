import pytest
from eval.run_security import run_security_suite


def test_red_team_s1_to_s10_zero_leakage(db_session):
    """
    Executes the comprehensive automated S1-S10 red-team security harness.
    Asserts ZERO data leakage across all personas and attack vectors.
    """
    summary = run_security_suite(db=db_session)
    assert summary["zero_leakage_guarantee_met"] is True, f"Security leakage detected: {summary['cases']}"
    assert summary["leaked_cases"] == 0
    assert summary["passed_cases"] == summary["total_cases"]
    assert summary["pass_rate_pct"] == 100.0
