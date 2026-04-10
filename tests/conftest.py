import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# HTML campione fedele alla stampante reale (estratto da localhost:60000)
INFO_HTML_FIXTURE = """
<html><body>
<dl class="items">
<dt>Model Name</dt><dd>Brother&nbsp;DCP-L2550DN&nbsp;series</dd>
<dt>Serial no.</dt><dd>E78283F1N254602</dd>
<dt>Main Firmware Version</dt><dd>ZF</dd>
<dt>Memory Size</dt><dd>128 MB</dd>
<dt>Page Counter</dt><dd>1472</dd>
<dt>Average Coverage****</dt><dd>8.26%</dd>
<dt>Remaining Life</dt>
<dd>Drum Unit* 88% Toner** 40%</dd>
<dt>Total Paper Jams</dt><dd>2</dd>
<dt>Jam Tray 1</dt><dd>1</dd>
<dt>Jam Inside</dt><dd>1</dd>
<dt>Jam Rear</dt><dd>0</dd>
<dt>Jam 2-sided</dt><dd>0</dd>
<dt>Replace Count</dt><dd>Toner 1 Drum Unit 0</dd>
<dt>Error History(last 10 errors)</dt>
<dd>1 Incepp. interno Page : 1109</dd>
<dd>2 Sostit. toner Page : 559</dd>
<dd>3 Toner insuff. Page : 432</dd>
</dl>
</body></html>
"""

STATUS_HTML_OK = """
<html><body>
<span class="moni moniOk">Risparmio</span>
</body></html>
"""

STATUS_HTML_IDLE = """
<html><body>
<span class="moni moniOk">Pronto</span>
</body></html>
"""

STATUS_HTML_ERROR = """
<html><body>
<span class="moni moniError">Errore carta</span>
</body></html>
"""
