import re
from pandas import Timestamp

from PyQt4.QtCore import *
from PyQt4.QtCore import pyqtSlot as Slot
from PyQt4.QtCore import pyqtSignal as Signal
from PyQt4.QtGui import *

from models.SupportedDtypes import SupportedDtypes


class AddAttributesDialog(QDialog):

    accepted = Signal(str, object, object)

    def __init__(self, parent=None):
        super(AddAttributesDialog, self).__init__(parent)

        self.initUi()

    def initUi(self):
        self.setModal(True)
        self.resize(303, 168)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setSizePolicy(sizePolicy)

        self.verticalLayout = QVBoxLayout(self)

        self.dialogHeading = QLabel(self.tr('Add a new attribute column'), self)

        self.gridLayout = QGridLayout()

        self.columnNameLineEdit = QLineEdit(self)
        self.columnNameLabel = QLabel(self.tr('Name'), self)
        self.dataTypeComboBox = QComboBox(self)

        self.dataTypeComboBox.addItems(SupportedDtypes.names())

        self.columnTypeLabel = QLabel(self.tr('Type'), self)
        self.defaultValueLineEdit = QLineEdit(self)
        self.defaultValueLabel = QLabel(self.tr('Inital Value(s)'), self)

        self.gridLayout.addWidget(self.columnNameLabel, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.columnNameLineEdit, 0, 1, 1, 1)

        self.gridLayout.addWidget(self.columnTypeLabel, 1, 0, 1, 1)
        self.gridLayout.addWidget(self.dataTypeComboBox, 1, 1, 1, 1)

        self.gridLayout.addWidget(self.defaultValueLabel, 2, 0, 1, 1)
        self.gridLayout.addWidget(self.defaultValueLineEdit, 2, 1, 1, 1)

        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.dialogHeading)
        self.verticalLayout.addLayout(self.gridLayout)
        self.verticalLayout.addWidget(self.buttonBox)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)


    def accept(self):
        super(AddAttributesDialog, self).accept()

        newColumn = self.columnNameLineEdit.text()
        dtype = SupportedDtypes.dtype(self.dataTypeComboBox.currentText())

        defaultValue = self.defaultValueLineEdit.text()
        try:
            if dtype in SupportedDtypes.intTypes() + SupportedDtypes.uintTypes():
                defaultValue = int(defaultValue)
            elif dtype in SupportedDtypes.floatTypes():
                defaultValue = float(defaultValue)
            elif dtype in SupportedDtypes.boolTypes():
                defaultValue = defaultValue.lower() in ['t', '1']
            elif dtype in SupportedDtypes.datetimeTypes():
                defaultValue = Timestamp(defaultValue)
                if isinstance(defaultValue, NaTType):
                    defaultValue = Timestamp('')
            else:
                defaultValue = dtype.type()
        except ValueError as e:
            defaultValue = dtype.type()

        self.accepted.emit(newColumn, dtype, defaultValue)

class FilterColDialog(QDialog):
    
    accepted = Signal(dict)
    
    def __init__(self,section,name,values,parent=None):
        super(FilterColDialog,self).__init__(parent)
        self.section = section
        self.name = name
        self.values = ['']
        for each in values:
            if str(each) not in self.values:
                self.values.append(str(each))
        self.filters=["","Equals","Does not equal", "Less than", 
        "Less than or equal to","Greater than","Greater than or equal to"]
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle(self.tr("Create Filter"))
        self.setModal(True)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setSizePolicy(sizePolicy)
        
        self.gridLayout=QGridLayout()
        
        self.showLabel=QLabel(self.tr("Show rows where %s:" % self.name))
        
        self.filterOne = QComboBox()
        self.filterTwo = QComboBox()
        self.filterOne.addItems(self.filters)
        self.filterTwo.addItems(self.filters)
        
        self.valueOne = QComboBox()
        self.valueOne.setEditable(True)
        self.valueTwo = QComboBox()
        self.valueTwo.setEditable(True)
        self.valueOne.addItems(self.values)
        self.valueTwo.addItems(self.values)
        
        self.andButton = QRadioButton("and")
        self.andButton.setChecked(True)
        self.orButton = QRadioButton("or")
        self.andOrBox = QHBoxLayout()
        self.andOrBox.addWidget(self.andButton)
        self.andOrBox.addWidget(self.orButton)        
        
        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        
        self.gridLayout.addWidget(self.showLabel,0,0)
        self.gridLayout.addWidget(self.filterOne,1,0,1,1)
        self.gridLayout.addWidget(self.valueOne,1,2,1,1)
        self.gridLayout.addLayout(self.andOrBox,2,0,1,1)
        self.gridLayout.addWidget(self.filterTwo,3,0,1,1)
        self.gridLayout.addWidget(self.valueTwo,3,2,1,1)
        self.gridLayout.addWidget(self.buttonBox,4,2)
        
        self.setLayout(self.gridLayout)
        
    def accept(self):
        selection={}

        filterOne = str(self.filterOne.currentText())
        if filterOne == '':
            QMessageBox.warning(self,"Filter Error","Must select at least one operation.\n")
        else:
            if filterOne == "Equals":
                filterOne = "=="
            elif filterOne == "Does not equal":
                filterOne = "!="
            elif filterOne == "Less than":
                filterOne = "<"
            elif filterOne == "Less than or equal to":
                filterOne = "<="
            elif filterOne == "Greater than":
                filterOne = ">"
            else:
                filterOne = ">="
            filterTwo = str(self.filterTwo.currentText())
            if filterTwo != '':
                if filterTwo == "Equals":
                    filterTwo = "=="
                elif filterTwo == "Does not equal":
                    filterTwo = "!="
                elif filterTwo == "Less than":
                    filterTwo = "<"
                elif filterTwo == "Less than or equal to":
                    filterTwo = "<="
                elif filterTwo == "Greater than":
                    filterTwo = ">"
                else:
                    filterTwo = ">="
            else:
                filterTwo = '' 
            
            
            selection['name']=str(self.name)
            selection['filterOne']=filterOne
            selection['filterTwo']=filterTwo
            selection['valueOne']=str(self.valueOne.currentText())
            selection['valueTwo']=str(self.valueTwo.currentText())
            selection['operator']= '&' if self.andButton.isChecked else '|'
            
            super(FilterColDialog, self).accept()
            self.accepted.emit(selection)

class FillNaNDialog(QDialog):
    
    accepted = Signal(list)
  
    def __init__(self,section,parent=None):
        super(FillNaNDialog,self).__init__(parent)
        self.section = section
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle(self.tr("Fill NaN's"))
        self.setModal(True)
        self.resize(366, 274)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setSizePolicy(sizePolicy)
        
        self.gridLayout=QGridLayout()
        
        self.fillWithLabel=QLabel(self.tr("Fill With"))
        self.fillWithEdit=QLineEdit()
        self.methodLabel=QLabel(self.tr("Fill Method"))
        self.fillMethodCombo=QComboBox()
        self.fillMethodCombo.addItems(['None','backfill','bfill','pad','ffill'])
        
        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        
        self.gridLayout.addWidget(self.fillWithLabel,0,0)
        self.gridLayout.addWidget(self.fillWithEdit,0,1)
        self.gridLayout.addWidget(self.methodLabel,1,0)
        self.gridLayout.addWidget(self.fillMethodCombo,1,1)
        self.gridLayout.addWidget(self.buttonBox,2,1)
        self.setLayout(self.gridLayout)
        
    def accept(self):
        selection = [self.fillMethodCombo.currentText(),self.fillWithEdit.text(),self.section]
        super(FillNaNDialog, self).accept()
        self.accepted.emit(selection)

class ReplaceEntryDialog(QDialog):

    accepted = Signal(list)
    
    def __init__(self,section,parent=None):
        super(ReplaceEntryDialog,self).__init__(parent)
        self.section = section
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle(self.tr('Replace Entry'))
        self.setModal(True)
        self.resize(366, 274)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setSizePolicy(sizePolicy)
        
        self.gridLayout = QGridLayout()
        
        self.toReplaceLabel = QLabel(self.tr("Value to Replace"))
        self.toReplaceLineEdit = QLineEdit()
        self.replaceWithLabel = QLabel(self.tr("Replace With"))
        self.replaceWithLineEdit = QLineEdit()
        
        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        
        self.gridLayout.addWidget(self.toReplaceLabel,0,0)
        self.gridLayout.addWidget(self.toReplaceLineEdit,0,1)
        self.gridLayout.addWidget(self.replaceWithLabel,1,0)
        self.gridLayout.addWidget(self.replaceWithLineEdit,1,1)
        self.gridLayout.addWidget(self.buttonBox,2,1)
        self.setLayout(self.gridLayout)
        
    def accept(self):
        selection = [self.toReplaceLineEdit.text(),self.replaceWithLineEdit.text(),self.section]
        super(ReplaceEntryDialog, self).accept()
        self.accepted.emit(selection)     


class RemoveAttributesDialog(QDialog):

    accepted = Signal(list)

    def __init__(self, columns, parent=None):
        super(RemoveAttributesDialog, self).__init__(parent)
        self.columns = columns
        self.initUi()

    def initUi(self):
        self.setWindowTitle(self.tr('Remove Attributes'))
        self.setModal(True)
        self.resize(366, 274)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setSizePolicy(sizePolicy)

        self.gridLayout = QGridLayout(self)

        self.dialogHeading = QLabel(self.tr('Select the attribute column(s) which shall be removed'), self)

        self.listView = QListView(self)

        model = QStandardItemModel()
        for column in self.columns:
            item = QStandardItem(column)
            model.appendRow(item)

        self.listView.setModel(model)
        self.listView.setSelectionMode(QListView.MultiSelection)

        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)

        self.gridLayout.addWidget(self.dialogHeading, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.listView, 1, 0, 1, 1)
        self.gridLayout.addWidget(self.buttonBox, 2, 0, 1, 1)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)



    def accept(self):
        selection = self.listView.selectedIndexes()
        names = []
        for index in selection:
            position = index.row()
            names.append((position, index.data(Qt.DisplayRole)))

        super(RemoveAttributesDialog, self).accept()
        self.accepted.emit(names)
        