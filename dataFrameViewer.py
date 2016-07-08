import csv
import sys
from collections import OrderedDict
from PyQt4.QtCore import *
from PyQt4.QtCore import pyqtSlot as Slot
from PyQt4.QtGui import *
import pandas as pd
import numpy as np
import qrc_resources


from dialogs.EditDialogs import (AddAttributesDialog, RemoveAttributesDialog, 
                                 ReplaceEntryDialog, FillNaNDialog,
                                 FilterColDialog)
from dialogs.ExcelFileDialog import ExcelFileDialog
from dialogs.MergeDataFrameDialog import MergeDataFrameDialog
from dialogs.GroupByDialog import GroupByDialog
from dialogs.DescribeDialog import DescribeDialog
from dialogs.GraphFormatDialog import GraphFormatDialog
from models.DataFrameTableModel import DataFrameTableModel

__author__ = "Stephen Terry"
__version__= "1.0.0"

class DataFrameViewer(QMainWindow):
    
    NextID = 1
    
    def __init__(self,filename='',parent=None):
        super(DataFrameViewer,self).__init__(parent)
        
        
        ## Tab widget for DataFrames########################################
        self.tableTabWidget = QTabWidget()
        self.tableTabWidget.setTabPosition(1)
        self.tableTabWidget.setTabsClosable(True)
        self.tableTabWidget.currentChanged.connect(self.tabChanged)
        self.setCentralWidget(self.tableTabWidget)

        
        ## Actions and shortcuts for table(s)##################################
        fileNewAction = self.createAction("&New", self.fileNew,
                QKeySequence.New, "filenew", "Create a file")
        fileOpenAction = self.createAction("&Open...", self.fileOpen,
                QKeySequence.Open, "fileopen",
                "Open an existing file")
        fileSaveAction = self.createAction("&Save", self.fileSave,
                QKeySequence.Save, "filesave", "Save the file")
        fileSaveAsAction = self.createAction("Save &As...",
                self.fileSaveAs, icon="filesaveas",
                tip="Save the file using a new filename")
        fileSaveAllAction = self.createAction("Save A&ll",
                self.fileSaveAll, icon="filesave",
                tip="Save all the files")
        fileCloseTabAction = self.createAction("Close &Tab",
                self.fileCloseTab, QKeySequence.Close, "filequit",
                "Close the active tab")
        fileQuitAction = self.createAction("&Quit", self.close,
                "Ctrl+Q", "filequit", "Close the application")
        
        self.editEditableAction = self.createAction("E&ditable", 
                self.enableEditing,icon="document-edit",checkable=True,
                signal="toggled(bool)")
        self.editAddRowAction = self.createAction("Add Row", self.addRow,
                icon='edit-table-insert-row-below', tip="Add a new row")
        self.editAddColAction = self.createAction("Add Column",
                self.showAddColumnDialog,icon='edit-table-insert-column-right',
                tip="Add a new column")
        self.editDelRowAction = self.createAction("Delete Row", self.removeRow,
                icon='edit-table-delete-row', tip="Delete a row")
        self.editDelColAction = self.createAction("Delete Column", 
                self.showRemoveColumnDialog,icon='edit-table-delete-column',
                tip="Delete a column")
        self.editUndoAction = self.createAction("Undo", self.undoChange,
                shortcut = 'Ctrl+Z',icon='previous', tip="Undo last action")
        self.editRedoAction = self.createAction("Redo", self.redoChange,
                shortcut = 'Ctrl+Y',icon='next', tip="Redo last action")
        self.mergeAction = self.createAction("Merge DataFrames",
                self.showMergeDialog, icon='merge', tip="Merge Dataframes")
        self.groupByAction = self.createAction("GroupBy", self.showGroupDialog,
                icon="group",tip="Group-by")
        self.graphAction = self.createAction("Launch Graphing Tool", 
                self.showGraphDialog, icon="graph", tip="Launch Graphing Tool")
        self.describeAction = self.createAction("Describe Data", 
                self.showDescribeDialog, icon="describe", tip="Describe Data")
        self.editEditableAction.setChecked(False)
        self.editAddRowAction.setEnabled(False)
        self.editAddColAction.setEnabled(False)
        self.editDelRowAction.setEnabled(False)
        self.editDelColAction.setEnabled(False)
        self.editUndoAction.setEnabled(False)
        self.editRedoAction.setEnabled(False)
        QShortcut(QKeySequence.PreviousChild, self, self.prevTab)
        QShortcut(QKeySequence.NextChild, self, self.nextTab)
        
        
        fileMenu = self.menuBar().addMenu("&File")
        self.addActions(fileMenu, (fileNewAction, fileOpenAction,
                fileSaveAction, fileSaveAsAction, fileSaveAllAction,
                fileCloseTabAction, None, fileQuitAction))
                
        editMenu = self.menuBar().addMenu("&Edit")
        self.addActions(editMenu,(self.editEditableAction,self.editAddRowAction,
                self.editAddColAction,self.editDelRowAction,self.editDelColAction,
                None,self.editUndoAction,self.editRedoAction))
                
        dataMenu = self.menuBar().addMenu("&Data")
        self.addActions(dataMenu,(self.mergeAction,self.groupByAction,
                self.describeAction))
        
        graphMenu = self.menuBar().addMenu("&Graph")
        self.addActions(graphMenu,(self.graphAction,))
                
        fileToolbar = self.addToolBar("File")
        fileToolbar.setObjectName("FileToolbar")
        self.addActions(fileToolbar, (fileNewAction, fileOpenAction,
                                      fileSaveAction))
        editToolbar = self.addToolBar("Edit")
        editToolbar.setObjectName("EditToolbar")
        self.addActions(editToolbar,(self.editEditableAction,self.editAddRowAction,
                self.editAddColAction,self.editDelRowAction,self.editDelColAction,
                None,self.editUndoAction,self.editRedoAction))
                
        miscToolbar = self.addToolBar("Misc")
        miscToolbar.setObjectName("MiscToolbar")
        self.addActions(miscToolbar,(self.mergeAction,self.groupByAction,self.graphAction,
                self.describeAction))
                
        self.connect(self.tableTabWidget,SIGNAL("tabCloseRequested(int)"),self.fileCloseTab)
        
        status = self.statusBar()
        status.setSizeGripEnabled(False)
        status.showMessage("Ready", 5000)

        self.setWindowTitle("DataFrameViewer")
        
        self.filename = filename
        if self.filename != '':
            self.loadFile(filename)
            
    def trackChanges(self):
        tableEdit = self.tableTabWidget.currentWidget()
        if isinstance(tableEdit,QTableView):
            tableEdit.model()._currChange += 1
            tableEdit.model()._changes.insert(tableEdit.model()._currChange,tableEdit.model()._df.copy())
            if tableEdit.model()._currChange > 0:
                self.editUndoAction.setEnabled(True)
            else:
                self.editUndoAction.setEnabled(False)
            if tableEdit.model()._currChange < len(tableEdit.model()._changes) - 1:
                tableEdit.model()._changes=tableEdit.model()._changes[:tableEdit.model()._currChange + 1]
                self.editRedoAction.setEnabled(False)
                
        if isinstance(tableEdit,QTabWidget):
            table = tableEdit.currentWidget()
            table.model()._currChange += 1
            table.model()._changes.insert(table.model()._currChange,table.model()._df.copy())
            if table.model()._currChange > 0:
                self.editUndoAction.setEnabled(True)
            else:
                self.editUndoAction.setEnabled(False)
            if table.model()._currChange < len(table.model()._changes) - 1:
                table.model()._changes=table.model()._changes[:table.model()._currChange + 1]
                self.editRedoAction.setEnabled(False)

            
    def undoChange(self):
        tableEdit = self.tableTabWidget.currentWidget()
        if isinstance(tableEdit,QTableView):
            if tableEdit.model()._currChange > 0:
                tableEdit.model().undo()
                self.editRedoAction.setEnabled(True)
            if tableEdit.model()._currChange == 0:
                self.editUndoAction.setEnabled(False)
                
        if isinstance(tableEdit,QTabWidget):
            table = tableEdit.currentWidget()
            if table.model()._currChange > 0:
                table.model().undo()
                self.editRedoAction.setEnabled(True)
            if table.model()._currChange == 0:
                self.editUndoAction.setEnabled(False)
                    
    
    def redoChange(self):
        tableEdit = self.tableTabWidget.currentWidget()
        if isinstance(tableEdit,QTableView):
            if tableEdit.model()._currChange < len(tableEdit.model()._changes) - 1:
                tableEdit.model().redo()
                self.editUndoAction.setEnabled(True)
            if tableEdit.model()._currChange == len(tableEdit.model()._changes) - 1:
                self.editRedoAction.setEnabled(False)
                
        if isinstance(tableEdit,QTabWidget):
            table = tableEdit.currentWidget()
            if table.model()._currChange < len(table.model()._changes) - 1:
                table.model().redo()
                self.editUndoAction.setEnabled(True)
            if table.model()._currChange == len(table.model().changes) - 1:
                self.editRedoAction.setEnabled(False)
            
            
    def closeEvent(self, event):
        
        self.fileSaveAll()


    def tabChanged(self):
    
        tableEdit = self.tableTabWidget.currentWidget()
        if isinstance(tableEdit,QTableView):
            if tableEdit.model().editable:
                self.editEditableAction.setChecked(True)
            else:
                self.editEditableAction.setChecked(False)
        if isinstance(tableEdit,QTabWidget):
            table = tableEdit.currentWidget()
            if table.model().editable:
                self.editEditableAction.setChecked(True)
            else:
                self.editEditableAction.setChecked(False)
        
        
    def prevTab(self):
        last = self.tableTabWidget.count()
        current = self.tableTabWidget.currentIndex()
        if last:
            last -= 1
            current = last if current == 0 else current - 1
            self.tableTabWidget.setCurrentIndex(current)


    def nextTab(self):
        last = self.tableTabWidget.count()
        current = self.tableTabWidget.currentIndex()
        if last:
            last -= 1
            current = 0 if current == last else current + 1
            self.tableTabWidget.setCurrentIndex(current)        
    
    def doNothing(self):
        pass
    
    def sortColumn(self,column,who):
        tableEdit = self.tableTabWidget.currentWidget()
        if isinstance(tableEdit,QTableView):
            model = tableEdit.model()
        elif isinstance(tableEdit,QTabWidget):
            tableEdit=tableEdit.currentWidget()
            model = tableEdit.model()
        else:
            return
            
        if model is not None:
            if self.okToEdit(model):
                if who:
                    model.sort(column,True)
                if not who:
                    model.sort(column,False)
    
############## CONTEXT MENU FUNCTIONS #########################################
    def headerMenu(self,position):
        tableEdit = self.tableTabWidget.currentWidget()
        if isinstance(tableEdit, QTableView):
            column = tableEdit.headers.logicalIndexAt(position)
        elif isinstance(tableEdit, QTabWidget):
            tableEdit = tableEdit.currentWidget()
            column = tableEdit.headers.logicalIndexAt(position)
        else:
            return

        menu = QMenu()
        submenu=QMenu("Sort")
        sortAscendAction=QAction("Ascending",self)
        sortAscendAction.triggered.connect(lambda: self.sortColumn(column,True))
        sortDescendAction=QAction("Descending",self)
        sortDescendAction.triggered.connect(lambda: self.sortColumn(column,False))
        submenu.addAction(sortAscendAction)
        submenu.addAction(sortDescendAction)
        convertMenu=QMenu("Convert Objects")
        convertNumericAction=QAction("Numeric",self)
        convertNumericAction.triggered.connect(lambda: tableEdit.model().convertColumnsToNumeric(column))
        convertDateAction=QAction("Date",self)
        convertDateAction.triggered.connect(lambda: tableEdit.model().convertColumnsToDate(column))
        convertDeltaAction=QAction("TimeDeltas",self)
        convertDeltaAction.triggered.connect(lambda: tableEdit.model().convertColumnsToTimeDeltas(column))
        convertMenu.addAction(convertNumericAction)
        convertMenu.addAction(convertDateAction)
        convertMenu.addAction(convertDeltaAction)
        fillNaNAction=QAction("Fill NaN's",self)
        fillNaNAction.triggered.connect(lambda: self.showFillNaNDialog(column))
        menu.addMenu(convertMenu)
        menu.addMenu(submenu)
        menu.addAction(fillNaNAction)
        replaceEntryAction=QAction("Replace",self)
        replaceEntryAction.triggered.connect(lambda: self.showReplaceValueDialog(column))
        filterColAction=QAction("Filter",self)
        filterColAction.triggered.connect(lambda: self.showFilterColDialog(column))   
        menu.addAction(replaceEntryAction)
        menu.addAction(filterColAction)
        menu.exec_(tableEdit.viewport().mapToGlobal(position))
        
    def vHeaderMenu(self,position):
        tableEdit = self.tableTabWidget.currentWidget()
        if isinstance(tableEdit, QTableView):
            column = tableEdit.headers.logicalIndexAt(position)
        elif isinstance(tableEdit, QTabWidget):
            tableEdit = tableEdit.currentWidget()
            column = tableEdit.headers.logicalIndexAt(position)
        else:
            return
        row = tableEdit.vHeaders.logicalIndexAt(position)
        menu = QMenu("Drop Row")
        dropRowAction=QAction("Drop",self)
        dropRowAction.triggered.connect(lambda: self.removeRow(val=row))
        menu.addAction(dropRowAction)
        menu.exec_(tableEdit.viewport().mapToGlobal(position))    
###############################################################################
    
    def fileNew(self):

        filename = "Unnamed-%d" % self.NextID
        self.NextID += 1
        table = QTableView()
        table.setAlternatingRowColors(True)
        model=DataFrameTableModel(filename=filename)
        model.trackDataChange.connect(self.trackChanges)
        table.setModel(model)
        ### Set some variables ###
        table.headers = table.horizontalHeader()
        table.vHeaders=table.verticalHeader()
        #### Set context menu for table headers ####
        table.headers.setContextMenuPolicy(Qt.CustomContextMenu)
        table.headers.customContextMenuRequested.connect(self.headerMenu)
        table.vHeaders.setContextMenuPolicy(Qt.CustomContextMenu)
        table.vHeaders.customContextMenuRequested.connect(self.vHeaderMenu)
        d={'':{'':''}}
        df=pd.DataFrame(d)
        model.setDataFrame(df)
        self.tableTabWidget.addTab(table, 
                                   QFileInfo(model._filename).fileName())
        self.tableTabWidget.setCurrentWidget(table)
        self._currentTab = self.tableTabWidget.currentIndex()
        


    def fileOpen(self):
        filename = str(QFileDialog.getOpenFileName(self,
                            "DataFrameViewer -- Open File"))
        if not filename == '':
            for i in range(self.tableTabWidget.count()):
                tableEdit = self.tableTabWidget.widget(i)
                if tableEdit is None:
                    return
                elif isinstance(tableEdit,QTabWidget):
                    for j in range(tableEdit.count()):
                        table = tableEdit.widget(i)
                        if isinstance(table,QTableView):
                            if table.model()._filename == filename:
                                tableEdit.setCurrentWidget(table)
                                self.tableTabWidget.setCurrentWidget(tableEdit)
                    
                elif tableEdit.model()._filename == filename:
                    self.tableTabWidget.setCurrentWidget(tableEdit)
                    break
                else:
                    pass
            else:
                self.loadFile(filename)


    def loadFile(self, filename):
        if filename.endswith('.xls') or filename.endswith('.xlsx'):
            df=pd.ExcelFile(filename)
            sheetnames=df.sheet_names
            dialog=ExcelFileDialog(filename,sheetnames,self)
            dialog.accepted.connect(self.loadExcel)
            dialog.show()
        else:
            table = QTableView()
            table.setAlternatingRowColors(True)
            model=DataFrameTableModel(filename=filename)
            model.trackDataChange.connect(self.trackChanges)
            table.setModel(model)
            ### Set some variables ###
            table.headers = table.horizontalHeader()
            table.vHeaders=table.verticalHeader()
            #### Set context menu for table headers ####
            table.headers.setContextMenuPolicy(Qt.CustomContextMenu)
            table.headers.customContextMenuRequested.connect(self.headerMenu)
            table.vHeaders.setContextMenuPolicy(Qt.CustomContextMenu)
            table.vHeaders.customContextMenuRequested.connect(self.vHeaderMenu)
            if model._filename.endswith('.csv'):
                df=pd.read_csv(model._filename)
                model.setDataFrame(df)
                self.tableTabWidget.addTab(table, QFileInfo(model._filename).fileName())
                self.tableTabWidget.setCurrentWidget(table)
            if model._filename.endswith('.txt'):
                delim = str(self.parseDelimiter(model._filename))
                if delim == ' ':
                    df=pd.read_csv(model._filename,delim_whitespace = True)
                else:
                    df=pd.read_csv(model._filename,sep=delim)
                model.setDataFrame(df)
                self.tableTabWidget.addTab(table, QFileInfo(model._filename).fileName())
                self.tableTabWidget.setCurrentWidget(table)
        
            
    def loadExcel(self,options):
        names = options['sheets']
        filename = options['file']
        openEach = options['openEach']
        df=pd.ExcelFile(filename)
        if not openEach:
            newTab = QTabWidget()
            newTab.setTabsClosable(True)
            newTab.currentChanged.connect(self.tabChanged)
            self.connect(newTab,SIGNAL("tabCloseRequested(int)"),
                         self.fileCloseInternalTab)
            for i in range(len(names)):
                table = QTableView()
                table.setAlternatingRowColors(True)
                model=DataFrameTableModel(filename=filename)
                model.trackDataChange.connect(self.trackChanges)
                table.setModel(model)
                ### Set some variables ###
                table.headers = table.horizontalHeader()
                table.vHeaders=table.verticalHeader()
                #### Set context menu for table headers ####
                table.headers.setContextMenuPolicy(Qt.CustomContextMenu)
                table.headers.customContextMenuRequested.connect(self.headerMenu)
                table.vHeaders.setContextMenuPolicy(Qt.CustomContextMenu)
                table.vHeaders.customContextMenuRequested.connect(self.vHeaderMenu)
                
                df2=df.parse(sheetname=names[i])
                model.setDataFrame(df2)
                newTab.addTab(table,names[i])
            newTab.setCurrentIndex(0)
            self.tableTabWidget.addTab(newTab,QFileInfo(filename).fileName())
            self.tableTabWidget.setCurrentWidget(newTab)
        else:
            for i in range(len(names)):
                table = QTableView()
                table.setAlternatingRowColors(True)
                model=DataFrameTableModel(filename=names[i])
                model.trackDataChange.connect(self.trackChanges)
                table.setModel(model)
                ### Set some variables ###
                table.headers = table.horizontalHeader()
                table.vHeaders=table.verticalHeader()
                #### Set context menu for table headers ####
                table.headers.setContextMenuPolicy(Qt.CustomContextMenu)
                table.headers.customContextMenuRequested.connect(self.headerMenu)
                table.vHeaders.setContextMenuPolicy(Qt.CustomContextMenu)
                table.vHeaders.customContextMenuRequested.connect(self.vHeaderMenu)
                df2=df.parse(sheetname=names[i])
                model.setDataFrame(df2)
                self.tableTabWidget.addTab(table,names[i])
                self.tableTabWidget.setCurrentWidget(table)
            

    def writeTextOutput(self,table):
        outfile=open(table.model()._filename)
        table.model()._df.to_string(outfile,index=False)
        table.model()._dirty = False
        outfile.close()
        
    def writeCSVOutput(self,table):
        table.model()._df.to_csv(table.model()._filename,index=False)
        table.model()._dirty = False
        
    def writePickleOutput(self,table):
        pass
        #table.model()._dirty = False
    
    def writeExcelOutput(self,table):
        if isinstance(table,QTabWidget):
            filename = table.currentWidget().model()._filename
            writer = pd.ExcelWriter(filename, engine='xlsxwriter')
            
            for i in range(table.count()):
                data=table.widget(i)
                sheetname=table.tabText(i)
                data.model()._df.to_excel(writer, sheet_name=sheetname,index=False)
                data.model()._dirty = False
            writer.save()
        if isinstance(table,QTableView):
            filename = table.model()._filename
            writer = pd.ExcelWriter(filename, engine='xlsxwriter')
            table.model()._df.to_excel(writer, sheet_name='Sheet 1',index=False)
            table.model()._dirty = False
            writer.save()

    def fileSave(self):
        tableEdit = self.tableTabWidget.currentWidget()
        if isinstance(tableEdit, QTableView):
            if tableEdit.model()._filename.endswith('.txt'):
                self.writeTextOutput(tableEdit)
            elif tableEdit.model()._filename.endswith('.csv'):
                self.writeCSVOutput(tableEdit)
            elif tableEdit.model()._filename.endswith('.pkl'):
                self.writePickleOutput(tableEdit)
            else:
                self.fileSaveAs()

            if (self.tableTabWidget.tabText(
                self.tableTabWidget.currentIndex()).startswith("Unnamed-")):
                self.tableTabWidget.setTabText(self.tableTabWidget.currentIndex(),
                        QFileInfo(tableEdit.model()._filename).fileName())
                        
        if isinstance(tableEdit,QTabWidget):
            files = []
            msg = "Select YES to save as Excel File\nSelect NO to save as csv's."
            reply = QMessageBox.question(self,"Excel File Detected",msg,
                                         QMessageBox.Yes,QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.writeExcelOutput(tableEdit)
            else:

                for i in range(tableEdit.count()):
                    newName=tableEdit.tabText(i) + '.csv'
                    table=tableEdit.widget(i)
                    table.model()._filename = os.path.join(QFileInfo(table.model()._filename).absolutePath(),newName)
                    files.append(table.model()._filename)
                    self.writeCSVOutput(table)

                self.tableTabWidget.removeTab(self.tableTabWidget.currentIndex())
                for f in files:
                    self.loadFile(f)


    def fileSaveAs(self):
        files_types = "Excel (*.xls);;Pickle (*.pkl);;CSV (*.csv);;Text (*.txt)"
        tableEdit = self.tableTabWidget.currentWidget()
        if isinstance(tableEdit, QTableView):
            filename = QFileDialog.getSaveFileNameAndFilter(self,
                        "DataFrameViewer -- Save File As",
                        tableEdit.model()._filename, files_types)
            if not filename[0] == '':
                tableEdit.model()._filename = filename[0]
                self.tableTabWidget.setTabText(self.tableTabWidget.currentIndex(),
                                          QFileInfo(filename[0]).fileName())
                if filename[1].find('.csv') >= 0:
                    self.writeCSVOutput(tableEdit)
                if filename[1].find('.xls') >= 0:
                    self.writeExcelOutput(tableEdit)
                if filename[1].find('.txt') >= 0:
                    self.writeTextOutput(tableEdit)
                if filename[1].find('.pkl') >= 0:
                    self.writePickleOutput(tableEdit)
        if isinstance(tableEdit,QTabWidget):
            msg = "Select YES to save the Excel File\nSelect NO to save single sheet."
            reply = QMessageBox.question(self,"Excel File Detected",msg,QMessageBox.Yes,QMessageBox.No)
            if reply == QMessageBox.Yes:
                filename = QFileDialog.getSaveFileName(self,
                        "DataFrameViewer -- Save File As",
                        tableEdit.currentWidget().model()._filename, "Excel (*.xls)")
                if not filename == '':
                    for i in range(tableEdit.count()):
                        tableEdit.widget(i).model()._filename = filename
                    self.tableTabWidget.setTabText(self.tableTabWidget.currentIndex(),
                                          QFileInfo(filename).fileName())
                    self.writeExcelOutput(tableEdit)
            else:
                table=tableEdit.currentWidget()
                filename = QFileDialog.getSaveFileNameAndFilter(self,
                            "DataFrameViewer -- Save File As",
                            table.model()._filename, files_types)
                if not filename[0] == '':
                    table.model()._filename = filename[0]
                    tableEdit.setTabText(tableEdit.currentIndex(),
                                         QFileInfo(filename[0]).fileName())
                    if filename[1].find('.csv') >= 0:
                        self.writeCSVOutput(tableEdit)
                    if filename[1].find('.xls') >= 0:
                        self.writeExcelOutput(tableEdit)
                    if filename[1].find('.txt') >= 0:
                        self.writeTextOutput(tableEdit)
                    if filename[1].find('.pkl') >= 0:
                        self.writePickleOutput(tableEdit)


    def fileSaveAll(self):
        for i in range(self.tableTabWidget.count()):
            tableEdit = self.tableTabWidget.widget(i)
            if isinstance(tableEdit,QTableView):
                if tableEdit.model()._dirty:
                    msg = "Save Changes to %s" % self.tableTabWidget.tabText(i)
                    reply = QMessageBox.question(self,"Save File",msg,
                                                 QMessageBox.Yes,QMessageBox.No)
                    if reply == QMessageBox.Yes:
                        self.fileSaveAs()
            if isinstance(tableEdit,QTabWidget):
                save=False
                for j in range(tableEdit.count()):
                    if tableEdit.widget(j).model()._dirty:
                        msg = "Save Changes to %s" % self.tableTabWidget.tabText(i)
                        reply = QMessageBox.question(self,"Save File",msg,
                                                     QMessageBox.Yes,QMessageBox.No)
                        if reply == QMessageBox.Yes:
                            msg = "Select YES to save as Excel File.\nSelect NO to save as csv."
                            reply = QMessageBox.question(self,"Excel File Detected",
                                                         msg,QMessageBox.Yes,QMessageBox.No)
                            if reply == QMessageBox.Yes:
                                save=True
                                break
                            else:
                                table=tableEdit.widget(j)
                                table.model()._filename = os.path.join(QFileInfo(table.model()._filename).absolutePath(),newName)
                                self.writeCSVOutput(table)

                if save:
                    self.writeExcelOutput(tableEdit)
                    

    def fileCloseTab(self):
        tableEdit = self.tableTabWidget.currentWidget()
        if isinstance(tableEdit,QTableView):
            tableEdit.close()
            self.tableTabWidget.removeTab(self.tableTabWidget.currentIndex())
        if isinstance(tableEdit,QTabWidget):
            self.tableTabWidget.removeTab(self.tableTabWidget.currentIndex())
            
    def fileCloseInternalTab(self):
        tableEdit = self.tableTabWidget.currentWidget()
        table = tableEdit.currentWidget()
        if isinstance(table,QTableView):
            table.close()
            tableEdit.removeTab(tableEdit.currentIndex())
        
        
    @Slot(bool)
    def enableEditing(self, enabled):

        tableEdit = self.tableTabWidget.currentWidget()
        if isinstance(tableEdit, QTableView):
            model = tableEdit.model()
        elif isinstance(tableEdit, QTabWidget):
            table = tableEdit.currentWidget()
            model = table.model()
        else:
            return


        if model is not None:
            model.enableEditing(enabled)
            if self.editEditableAction.isChecked():
                self.editAddRowAction.setEnabled(True)
                self.editAddColAction.setEnabled(True)
                self.editDelRowAction.setEnabled(True)
                self.editDelColAction.setEnabled(True)
            else:
                self.editAddRowAction.setEnabled(False)
                self.editAddColAction.setEnabled(False)
                self.editDelRowAction.setEnabled(False)
                self.editDelColAction.setEnabled(False)
                
    def okToEdit(self,model):
        if not model.editable:
            reply = QMessageBox.question(self,"Make Edits",
                               "Make this DataFrame editable?",
                               QMessageBox.Yes|QMessageBox.No|QMessageBox.Cancel)
            if reply == QMessageBox.Cancel or reply == QMessageBox.No:
                return False
            elif reply == QMessageBox.Yes:
                model.editable=True
                self.editEditableAction.setChecked(True)
                self.enableEditing(True)
                return True
            else:
                return False
        return True



    @Slot(str, object, object)
    def addColumn(self, columnName, dtype, defaultValue):
        """Adds a column with the given parameters to the underlying model

        This method is also a slot.
        If no model is set, nothing happens.

        Args:
            columnName (str): The name of the new column.
            dtype (numpy.dtype): The datatype of the new column.
            defaultValue (object): Fill the column with this value.

        """
        tableEdit = self.tableTabWidget.currentWidget()
        if isinstance(tableEdit, QTableView):
            model = tableEdit.model()
        elif isinstance(tableEdit, QTabWidget):
            tableEdit = tableEdit.currentWidget()
            model = tableEdit.model()
        else:
            return

        if model is not None:
            if self.okToEdit(model):
                model.addDataFrameColumn(columnName, dtype, defaultValue)

        self.editAddColAction.setChecked(False)

    @Slot(bool)
    def showAddColumnDialog(self):
        """Display the dialog to add a column to the model.

        This method is also a slot.

        Args:
            triggered (bool): If the corresponding button was
                activated, the dialog will be created and shown.

        """
        tableEdit = self.tableTabWidget.currentWidget()
        if isinstance(tableEdit, QTableView):
            model = tableEdit.model()
        elif isinstance(tableEdit, QTabWidget):
            tableEdit = tableEdit.currentWidget()
            model = tableEdit.model()
        else:
            return
            
        dialog = AddAttributesDialog(self)
        dialog.accepted.connect(self.addColumn)
        dialog.show()    

    def addRow(self):

        tableEdit = self.tableTabWidget.currentWidget()
        if isinstance(tableEdit, QTableView):
            model = tableEdit.model()
        elif isinstance(tableEdit, QTabWidget):
            tableEdit = tableEdit.currentWidget()
            model = tableEdit.model()
        else:
            return
            
        if model is not None:
            if self.okToEdit(model):
                model.addDataFrameRows()
                self.sender().setChecked(False)


    def removeRow(self,val=''):

        tableEdit = self.tableTabWidget.currentWidget()
        if isinstance(tableEdit, QTableView):
            model = tableEdit.model()
        elif isinstance(tableEdit, QTabWidget):
            tableEdit = tableEdit.currentWidget()
            model = tableEdit.model()
        else:
            return
            
        selection = tableEdit.selectedIndexes()

        if val == '':
            rows = [index.row() for index in selection]
        else:
            rows = [val]
            
        if model is not None:
            if self.okToEdit(model):
                model.removeDataFrameRows(set(rows))
                self.sender().setChecked(False)


    def removeColumns(self, columnNames):
        """Removes one or multiple columns from the model.

        This method is also a slot.

        Args:
            columnNames (list): A list of columns, which shall
                be removed from the model.

        """
        tableEdit = self.tableTabWidget.currentWidget()
        if isinstance(tableEdit, QTableView):
            model = tableEdit.model()
        elif isinstance(tableEdit, QTabWidget):
            model = tableEdit.currentWidget().model()
        else:
            return
        

        if model is not None:
            if self.okToEdit(model):
                model.removeDataFrameColumns(columnNames)

        self.editDelColAction.setChecked(False)

    @Slot(bool)
    def showRemoveColumnDialog(self):
        """Display the dialog to remove column(s) from the model.

        This method is also a slot.

        Args:
            triggered (bool): If the corresponding button was
                activated, the dialog will be created and shown.

        """
        tableEdit = self.tableTabWidget.currentWidget()
        if isinstance(tableEdit, QTableView):
            model = tableEdit.model()
        elif isinstance(tableEdit, QTabWidget):
            model = tableEdit.currentWidget().model()
        else:
            return
        
        if model is not None:
            columns = model.dataFrameColumns()
            dialog = RemoveAttributesDialog(columns, self)
            dialog.accepted.connect(self.removeColumns)
            dialog.show()
            
    def showFilterColDialog(self,section):

        tableEdit = self.tableTabWidget.currentWidget()
        if isinstance(tableEdit, QTableView):
            model = tableEdit.model()
        elif isinstance(tableEdit, QTabWidget):
            model = tableEdit.currentWidget().model()
        else:
            return      
 
        name = model._df.columns[section]
        values = model._df[name].values.tolist()
        
        dialog = FilterColDialog(section,name,values,self)
        dialog.accepted.connect(self.filterCol)
        dialog.show()
        
    def filterCol(self,selection):
        
        tableEdit = self.tableTabWidget.currentWidget()
        if isinstance(tableEdit, QTableView):
            model = tableEdit.model()
        elif isinstance(tableEdit, QTabWidget):
            model = tableEdit.currentWidget().model()
        else:
            return

        if model is not None:
            if self.okToEdit(model):
                model.filterCol(selection)
            
            
    def showReplaceValueDialog(self,section):
        
        tableEdit = self.tableTabWidget.currentWidget()
        if isinstance(tableEdit, QTableView):
            model = tableEdit.model()
        elif isinstance(tableEdit, QTabWidget):
            model = tableEdit.currentWidget().model()
        else:
            return      
        
        dialog = ReplaceEntryDialog(section,self)
        dialog.accepted.connect(self.replaceValue)
        dialog.show()
        
    def replaceValue(self,selection):
        
        tableEdit = self.tableTabWidget.currentWidget()
        if isinstance(tableEdit, QTableView):
            model = tableEdit.model()
        elif isinstance(tableEdit, QTabWidget):
            model = tableEdit.currentWidget().model()
        else:
            return

        if model is not None:
            if self.okToEdit(model):
                model.replaceValue(selection)

    def showFillNaNDialog(self,section):
        
        tableEdit = self.tableTabWidget.currentWidget()
        if isinstance(tableEdit, QTableView):
            model = tableEdit.model()
        elif isinstance(tableEdit, QTabWidget):
            model = tableEdit.currentWidget().model()
        else:
            return      
        
        dialog = FillNaNDialog(section,self)
        dialog.accepted.connect(self.fillNaN)
        dialog.show()
        
    def fillNaN(self,selection):
        
        tableEdit = self.tableTabWidget.currentWidget()
        if isinstance(tableEdit, QTableView):
            model = tableEdit.model()
        elif isinstance(tableEdit, QTabWidget):
            model = tableEdit.currentWidget().model()
        else:
            return

        if model is not None:
            if self.okToEdit(model):
                model.fillNaN(selection)
            
    def showGroupDialog(self):
        if self.tableTabWidget.count() == 0:
            QMessageBox.warning(self,"DataFrameViewer Error",
            "No initial DataFrame opened.\nPlease open a DataFrame.")
        else:
            tableEdit = self.tableTabWidget.currentWidget()
            if isinstance(tableEdit, QTableView):
                data = tableEdit
                idx = self.tableTabWidget.currentIndex()
            elif isinstance(tableEdit,QTabWidget):
                data = tableEdit.currentWidget()
                idx = [self.tableTabWidget.currentIndex(),tableEdit.currentIndex()]
            else:
                return
            if not data.model()._grouping:
                options={'data':data,'idx':idx}
                tableEdit.model()._grouping=True
                dialog = GroupByDialog(options,self)
                dialog.changed.connect(self.doGroupBy)
                dialog.show()
            
    def doGroupBy(self,opts):

        if opts['key'] == "Accept":
            if opts['newTab'] == True:
                for i in range(self.tableTabWidget.count()):
                    tableEdit = self.tableTabWidget.widget(i)
                    if isinstance(tableEdit,QTableView):
                        if tableEdit.model()._filename == opts['name']:
                            self.tableTabWidget.setCurrentWidget(tableEdit)
                            break
                    
                else: 
                    table = QTableView()
                    model=DataFrameTableModel(filename=opts['name'])
                    model.trackDataChange.connect(self.trackChanges)
                    table.setModel(model)
                    ### Set some variables ###
                    table.headers = table.horizontalHeader()
                    table.vHeaders=table.verticalHeader()
                    #### Set context menu for table headers ####
                    table.headers.setContextMenuPolicy(Qt.CustomContextMenu)
                    table.headers.customContextMenuRequested.connect(self.headerMenu)
                    table.vHeaders.setContextMenuPolicy(Qt.CustomContextMenu)
                    table.vHeaders.customContextMenuRequested.connect(self.vHeaderMenu)
                    
                    model.setDataFrame(opts['df'])
                    self.tableTabWidget.addTab(table, opts['name'])
                    self.tableTabWidget.setCurrentWidget(table)
            else:
                if type(opts['idx']) == int:
                    self.tableTabWidget.setCurrentIndex(opts['idx'])
                    self.tableTabWidget.widget(opts['idx']).model().setDataFrame(opts['df'])
                    self.tableTabWidget.setTabText(opts['idx'],opts['name'])
                if type(opts['idx']) == list:
                    self.tableTabWidget.setCurrentIndex(opts['idx'][0])
                    self.tableTabWidget.widget(opts['idx'][0]).setCurrentIndex(opts['idx'][1])
                    self.tableTabWidget.widget(opts['idx'][0]).widget(opts['idx'][1]).model().setDataFrame(opts['df'])
                    self.tableTabWidget.widget(opts['idx'][0]).setTabText(opts['idx'][1],opts['name'])
        
        elif opts['key'] == "Reject":
            if len(opts) > 2:
                if type(opts['idx']) == int:
                    self.tableTabWidget.setCurrentIndex(opts['idx'])
                    self.tableTabWidget.widget(opts['idx']).model().setDataFrame(opts['df'])
                    self.tableTabWidget.setTabText(opts['idx'],opts['name'])
                if type(opts['idx']) == list:
                    self.tableTabWidget.setCurrentIndex(opts['idx'][0])
                    self.tableTabWidget.widget(opts['idx'][0]).setCurrentIndex(opts['idx'][1])
                    self.tableTabWidget.widget(opts['idx'][0]).widget(opts['idx'][1]).model().setDataFrame(opts['df'])
                    self.tableTabWidget.widget(opts['idx'][0]).setTabText(opts['idx'][1],opts['name'])
            if type(opts['idx']) == int:
                self.tableTabWidget.setCurrentIndex(opts['idx'])
                self.tableTabWidget.widget(opts['idx']).model()._grouping = False
            if type(opts['idx']) == list:
                    self.tableTabWidget.setCurrentIndex(opts['idx'][0])
                    self.tableTabWidget.widget(opts['idx'][0]).setCurrentIndex(opts['idx'][1])
                    self.tableTabWidget.widget(opts['idx'][0]).widget(opts['idx'][1]).model()._grouping = False
        else:
            pass
            
    def showMergeDialog(self):
        if self.tableTabWidget.count() == 0:
            QMessageBox.warning(self,"DataFrameViewer Error",
            "No initial DataFrame opened.\nPlease open a DataFrame.")
        elif self.tableTabWidget.count() < 2:
            QMessageBox.warning(self,"DataFrameViewer Error",
            "Only one DataFrame opened.\nPlease open another DataFrame to merge with.")
        else:
            available = OrderedDict()
            status = {}
            for i in range(self.tableTabWidget.count()):
                tableEdit = self.tableTabWidget.widget(i)
                if isinstance(tableEdit,QTableView):
                    status['cols']=tableEdit.model()._df.columns
                    status['view']=True
                    status['idx']=i
                    status['name']=self.tableTabWidget.tabText(i)
                    available[self.tableTabWidget.tabText(i)]=status.copy()
                if isinstance(tableEdit,QTabWidget):
                    for j in range(tableEdit.count()):
                        table = tableEdit.widget(j)
                        if isinstance(table,QTableView):
                            status['cols']=table.model()._df.columns
                            status['view']=False
                            status['idx']=[i,j]
                            status['name']=tableEdit.tabText(j)
                            available[self.tableTabWidget.tabText(i)+'_'+tableEdit.tabText(j)]=status.copy()

            if len(available) > 0:
                dialog = MergeDataFrameDialog(available,self)
                dialog.accepted.connect(self.doMerge)
                dialog.show()

    def doMerge(self,options):
        merge_options = options['merge_options']
        left = options['left']
        right = options['right']
        title = 'Merged_' + left['name'] + '_' + right['name']
        if merge_options.has_key('how'):
            how=merge_options['how']
        if merge_options.has_key('on'):
            on=merge_options['on']
        else:
            on=None
        if merge_options.has_key('left_on'):
            left_on=merge_options['left_on']
        else:
            left_on=None
        if merge_options.has_key('right_on'):
            right_on=merge_options['right_on']
        else:
            right_on=None
        if merge_options.has_key('left_index'):
            left_index=merge_options['left_index']
        else:
            left_index=False
        if merge_options.has_key('right_index'):
            right_index=merge_options['right_index']
        else:
            right_index=None
        if merge_options.has_key('suffix_x'):
            suffix_x=merge_options['suffix_x']
        else:
            suffix_x = '_x'
        if merge_options.has_key('suffix_y'):
            suffix_y=merge_options['suffix_y']
        else:
            suffix_y = '_y'
        suffixes = (suffix_x,suffix_y)
        
        if type(left['idx']) == int:
            left_df=self.tableTabWidget.widget(left['idx']).model()._df
        if type(left['idx']) == list:
            tab=self.tableTabWidget.widget(left['idx'][0])
            left_df=tab.widget(left['idx'][1]).model()._df
        if type(right['idx']) == int:
            right_df=self.tableTabWidget.widget(right['idx']).model()._df
        if type(right['idx']) == list:
            tab=self.tableTabWidget.widget(right['idx'][0])
            right_df=tab.widget(right['idx'][1]).model()._df
            
        df=pd.merge(left_df,right_df,how=how,on=on,left_on=left_on,right_on=right_on,
                    left_index=left_index,right_index=right_index,suffixes=suffixes)
            
        table = QTableView()
        model=DataFrameTableModel(filename=title)
        model.trackDataChange.connect(self.trackChanges)
        table.setModel(model)
        ### Set some variables ###
        table.headers = table.horizontalHeader()
        table.vHeaders=table.verticalHeader()
        #### Set context menu for table headers ####
        table.headers.setContextMenuPolicy(Qt.CustomContextMenu)
        table.headers.customContextMenuRequested.connect(self.headerMenu)
        table.vHeaders.setContextMenuPolicy(Qt.CustomContextMenu)
        table.vHeaders.customContextMenuRequested.connect(self.vHeaderMenu)
        
        model.setDataFrame(df)
        model._dirty = True
        self.tableTabWidget.addTab(table, title)
        self.tableTabWidget.setCurrentWidget(table)
        
    def showDescribeDialog(self):

        if self.tableTabWidget.count() == 0:
            QMessageBox.warning(self,"DataFrameViewer Error",
            "No DataFrame to Describe.\nPlease open a DataFrame.")        
        else:
            tableEdit = self.tableTabWidget.currentWidget()
            if isinstance(tableEdit,QTableView):
                x = tableEdit.model()._df.describe()
            if isinstance(tableEdit,QTabWidget):
                table=tableEdit.currentWidget()
                x = table.model()._df.describe()
                
            dialog = DescribeDialog(x,self)
            dialog.show()
            
    def showGraphDialog(self):
        
        data = {}
        if self.tableTabWidget.count() == 0:
            QMessageBox.warning(self,"DataFrameViewer Error",
            "No DataFrame to Graph.\nPlease open a DataFrame.")
        else:
            for i in range(self.tableTabWidget.count()):
                tableEdit = self.tableTabWidget.widget(i)
                if isinstance(tableEdit, QTableView):
                    data[self.tableTabWidget.tabText(i)]=tableEdit.model()._df
                if isinstance(tableEdit, QTabWidget):
                    for j in range(tableEdit.count()):
                        table=tableEdit.widget(j)
                        name=QFileInfo(table.model()._filename).fileName()+'_'+tableEdit.tabText(j)
                        data[name]=table.model()._df
                        
            dialog = GraphFormatDialog(data,self)
            dialog.show()
        
    def parseDelimiter(self,f):
        
        infile = open(f)
        lines = infile.readlines()
        infile.close()
        
        sniffer = csv.Sniffer()
        text = sniffer.sniff(lines[0])
        return text.delimiter
                
        

###############################################################################
# The following are GUI shortcut tools
###############################################################################
    ## Create an action for GUIs
    def createAction(self, text, slot = None, shortcut = None, icon = None,
                     tip = None, checkable = False, signal = "triggered()"):
        action = QAction(text,self)
        if icon is not None:
            action.setIcon(QIcon(":/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, SIGNAL(signal),slot)
        if checkable:
            action.setCheckable(True)
        return action
        
    def addActions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)    
        
    ## Create a button
    def createButton(self,text, kind= "push", checkable = False):
            
        if kind == "push":
            button = QPushButton(text)
        if kind == "radio":
            button = QRadioButton(text)
        if kind == "check":
            button = QCheckBox(text)
        if checkable:
            button.setEnabled(True)
        return button
###############################################################################
###############################################################################
 
if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = DataFrameViewer()
    form.show()
    app.exec_()