# -*- coding: utf-8 -*-
"""
Created on Tue Feb 02 10:07:55 2016

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


class GroupByDialog(QDialog):
    
    changed = Signal(object)
    
    def __init__(self,options,parent=None):
        super(GroupByDialog,self).__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.callerModified = False
        self.data = options['data']
        self.callerIndex=options['idx']
        self.initUI()
        
    def initUI(self):
        
        self.title = QFileInfo(self.data.model()._filename).fileName()
        self.title = self.title + ' Group By Options'
        self.setWindowTitle(self.tr(self.title))
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setSizePolicy(sizePolicy)
        
        self.gridLayout=QGridLayout()
        
        self.groupByLabel=QLabel("Group by")
        self.groupByList=QListView(self)
        #self.groupCombo.addItems(self.df.columns)
        
        self.groupsLabel=QLabel("Groups")
        self.groupsList=QListView(self)
        self.addTabCheckBox=QCheckBox("Show Group in New Tab",self)
        self.addTabCheckBox.setChecked(True)
        
        groupByModel = QStandardItemModel()
        for col in self.data.model()._df.columns:
            item = QStandardItem(col)
            groupByModel.appendRow(item)        

        self.groupByList.setModel(groupByModel)
        self.groupByList.clicked.connect(self.updateGroups)
        
        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Apply | QDialogButtonBox.Close)
        
        self.buttonBox.button(QDialogButtonBox.Apply).clicked.connect(self.apply)
        self.buttonBox.button(QDialogButtonBox.Close).clicked.connect(self.reject)
        
        self.gridLayout.addWidget(self.groupByLabel,0,0)
        self.gridLayout.addWidget(self.groupsLabel,0,1)
        self.gridLayout.addWidget(self.groupByList,1,0)
        self.gridLayout.addWidget(self.groupsList,1,1)
        self.gridLayout.addWidget(self.addTabCheckBox,2,0)
        self.gridLayout.addWidget(self.buttonBox,2,1)
        self.setLayout(self.gridLayout)
        
        
    def updateGroups(self):
        
        selection = self.groupByList.selectedIndexes()
        for index in selection:
            self.field = index.data(Qt.DisplayRole)
        self.grouped = self.data.model()._df.groupby(self.field)
        
        l=[]
        for each in self.grouped.groups.keys():
            l.append(str(each))
            
        model = QStandardItemModel()
        for group in l:
            item = QStandardItem(group)
            model.appendRow(item)
        self.groupsList.setModel(model)
        
    def apply(self):

        opts = {}
        self.group = None
        selection = self.groupsList.selectedIndexes()
        for index in selection:
            self.group = index.data(Qt.DisplayRole)
            
        if self.group is None:
            QMessageBox.warning(self,"Group By Error","No Group Selected!!\n"
                "Please select an item in the Group By and Groups lists.")
            return            
            
        if self.group.isdigit():
            self.selected=self.grouped.get_group(int(self.group)).copy()

        elif self.group.find('.') == 0:
            if self.group[1:].isdigit():
                self.selected=self.grouped.get_group(float(self.group)).copy()

        elif self.group.find('.') > 0:
            if self.group[:self.group.find('.')].isdigit():
                if self.group[self.group.find('.')+1:].isdigit():
                    self.selected=self.grouped.get_group(float(self.group)).copy()

        else:
            self.selected=self.grouped.get_group(self.group)
            
        if self.addTabCheckBox.isChecked():
            opts['newTab']=True
        else:
            self.callerModified = True
            opts['newTab']=False
            
        name=(QFileInfo(self.data.model()._filename).fileName() + '_groupBy_' +
              str(self.field) + '_group_' + str(self.group))
              
        opts['key'] = "Accept"
        opts['name']=name
        opts['idx']=self.callerIndex
        opts['df']=self.selected
            
        self.changed.emit(opts)
        
    def reject(self):
        
        opts = {}
        if self.callerModified:
            opts['key'] = "Reject"
            opts['name'] = QFileInfo(self.data.model()._filename).fileName()
            opts['idx']=self.callerIndex
            opts['df']=self.data
            self.changed.emit(opts)
        
        else:
            opts['key'] = "Reject"
            opts['idx']=self.callerIndex
            self.changed.emit(opts)
            
        QDialog.reject(self)
