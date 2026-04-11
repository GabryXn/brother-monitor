# drivers/snmp.py
from __future__ import annotations

from drivers.base import PrinterData, PrinterDriver

# Standard Printer MIB v2 OIDs (RFC 3805)
_OID_TONER_LEVEL    = "1.3.6.1.2.1.43.11.1.1.9.1.1"
_OID_TONER_MAX      = "1.3.6.1.2.1.43.11.1.1.8.1.1"
_OID_DRUM_LEVEL     = "1.3.6.1.2.1.43.11.1.1.9.1.2"
_OID_DRUM_MAX       = "1.3.6.1.2.1.43.11.1.1.8.1.2"
_OID_PRINTER_STATUS = "1.3.6.1.2.1.25.3.5.1.1.1"

# hrPrinterStatus values
_HR_STATUS = {3: "idle", 4: "printing", 5: "sleep"}


def _pct(level: int | None, max_val: int | None) -> int:
    """Convert raw level/max to percentage. -1 max means unlimited (return 100)."""
    if level is None or max_val is None:
        return 0
    if max_val <= 0:          # -1 = unlimited supply
        return 100
    return max(0, min(100, round(level * 100 / max_val)))


class SNMPDriver(PrinterDriver):
    """Driver for any printer that supports the standard Printer MIB via SNMP v2c."""

    def __init__(self, host: str, community: str = "public", port: int = 161):
        self.host      = host
        self.community = community
        self.port      = port

    def _get_oid(self, oid: str) -> int | None:
        """Perform a single SNMP GET and return the integer value, or None on error."""
        from pysnmp.hlapi import (
            getCmd, SnmpEngine, CommunityData, UdpTransportTarget,
            ContextData, ObjectType, ObjectIdentity,
        )
        error_indication, error_status, _, var_binds = next(
            getCmd(
                SnmpEngine(),
                CommunityData(self.community),
                UdpTransportTarget((self.host, self.port), timeout=3, retries=1),
                ContextData(),
                ObjectType(ObjectIdentity(oid)),
            )
        )
        if error_indication or error_status or not var_binds:
            return None
        return int(var_binds[0][1])

    def fetch(self) -> PrinterData:
        try:
            toner_level = self._get_oid(_OID_TONER_LEVEL)
            toner_max   = self._get_oid(_OID_TONER_MAX)
            drum_level  = self._get_oid(_OID_DRUM_LEVEL)
            drum_max    = self._get_oid(_OID_DRUM_MAX)
            hr_status   = self._get_oid(_OID_PRINTER_STATUS)

            data = PrinterData()
            data.toner_pct = _pct(toner_level, toner_max)
            data.drum_pct  = _pct(drum_level,  drum_max)
            data.status    = _HR_STATUS.get(hr_status, "idle") if hr_status else "idle"
            return data
        except Exception:
            return PrinterData(status="offline")
