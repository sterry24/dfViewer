# -*- coding: utf-8 -*-
"""
Created on Tue Feb 02 09:29:42 2016

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

class ExcelFileDialog(QDialog):
    
    accepted = Signal(dict)
    
    def __init__(self,filename,options,parent=None):
        super(ExcelFileDialog,self).__init__(parent)
        self.filename=filename
        self.sheets=options
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle(self.tr("Open Excel File"))
        self.setModal(True)
        self.resize(366, 274)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setSizePolicy(sizePolicy)
        
        self.gridLayout = QGridLayout(self)
        
        self.frameLabel=QLabel("Select Excel Sheet(s) to Parse")
        
        self.listView = QListView(self)
        
        model = QStandardItemModel()
        for sheet in self.sheets:
            item = QStandardItem(sheet)
            model.appendRow(item)

        self.listView.setModel(model)
        self.listView.setSelectionMode(QListView.MultiSelection)
        
        self.openEach=QCheckBox("Open sheets individually",self)

        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        
        self.frameComboBox=QComboBox()
        self.frameComboBox.addItems(self.sheets)
        selectButton=QPushButton("Ok")
        self.connect(selectButton,SIGNAL("clicked()"),self,SLOT("accept()"))
        
        self.gridLayout.addWidget(self.frameLabel, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.listView, 1, 0, 1, 1)
        self.gridLayout.addWidget(self.openEach, 2, 0, 1, 1)
        self.gridLayout.addWidget(self.buttonBox, 3, 0, 1, 1)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.setLayout(self.gridLayout)
        
    def accept(self):
        selection = self.listView.selectedIndexes()
        names = []
        for index in selection:
            names.append(index.data(Qt.DisplayRole))
        
        if self.openEach.isChecked():
            openEach = True
        else:
            openEach = False
        options={"file":self.filename,"sheets":names,"openEach":openEach}
        super(ExcelFileDialog, self).accept()
        self.accepted.emit(options)