from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap
import sys
app = QApplication(sys.argv)
svg = open('Printer--Streamline-Plump.svg').read()
svg = svg.replace('#000000', '#4caf50')
pm = QPixmap()
res = pm.loadFromData(svg.encode('utf-8'))
print('LOAD SVG RESULT:', res)
