import pytest
from unittest.mock import patch, MagicMock
from drivers.snmp import SNMPDriver


def _make_driver():
    return SNMPDriver(host="192.168.1.1", community="public")


def _mock_get_oid(values: dict):
    """Return a side_effect function for SNMPDriver._get_oid."""
    def _impl(oid: str):
        return values.get(oid)
    return _impl


def test_fetch_idle_with_toner_and_drum():
    driver = _make_driver()
    oid_values = {
        "1.3.6.1.2.1.43.11.1.1.9.1.1": 400,
        "1.3.6.1.2.1.43.11.1.1.8.1.1": 1000,
        "1.3.6.1.2.1.43.11.1.1.9.1.2": 880,
        "1.3.6.1.2.1.43.11.1.1.8.1.2": 1000,
        "1.3.6.1.2.1.25.3.5.1.1.1":    3,
    }
    with patch.object(driver, "_get_oid", side_effect=_mock_get_oid(oid_values)):
        data = driver.fetch()
    assert data.toner_pct == 40
    assert data.drum_pct == 88
    assert data.status == "idle"


def test_fetch_printing_status():
    driver = _make_driver()
    oid_values = {
        "1.3.6.1.2.1.43.11.1.1.9.1.1": 500,
        "1.3.6.1.2.1.43.11.1.1.8.1.1": 1000,
        "1.3.6.1.2.1.43.11.1.1.9.1.2": 900,
        "1.3.6.1.2.1.43.11.1.1.8.1.2": 1000,
        "1.3.6.1.2.1.25.3.5.1.1.1":    4,
    }
    with patch.object(driver, "_get_oid", side_effect=_mock_get_oid(oid_values)):
        data = driver.fetch()
    assert data.status == "printing"


def test_fetch_offline_on_exception():
    driver = _make_driver()
    with patch.object(driver, "_get_oid", side_effect=Exception("timeout")):
        data = driver.fetch()
    assert data.status == "offline"


def test_fetch_drum_unlimited():
    """When drum max is -1 (unlimited), drum_pct should be 100."""
    driver = _make_driver()
    oid_values = {
        "1.3.6.1.2.1.43.11.1.1.9.1.1": 400,
        "1.3.6.1.2.1.43.11.1.1.8.1.1": 1000,
        "1.3.6.1.2.1.43.11.1.1.9.1.2": -1,
        "1.3.6.1.2.1.43.11.1.1.8.1.2": -1,
        "1.3.6.1.2.1.25.3.5.1.1.1":    3,
    }
    with patch.object(driver, "_get_oid", side_effect=_mock_get_oid(oid_values)):
        data = driver.fetch()
    assert data.drum_pct == 100
