# custom module imports
import spike_pipeline.common.common_widget as cw

# pyqt imports
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget)

# ----------------------------------------------------------------------------------------------------------------------


class InfoTab(QWidget):
    # widget stylesheets
    table_style = """
        QTableWidget {
            font: Arial 6px;
            border: 1px solid;
        }
        QHeaderView {
            font: Arial 6px;
            font-weight: 1000;
        }
    """

    def __init__(self, t_lbl, layout=QVBoxLayout):
        super(InfoTab, self).__init__()

        # field initialisations
        self.table = None
        self.t_lbl = t_lbl

        # field retrieval
        self.tab_layout = layout(self)
        self.tab_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.tab_layout)

    def create_table_widget(self):

        # creates the table object
        self.table = QTableWidget(None)

        # sets the table properties
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        self.table.setObjectName(self.t_lbl)
        self.table.setStyleSheet(self.table_style)
        self.table.verticalHeader().setVisible(False)

        # adds the table to the layout
        self.tab_layout.addWidget(self.table)

        # resets the channel table style
        table_style = cw.CheckBoxStyle(self.table.style())
        self.table.setStyle(table_style)

        # table header setup
        table_header = cw.CheckTableHeader(self.table)
        self.table.setHorizontalHeader(table_header)
