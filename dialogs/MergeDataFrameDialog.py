from PyQt4.QtCore import *
from PyQt4.QtCore import pyqtSignal as Signal
from PyQt4.QtGui import *

__author__  = "Stephen Terry"
__version__ = "1.0.0"

class MergeDataFrameDialog(QDialog):

    accepted = Signal(dict)
    
    def __init__(self,options,parent=None):
        super(MergeDataFrameDialog,self).__init__(parent)
        self.options = options
        self.merge_options={}
        self.initUi()

    def initUi(self):
        self.setWindowTitle(self.tr('DataFrame Merge Options'))
        self.setModal(True)
        #self.resize(366, 274)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setSizePolicy(sizePolicy)
        
        self.gridLayout = QGridLayout()
        
        self.leftLabel = QLabel(self.tr('Select Left Frame'),self)
        self.rightLabel = QLabel(self.tr('Select Right Frame'),self)
        
        self.leftView = QListView(self)
        self.rightView = QListView(self)
        
        model = QStandardItemModel()
        for key in self.options.keys():
            item = QStandardItem(key)
            model.appendRow(item)
            
        self.leftView.setModel(model)
        self.rightView.setModel(model)
        self.leftView.clicked.connect(self.updateLeftCombo)
        self.rightView.clicked.connect(self.updateRightCombo)

        self.optGrid=QGridLayout()
        self.optGroupBox=QGroupBox("Merge Options")        
        
        joinGroupBox=QGroupBox("Join Options")
        self.innerJoinButton=QRadioButton("Inner")
        self.innerJoinButton.setChecked(True)
        self.outerJoinButton=QRadioButton("Outer")
        self.leftJoinButton=QRadioButton("Left")
        self.rightJoinButton=QRadioButton("Right")
        
        joinBox=QHBoxLayout()
        joinBox.addWidget(self.innerJoinButton)
        joinBox.addWidget(self.outerJoinButton)
        joinBox.addWidget(self.leftJoinButton)
        joinBox.addWidget(self.rightJoinButton)
        joinGroupBox.setLayout(joinBox)
        
        self.leftCombo=QComboBox()
        self.rightCombo=QComboBox()
        leftComboLabel=QLabel('Left Frame Merge On')
        rightComboLabel=QLabel('Right Frame Merge On')
        frameComboLabel=QLabel('Merge On')
        self.frameCombo=QComboBox()
        suffixLabel_x=QLabel("Left Frame Suffix")
        self.suffixLineEdit_x=QLineEdit()
        suffixLabel_y=QLabel("Right Frame Suffix")
        self.suffixLineEdit_y=QLineEdit()
        self.leftIndexCheck=QCheckBox("Merge on Left Index")
        self.rightIndexCheck=QCheckBox("Merge on Right Index")
        
        self.optGrid.addWidget(leftComboLabel,0,0)
        self.optGrid.addWidget(self.leftCombo,0,1)
        self.optGrid.addWidget(rightComboLabel,1,0)
        self.optGrid.addWidget(self.rightCombo,1,1)
        self.optGrid.addWidget(frameComboLabel,2,0)
        self.optGrid.addWidget(self.frameCombo,2,1)
        self.optGrid.addWidget(suffixLabel_x,3,0)
        self.optGrid.addWidget(self.suffixLineEdit_x,3,1,1,2)
        self.optGrid.addWidget(suffixLabel_y,4,0)
        self.optGrid.addWidget(self.suffixLineEdit_y,4,1,1,2)
        self.optGrid.addWidget(self.leftIndexCheck,5,0)
        self.optGrid.addWidget(self.rightIndexCheck,5,1)
        self.optGrid.addWidget(joinGroupBox,6,0,1,2)
        self.optGroupBox.setLayout(self.optGrid)
        
        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        
        self.gridLayout.addWidget(self.leftLabel,0,0)
        self.gridLayout.addWidget(self.rightLabel,0,1)
        self.gridLayout.addWidget(self.leftView, 1, 0, 1, 1)
        self.gridLayout.addWidget(self.rightView, 1, 1, 1, 1)
        self.gridLayout.addWidget(self.optGroupBox, 1, 2, 1, 1)
        
        
        self.gridLayout.addWidget(self.buttonBox, 3, 2, 1, 1)

        self.setLayout(self.gridLayout)


    def updateLeftCombo(self):
        selection = self.leftView.selectedIndexes()
        for index in selection:
            self.leftName = index.data(Qt.DisplayRole)
        self.leftCombo.clear()
        self.leftCombo.addItem("")
        self.leftCombo.addItems(self.options[self.leftName]['cols'])
        self.updateMergeCombo()
        
    def updateRightCombo(self):
        selection = self.rightView.selectedIndexes()
        for index in selection:
            self.rightName = index.data(Qt.DisplayRole)
        self.rightCombo.clear()
        self.rightCombo.addItem("")
        self.rightCombo.addItems(self.options[self.rightName]['cols'])
        self.updateMergeCombo()
        
    def updateMergeCombo(self):
        self.frameCombo.clear()
        self.frameCombo.addItem("")
        lItems = [self.leftCombo.itemText(i) for i in range(self.leftCombo.count())]
        rItems = [self.rightCombo.itemText(i) for i in range(self.rightCombo.count())]
        self.frameCombo.addItems(lItems)
        self.frameCombo.addItems(rItems)
        
    def accept(self):
        class MergeError(Exception): pass
        try:
            if (self.leftIndexCheck.isChecked() and  
            (self.rightIndexCheck.isChecked() or self.rightFrameCombo.currentText() != '')):
                pass
            elif (self.rightIndexCheck.isChecked() and  
            (self.leftIndexCheck.isChecked() or self.leftFrameCombo.currentText() != '')):
                pass
            elif (self.leftCombo.currentText() != '' and
            (self.rightCombo.currentText() != '' or self.rightIndexCheck.isChecked())):
                pass
            elif (self.rightCombo.currentText() != '' and
            (self.leftCombo.currentText() != '' or self.leftIndexCheck.isChecked())):
                pass
            elif self.frameCombo.currentText() != "":
                pass
            else:
                raise MergeError("ERROR!\n Check Merge On Conditions.\n"
                                   "See Help -> Merge Conditions or pandas.DataFrame.merge\n"
                                   "instructions.")
        except MergeError as e:
            QMessageBox.warning(self,"Merge Error",unicode(e))
            return
        if self.leftName == self.rightName:
            QMessageBox.warning(self,"Merge Error","Left Frame and Right Frame cannot be the same!!\n")
            return
        
        if self.suffixLineEdit_x.text() != '':
            if not self.suffixLineEdit_x.text().startswith('_'):
                self.merge_options['suffix_x']='_'+self.suffixLineEdit_x.text()
            else:
                self.merge_options['suffix_x']=self.suffixLineEdit_x.text()
        if self.suffixLineEdit_y.text() != '':
            if not self.suffixLineEdit_y.text().startswith('_'):
                self.merge_options['suffix_y']='_'+self.suffixLineEdit_y.text()
            else:
                self.merge_options['suffix_y']=self.suffixLineEdit_y.text()

        if self.innerJoinButton.isChecked():
            self.merge_options['how']='inner'
        elif self.outerJoinButton.isChecked():
            self.merge_options['how']='outer'
        elif self.leftJoinButton.isChecked():
            self.merge_options['how']='left'
        elif self.rightJoinButton.isChecked():
            self.merge_options['how']='right'
        else:
            pass
        if self.frameCombo.currentText() != '':
            self.merge_options['on']=self.frameCombo.currentText()
        if self.leftCombo.currentText() != '':
            self.merge_options['left_on']=self.leftCombo.currentText()
        if self.rightCombo.currentText() != '':
            self.merge_options['right_on']=self.rightCombo.currentText()
        if self.leftIndexCheck.isChecked():
            self.merge_options['left_index']=True
        if self.rightIndexCheck.isChecked():
            self.merge_options['right_index']=True
   
        output={"merge_options":self.merge_options,"left":self.options[self.leftName],"right":self.options[self.rightName]}
        
        super(MergeDataFrameDialog, self).accept()
        self.accepted.emit(output)