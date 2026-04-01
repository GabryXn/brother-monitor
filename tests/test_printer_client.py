# tests/test_printer_client.py
import pytest
from printer_client import _parse_info, _parse_status, PrinterData
from tests.conftest import INFO_HTML_FIXTURE, STATUS_HTML_OK, STATUS_HTML_IDLE, STATUS_HTML_ERROR


def test_parse_info_toner_drum():
    data = _parse_info(INFO_HTML_FIXTURE)
    assert data.toner_pct == 40
    assert data.drum_pct == 88


def test_parse_info_device_info():
    data = _parse_info(INFO_HTML_FIXTURE)
    assert "DCP-L2550DN" in data.model
    assert data.serial == "E78283F1N254602"
    assert data.firmware == "ZF"
    assert data.memory_mb == 128


def test_parse_info_counters():
    data = _parse_info(INFO_HTML_FIXTURE)
    assert data.page_count == 1472
    assert data.avg_coverage == pytest.approx(8.26)


def test_parse_info_jams():
    data = _parse_info(INFO_HTML_FIXTURE)
    assert data.jams["total"] == 2
    assert data.jams["tray1"] == 1
    assert data.jams["inside"] == 1
    assert data.jams["rear"] == 0


def test_parse_info_replace_counts():
    data = _parse_info(INFO_HTML_FIXTURE)
    assert data.replace_counts["toner"] == 1
    assert data.replace_counts["drum"] == 0


def test_parse_info_errors():
    data = _parse_info(INFO_HTML_FIXTURE)
    assert len(data.errors) >= 2
    descs = [e["desc"] for e in data.errors]
    assert any("Incepp" in d for d in descs)


def test_parse_status_sleep():
    data = PrinterData()
    _parse_status(STATUS_HTML_OK, data)
    assert data.status == "sleep"
    assert "Risparmio" in data.status_detail


def test_parse_status_idle():
    data = PrinterData()
    _parse_status(STATUS_HTML_IDLE, data)
    assert data.status == "idle"


def test_parse_status_error():
    data = PrinterData()
    _parse_status(STATUS_HTML_ERROR, data)
    assert data.status == "error"
