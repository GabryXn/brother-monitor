# printer_client.py
from __future__ import annotations
from dataclasses import dataclass, field
import re
import requests
from bs4 import BeautifulSoup

BASE_URL = "http://localhost:60000"
TIMEOUT = 5


@dataclass
class PrinterData:
    status: str = "offline"        # idle / printing / sleep / offline / error
    status_detail: str = ""
    toner_pct: int = 0
    drum_pct: int = 0
    model: str = ""
    serial: str = ""
    firmware: str = ""
    memory_mb: int = 0
    page_count: int = 0
    avg_coverage: float = 0.0
    errors: list = field(default_factory=list)   # [{"desc": str, "page": int}]
    jams: dict = field(default_factory=dict)
    replace_counts: dict = field(default_factory=dict)
    page_stats: dict = field(default_factory=dict)


class PrinterClient:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url

    def fetch(self) -> PrinterData:
        try:
            info_resp = requests.get(
                f"{self.base_url}/general/information.html",
                params={"kind": "item"},
                timeout=TIMEOUT,
            )
            status_resp = requests.get(
                f"{self.base_url}/general/status.html",
                timeout=TIMEOUT,
            )
            data = _parse_info(info_resp.text)
            _parse_status(status_resp.text, data)
            return data
        except requests.exceptions.RequestException:
            return PrinterData(status="offline")


def _parse_info(html: str) -> PrinterData:
    data = PrinterData()
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)

    def _find(pattern: str, group: int = 1, default=None):
        m = re.search(pattern, text, re.IGNORECASE)
        return m.group(group) if m else default

    raw_model = _find(r"Model\s+Name\s+(Brother[^\n]{3,40}?)(?:\s{2,}|Serial|$)")
    if raw_model:
        data.model = re.sub(r"\s+", " ", raw_model.replace("\xa0", " ")).strip()

    data.serial = _find(r"Serial\s+no\.\s+(\S+)") or ""
    data.firmware = _find(r"Main\s+Firmware\s+Version\s+(\S+)") or ""

    mem = _find(r"Memory\s+Size\s+(\d+)\s+MB")
    if mem:
        data.memory_mb = int(mem)

    pc = _find(r"Page\s+Counter\s+(\d+)")
    if pc:
        data.page_count = int(pc)

    cov = _find(r"Average\s+Coverage[*\s]*([\d.]+)%")
    if cov:
        data.avg_coverage = float(cov)

    drum = _find(r"Drum\s+Unit[*\s]*([\d]+)%")
    if drum:
        data.drum_pct = int(drum)

    # Toner viene DOPO Drum Unit nella stessa riga — cerca "Toner** 40%" ma non "Drum"
    toner = _find(r"Toner[*\s]*([\d]+)%")
    if toner:
        data.toner_pct = int(toner)

    # Jams
    jams: dict = {}
    for key, pat in [
        ("total",  r"Total\s+Paper\s+Jams\s+(\d+)"),
        ("tray1",  r"Jam\s+Tray\s+1\s+(\d+)"),
        ("inside", r"Jam\s+Inside\s+(\d+)"),
        ("rear",   r"Jam\s+Rear\s+(\d+)"),
        ("duplex", r"Jam\s+2-sided\s+(\d+)"),
    ]:
        v = _find(pat)
        if v is not None:
            jams[key] = int(v)
    data.jams = jams

    # Replace counts
    rc_match = re.search(r"Replace\s+Count\s+Toner\s+(\d+)\s+Drum\s+Unit\s+(\d+)", text, re.IGNORECASE)
    if rc_match:
        data.replace_counts = {"toner": int(rc_match.group(1)), "drum": int(rc_match.group(2))}

    # Error history — righe tipo "1 Incepp. interno Page : 1109"
    errors = []
    for m in re.finditer(r"\d+\s+([\w\s.'àèìòùÀÈÌÒÙ.-]{3,40}?)\s+Page\s*[:\s]+(\d+)", text):
        desc = m.group(1).strip()
        page = int(m.group(2))
        if desc:
            errors.append({"desc": desc, "page": page})
    data.errors = errors[:10]

    return data


def _parse_status(html: str, data: PrinterData) -> None:
    soup = BeautifulSoup(html, "html.parser")
    moni = soup.find(class_=re.compile(r"\bmoni\b"))
    if not moni:
        return
    classes = moni.get("class", [])
    text = moni.get_text(strip=True)
    data.status_detail = text
    if any(c in classes for c in ("moniError", "moniWarn")):
        data.status = "error"
    elif "moniOk" in classes:
        low = text.lower()
        if any(k in low for k in ("print", "stampa")):
            data.status = "printing"
        elif any(k in low for k in ("sleep", "risparmio")):
            data.status = "sleep"
        else:
            data.status = "idle"
