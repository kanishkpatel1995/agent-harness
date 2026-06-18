"""Tests for the Budget / kill switch."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from harness.budget import Budget, BudgetExceeded


def test_step_cap():
    b = Budget(max_steps=2)
    b.check_step()
    b.check_step()
    with pytest.raises(BudgetExceeded):
        b.check_step()


def test_token_cap():
    b = Budget(max_tokens=100)
    with pytest.raises(BudgetExceeded):
        b.record_usage({"prompt_tokens": 90, "completion_tokens": 20}, "fake")


def test_cost_cap():
    b = Budget(max_usd=0.001)
    with pytest.raises(BudgetExceeded):
        b.record_usage({"prompt_tokens": 100000, "completion_tokens": 100000}, "gpt-4o")


def test_cost_accumulates():
    b = Budget(max_usd=100)
    b.record_usage({"prompt_tokens": 1000, "completion_tokens": 1000}, "gpt-4o-mini")
    assert b.usd > 0
    assert b.total_tokens == 2000
