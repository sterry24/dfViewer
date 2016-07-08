# -*- coding: utf-8 -*-
"""
Created on Wed Feb 03 14:53:28 2016

@author: sterry
"""

from PyQt4.QtCore import *
try:
    from PyQt4.QtCore import QString
except:
    QString = str
from PyQt4.QtCore import pyqtSlot as Slot
from PyQt4.QtCore import pyqtSignal as Signal
from PyQt4.QtGui import *
from models.DataFrameTableModel import DataFrameTableModel

class DescribeDialog(QDialog):
    
    def __init__(self,data,parent=None):
        super(DescribeDialog,self).__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)
        self.data=data
        self.initUI()
        
    def initUI(self):
        
        self.gridLayout = QGridLayout()
        self.table=QTableView()
        self.model=DataFrameTableModel()
        self.table.setModel(self.model)
        self.model.setDataFrame(self.data)
        self.buttonBox=QDialogButtonBox(QDialogButtonBox.Ok)
        self.buttonBox.clicked.connect(self.accept)
        
        self.gridLayout.addWidget(self.table,0,0)
        self.gridLayout.addWidget(self.buttonBox,1,0)     
        
        self.setLayout(self.gridLayout)