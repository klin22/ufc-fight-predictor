import pytest

from ufc_forecast.probability import american_probabilities


def test_positive_american_odds():
    assert american_probabilities(200) == pytest.approx(1 / 3)


def test_negative_american_odds():
    assert american_probabilities(-200) == pytest.approx(2 / 3)


def test_even_money():
    assert american_probabilities(100) == pytest.approx(0.5)
