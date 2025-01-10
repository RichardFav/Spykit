# module import
import os
import sys
import time
from PyQt5.QtWidgets import QApplication

if __name__ == '__main__':
    # sets the windows style (if on Subiculum)
    if sys.platform == 'linux':
        QApplication.setStyle('windows')

    # runs the analysis GUIs
    app = QApplication([])
    time.sleep(0.5)
    h_main = main_analysis.AnalysisGUI()
    time.sleep(0.5)
    app.exec()