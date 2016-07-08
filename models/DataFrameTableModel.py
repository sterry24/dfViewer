import pandas as pd
import numpy as np

from PyQt4.QtCore import *
from PyQt4.QtCore import pyqtSlot as Slot
from PyQt4.QtCore import pyqtSignal as Signal
from PyQt4.QtGui import *

from models.SupportedDtypes import SupportedDtypes

__author__  = "Stephen Terry"
__version__ = "1.0.0"

class DataFrameTableModel(QAbstractTableModel):

    _float_precisions = {
        "float16": np.finfo(np.float16).precision - 2,
        "float32": np.finfo(np.float32).precision - 1,
        "float64": np.finfo(np.float64).precision - 1
    }

    """list of int datatypes for easy checking in data() and setData()"""
    _intDtypes = SupportedDtypes.intTypes() + SupportedDtypes.uintTypes()
    """list of float datatypes for easy checking in data() and setData()"""
    _floatDtypes = SupportedDtypes.floatTypes()
    """list of bool datatypes for easy checking in data() and setData()"""
    _boolDtypes = SupportedDtypes.boolTypes()
    """list of datetime datatypes for easy checking in data() and setData()"""
    _dateDtypes = SupportedDtypes.datetimeTypes()

    _timestampFormat = Qt.ISODate

    sortingStart = Signal()
    sortingFinish = Signal()
    dtypeChanged = Signal(int, object)
    changingDtypeFailed = Signal(object, QModelIndex, object)
    dataChanged = Signal()
    dataFrameChanged = Signal()
    trackDataChange = Signal()
    
    def __init__(self, filename="", dataFrame=None, copyDataFrame=False):
        
        super(DataFrameTableModel, self).__init__()

        self._filename = filename
        self._dirty = False
        self._df = pd.DataFrame()
        self._grouping = False
        self._changes = []
        self._currChange = 0
        if dataFrame is not None:
            self.setDataFrame(dataFrame, copyDataFrame=copyDataFrame)
        #self.dataChanged.emit()
        
        self.editable = False
        
    def dataFrame(self):

        return self._df

    def setDataFrame(self, dataFrame, copyDataFrame=False):

        if not isinstance(dataFrame, pd.core.frame.DataFrame):
            raise TypeError("not of type pandas.core.frame.DataFrame")

        self.layoutAboutToBeChanged.emit()
        if copyDataFrame:
            self._df = dataFrame.copy()
        else:
            self._df = dataFrame

#        self._columnDtypeModel = ColumnDtypeModel(dataFrame)
#        self._columnDtypeModel.dtypeChanged.connect(self.propagateDtypeChanges)
#        self._columnDtypeModel.changeFailed.connect(
#            lambda columnName, index, dtype: self.changingDtypeFailed.emit(columnName, index, dtype)
#        )
        self.layoutChanged.emit()
        self.dataChanged.emit()
        self.dataFrameChanged.emit()
        self._changes.insert(self._currChange,self._df.copy())

        
    @Slot(int, object)
    def propagateDtypeChanges(self, column, dtype):
        self.dtypeChanged.emit(column, dtype)

    @property
    def timestampFormat(self):

        return self._timestampFormat

    @timestampFormat.setter
    def timestampFormat(self, timestampFormat):

        if not isinstance(timestampFormat, (unicode, )):
            raise TypeError('not of type unicode')

        self._timestampFormat = timestampFormat
        
###### The following methods are for Read-Only models #########################
    def rowCount(self, index=QModelIndex()):
        
        return len(self._df.index)

    def columnCount(self, index=QModelIndex()):
        
        return len(self._df.columns)
        
    def data(self, index, role=Qt.DisplayRole):

        if role == Qt.DisplayRole:
            i=index.row()
            j=index.column()
            #return '{0}'.format(self._df.iget_value(i,j))
            return '{0}'.format(self._df.iat[i,j])
        else:
            return None
            
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            try:
                return self._df.columns.tolist()[section]
            except (IndexError, ):
                return None

        elif orientation == Qt.Vertical:
            try:
                if type(self._df.index.tolist()[section]) == str:
                    return self._df.index.tolist()[section]
                else:
                    return int(section)
            except (IndexError, ):
                return None
###############################################################################
                
###### The following methods are for editable models ##########################
    def flags(self, index):

        flags = super(DataFrameTableModel, self).flags(index)

        if not self.editable:
            return flags

        col = self._df.columns[index.column()]
        if self._df[col].dtype == np.bool:
            flags |= Qt.ItemIsUserCheckable
        else:
            # if you want to have a combobox for bool columns set this
            flags |= Qt.ItemIsEditable

        return flags
        
    def setData(self, index, value, role=Qt.DisplayRole):

        if not index.isValid() or not self.editable:
            return False

        if value != index.data(role):

            self.layoutAboutToBeChanged.emit()

            row = self._df.index[index.row()]
            col = self._df.columns[index.column()]
            columnDtype = self._df[col].dtype


            if columnDtype == object:
                pass

            elif columnDtype in self._intDtypes:
                dtypeInfo = np.iinfo(columnDtype)
                value = np.int64(value).astype(columnDtype)
                if value < dtypeInfo.min:
                    value = dtypeInfo.min
                elif value > dtypeInfo.max:
                    value = dtypeInfo.max
                else:
                    pass

            elif columnDtype in self._floatDtypes:
                value = np.float64(value).astype(columnDtype)

            elif columnDtype in self._boolDtypes:
                value = np.bool_(value)

            elif columnDtype in self._dateDtypes:
                # convert the given value to a compatible datetime object.
                # if the conversation could not be done, keep the original
                # value.
                if isinstance(value, QDateTime):
                    value = value.toString(self.timestampFormat)
                try:
                    value = pd.Timestamp(value)
                except Exception:
                    raise Exception(u"Can't convert '{0}' into a datetime".format(value))
                    return False
            else:
                raise TypeError("try to set unhandled data type")

            self._df.set_value(row, col, value)

            #print 'after change: ', value, self._df.iloc[row][col]
            self._dirty = True
            self.layoutChanged.emit()
            self.dataChanged.emit()
            self.trackDataChange.emit()
            return True
        else:
            return False
            
    def addDataFrameColumn(self, columnName, dtype, defaultValue):
        if not self.editable or dtype not in SupportedDtypes.allTypes():
            return False

        elements = self.rowCount()
        columnPosition = self.columnCount()

        newColumn = pd.Series([defaultValue]*elements, index=self._df.index, dtype=dtype)

        self.beginInsertColumns(QModelIndex(), columnPosition - 1, columnPosition - 1)
        try:
            self._df.insert(columnPosition, columnName, newColumn, allow_duplicates=False)
        except ValueError as e:
            # columnName does already exist
            return False

        self.endInsertColumns()
        self._dirty = True
        self.layoutChanged.emit()
        self.dataChanged.emit()
        self.trackDataChange.emit()
        self.propagateDtypeChanges(columnPosition, newColumn.dtype)

        return True

    def addDataFrameRows(self, count=1):
        # don't allow any gaps in the data rows.
        # and always append at the end

        if not self.editable:
            return False

        position = self.rowCount()

        if count < 1:
            return False

        ## What is self.dataFrame()
        if len(self.dataFrame().columns) == 0:
            # log an error message or warning
            return False

        # Note: This function emits the rowsAboutToBeInserted() signal which
        # connected views (or proxies) must handle before the data is
        # inserted. Otherwise, the views may end up in an invalid state.
        self.beginInsertRows(QModelIndex(), position, position + count - 1)

        defaultValues = []
        for dtype in self._df.dtypes:
            if dtype.type == np.dtype('<M8[ns]'):
                val = pd.Timestamp('')
            elif dtype.type == np.dtype(object):
                val = ''
            else:
                val = dtype.type()
            defaultValues.append(val)

        for i in range(count):
            self._df.loc[position + i] = defaultValues
        self._df.reset_index()
        self.endInsertRows()
        self._dirty = True
        self.layoutChanged.emit()
        self.dataChanged.emit()
        self.trackDataChange.emit()
        return True                      

    def removeDataFrameColumns(self, columns):
        if not self.editable:
            return False

        if columns:
            deleted = 0
            errorOccured = False
            for (position, name) in columns:
                position = position - deleted
                if position < 0:
                    position = 0
                self.beginRemoveColumns(QModelIndex(), position, position)
                try:
                    self._df.drop(name, axis=1, inplace=True)
                except ValueError as e:
                    errorOccured = True
                    continue
                self.endRemoveColumns()
                deleted += 1
            self._dirty = True
            self.layoutChanged.emit()
            self.dataChanged.emit()
            self.trackDataChange.emit()

            if errorOccured:
                return False
            else:
                return True
        return False

    def removeDataFrameRows(self, rows):
        if not self.editable:
            return False

        if rows:
            position = min(rows)
            count = len(rows)
            self.beginRemoveRows(QModelIndex(), position, position + count - 1)

            removedAny = False
            for idx, line in self._df.iterrows():
                if idx in rows:
                    removedAny = True
                    self._df.drop(idx, inplace=True)

            if not removedAny:
                return False

            self._df.reset_index(inplace=True, drop=True)

            self.endRemoveRows()
            self._dirty = True
            self.layoutChanged.emit()
            self.dataChanged.emit()
            self.trackDataChange.emit()
            return True
        return False
            
    def replaceValue(self,options):
        if not self.editable:
            return False
            
        col=self._df.columns[options[2]]
            
        if options[0] != '':
            if options[1] != '':
                if options[1].isdigit():
                    options[1]=int(options[1])
                elif options[1].find('.') == 0:
                    if options[1][1:].isdigit():
                        options[1]=float(options[1])
                elif options[1].find('.') >= 0:
                    if options[1][:options[1].find('.')].isdigit():
                        options[1]=float(options[1])
                else:
                    pass
                self._df[col].replace(to_replace=options[0],
                                           value=options[1],inplace=True)
                self._dirty = True            
                self.layoutChanged.emit()
                self.dataChanged.emit() 
                self.trackDataChange.emit()
                
    def filterCol(self,options):
        err = False
        if not self.editable:
            return False
            
        name = options['name']
        operator = options['operator']
        filterOne = options['filterOne']
        if options['valueOne'].find('.') == 0:
            if options['valueOne'][options['valueOne'].find('.'):].isdigit():
                options['valueOne']=float(options['valueOne'])
        elif options['valueOne'].find('.') > 0:
            if ((options['valueOne'][:options['valueOne'].find('.')].isdigit()) and
                (options['valueOne'][options['valueOne'].find('.')+1:].isdigit())):
                options['valueOne']=float(options['valueOne'])
        else:
            try:
                options['valueOne']=int(options['valueOne'])
            except ValueError:
                err = True
                
        if options['filterTwo'] == '' and not err:
            if filterOne == "==":
                self._df=self._df[self._df[name] == options['valueOne']]
            elif filterOne == "!=":
                self._df=self._df[self._df[name] != options['valueOne']]
            elif filterOne == "<":
                self._df=self._df[self._df[name] < options['valueOne']]
            elif filterOne == "<=":
                self._df=self._df[self._df[name] <= options['valueOne']]
            elif filterOne == ">":
                self._df=self._df[self._df[name] > options['valueOne']]
            elif filterOne == ">=":
                self._df=self._df[self._df[name] >= options['valueOne']]
            else:
                pass
        elif options['filterTwo'] != '' and not err:

            filterTwo = options['filterTwo']
            if options['valueTwo'].find('.') == 0:
                if options['valueTwo'][options['valueTwo'].find('.'):].isdigit():
                    options['valueTwo']=float(options['valueTwo'])
            elif options['valueTwo'].find('.') > 0:
                if ((options['valueTwo'][:options['valueTwo'].find('.')-1].isdigit()) and
                    (options['valueTwo'][options['valueTwo'].find('.'):].isdigit())):
                    options['valueTwo']=float(options['valueTwo'])
            else:
                try:
                    options['valueTwo']=int(options['valueTwo'])
                except ValueError:
                    err = True
            if not err:
                if filterOne == "==":
                    if operator == '&':
                        if filterTwo == "==":
                            self._df=self._df[(self._df[name] == options['valueOne'])
                                             & (self._df[name] == options['valueTwo'])]
                        elif filterTwo == "!=":
                            self._df=self._df[(self._df[name] == options['valueOne'])
                                             & (self._df[name] != options['valueTwo'])]
                        elif filterTwo == "<":
                            self._df=self._df[(self._df[name] == options['valueOne'])
                                             & (self._df[name] < options['valueTwo'])]
                        elif filterTwo == "<=":
                            self._df=self._df[(self._df[name] == options['valueOne'])
                                             & (self._df[name] <= options['valueTwo'])]
                        elif filterTwo == ">":
                            self._df=self._df[(self._df[name] == options['valueOne'])
                                             & (self._df[name] > options['valueTwo'])]
                        elif filterTwo == ">=":
                            self._df=self._df[(self._df[name] == options['valueOne'])
                                             & (self._df[name] >= options['valueTwo'])]
                        else:
                            pass
                    if operator == '|':
                        if filterTwo == "==":
                            self._df=self._df[(self._df[name] == options['valueOne'])
                                             | (self._df[name] == options['valueTwo'])]
                        elif filterTwo == "!=":
                            self._df=self._df[(self._df[name] == options['valueOne'])
                                             | (self._df[name] != options['valueTwo'])]
                        elif filterTwo == "<":
                            self._df=self._df[(self._df[name] == options['valueOne'])
                                             | (self._df[name] < options['valueTwo'])]
                        elif filterTwo == "<=":
                            self._df=self._df[(self._df[name] == options['valueOne'])
                                             | (self._df[name] <= options['valueTwo'])]
                        elif filterTwo == ">":
                            self._df=self._df[(self._df[name] == options['valueOne'])
                                             | (self._df[name] > options['valueTwo'])]
                        elif filterTwo == ">=":
                            self._df=self._df[(self._df[name] == options['valueOne'])
                                             | (self._df[name] >= options['valueTwo'])]
                        else:
                            pass
                elif filterOne == "!=":
                    if operator == '&':
                        if filterTwo == "==":
                            self._df=self._df[(self._df[name] != options['valueOne'])
                                             & (self._df[name] == options['valueTwo'])]
                        elif filterTwo == "!=":
                            self._df=self._df[(self._df[name] != options['valueOne'])
                                             & (self._df[name] != options['valueTwo'])]
                        elif filterTwo == "<":
                            self._df=self._df[(self._df[name] != options['valueOne'])
                                             & (self._df[name] < options['valueTwo'])]
                        elif filterTwo == "<=":
                            self._df=self._df[(self._df[name] != options['valueOne'])
                                             & (self._df[name] <= options['valueTwo'])]
                        elif filterTwo == ">":
                            self._df=self._df[(self._df[name] != options['valueOne'])
                                             & (self._df[name] > options['valueTwo'])]
                        elif filterTwo == ">=":
                            self._df=self._df[(self._df[name] != options['valueOne'])
                                             & (self._df[name] >= options['valueTwo'])]
                        else:
                            pass
                    if operator == '|':
                        if filterTwo == "==":
                            self._df=self._df[(self._df[name] != options['valueOne'])
                                             | (self._df[name] == options['valueTwo'])]
                        elif filterTwo == "!=":
                            self._df=self._df[(self._df[name] != options['valueOne'])
                                             | (self._df[name] != options['valueTwo'])]
                        elif filterTwo == "<":
                            self._df=self._df[(self._df[name] != options['valueOne'])
                                             | (self._df[name] < options['valueTwo'])]
                        elif filterTwo == "<=":
                            self._df=self._df[(self._df[name] != options['valueOne'])
                                             | (self._df[name] <= options['valueTwo'])]
                        elif filterTwo == ">":
                            self._df=self._df[(self._df[name] != options['valueOne'])
                                             | (self._df[name] > options['valueTwo'])]
                        elif filterTwo == ">=":
                            self._df=self._df[(self._df[name] != options['valueOne'])
                                             | (self._df[name] >= options['valueTwo'])]
                        else:
                            pass
                elif filterOne == "<":
                    if operator == '&':
                        if filterTwo == "==":
                            self._df=self._df[(self._df[name] < options['valueOne'])
                                             & (self._df[name] == options['valueTwo'])]
                        elif filterTwo == "!=":
                            self._df=self._df[(self._df[name] < options['valueOne'])
                                             & (self._df[name] != options['valueTwo'])]
                        elif filterTwo == "<":
                            self._df=self._df[(self._df[name] < options['valueOne'])
                                             & (self._df[name] < options['valueTwo'])]
                        elif filterTwo == "<=":
                            self._df=self._df[(self._df[name] < options['valueOne'])
                                             & (self._df[name] <= options['valueTwo'])]
                        elif filterTwo == ">":
                            self._df=self._df[(self._df[name] < options['valueOne'])
                                             & (self._df[name] > options['valueTwo'])]
                        elif filterTwo == ">=":
                            self._df=self._df[(self._df[name] < options['valueOne'])
                                             & (self._df[name] >= options['valueTwo'])]
                        else:
                            pass
                    if operator == '|':
                        if filterTwo == "==":
                            self._df=self._df[(self._df[name] < options['valueOne'])
                                             | (self._df[name] == options['valueTwo'])]
                        elif filterTwo == "!=":
                            self._df=self._df[(self._df[name] < options['valueOne'])
                                             | (self._df[name] != options['valueTwo'])]
                        elif filterTwo == "<":
                            self._df=self._df[(self._df[name] < options['valueOne'])
                                             | (self._df[name] < options['valueTwo'])]
                        elif filterTwo == "<=":
                            self._df=self._df[(self._df[name] < options['valueOne'])
                                             | (self._df[name] <= options['valueTwo'])]
                        elif filterTwo == ">":
                            self._df=self._df[(self._df[name] < options['valueOne'])
                                             | (self._df[name] > options['valueTwo'])]
                        elif filterTwo == ">=":
                            self._df=self._df[(self._df[name] < options['valueOne'])
                                             | (self._df[name] >= options['valueTwo'])]
                        else:
                            pass
                elif filterOne == "<=":
                    if operator == '&':
                        if filterTwo == "==":
                            self._df=self._df[(self._df[name] <= options['valueOne'])
                                             & (self._df[name] == options['valueTwo'])]
                        elif filterTwo == "!=":
                            self._df=self._df[(self._df[name] <= options['valueOne'])
                                             & (self._df[name] != options['valueTwo'])]
                        elif filterTwo == "<":
                            self._df=self._df[(self._df[name] <= options['valueOne'])
                                             & (self._df[name] < options['valueTwo'])]
                        elif filterTwo == "<=":
                            self._df=self._df[(self._df[name] <= options['valueOne'])
                                             & (self._df[name] <= options['valueTwo'])]
                        elif filterTwo == ">":
                            self._df=self._df[(self._df[name] <= options['valueOne'])
                                             & (self._df[name] > options['valueTwo'])]
                        elif filterTwo == ">=":
                            self._df=self._df[(self._df[name] <= options['valueOne'])
                                             & (self._df[name] >= options['valueTwo'])]
                        else:
                            pass
                    if operator == '|':
                        if filterTwo == "==":
                            self._df=self._df[(self._df[name] <= options['valueOne'])
                                             | (self._df[name] == options['valueTwo'])]
                        elif filterTwo == "!=":
                            self._df=self._df[(self._df[name] <= options['valueOne'])
                                             | (self._df[name] != options['valueTwo'])]
                        elif filterTwo == "<":
                            self._df=self._df[(self._df[name] <= options['valueOne'])
                                             | (self._df[name] < options['valueTwo'])]
                        elif filterTwo == "<=":
                            self._df=self._df[(self._df[name] <= options['valueOne'])
                                             | (self._df[name] <= options['valueTwo'])]
                        elif filterTwo == ">":
                            self._df=self._df[(self._df[name] <= options['valueOne'])
                                             | (self._df[name] > options['valueTwo'])]
                        elif filterTwo == ">=":
                            self._df=self._df[(self._df[name] <= options['valueOne'])
                                             | (self._df[name] >= options['valueTwo'])]
                        else:
                            pass
                elif filterOne == ">":
                    if operator == '&':
                        if filterTwo == "==":
                            self._df=self._df[(self._df[name] > options['valueOne'])
                                             & (self._df[name] == options['valueTwo'])]
                        elif filterTwo == "!=":
                            self._df=self._df[(self._df[name] > options['valueOne'])
                                             & (self._df[name] != options['valueTwo'])]
                        elif filterTwo == "<":
                            self._df=self._df[(self._df[name] > options['valueOne']) & 
                                              (self._df[name] < options['valueTwo'])]
                        elif filterTwo == "<=":
                            self._df=self._df[(self._df[name] > options['valueOne'])
                                             & (self._df[name] <= options['valueTwo'])]
                        elif filterTwo == ">":
                            self._df=self._df[(self._df[name] > options['valueOne'])
                                             & (self._df[name] > options['valueTwo'])]
                        elif filterTwo == ">=":
                            self._df=self._df[(self._df[name] > options['valueOne'])
                                             & (self._df[name] >= options['valueTwo'])]
                        else:
                            pass
                    if operator == '|':
                        if filterTwo == "==":
                            self._df=self._df[(self._df[name] > options['valueOne'])
                                             | (self._df[name] == options['valueTwo'])]
                        elif filterTwo == "!=":
                            self._df=self._df[(self._df[name] > options['valueOne'])
                                             | (self._df[name] != options['valueTwo'])]
                        elif filterTwo == "<":
                            #print("Right one: > <")
                            self._df=self._df[(self._df[name] > options['valueOne'])
                                             | (self._df[name] < options['valueTwo'])]
                        elif filterTwo == "<=":
                            self._df=self._df[(self._df[name] > options['valueOne'])
                                             | (self._df[name] <= options['valueTwo'])]
                        elif filterTwo == ">":
                            self._df=self._df[(self._df[name] > options['valueOne'])
                                             | (self._df[name] > options['valueTwo'])]
                        elif filterTwo == ">=":
                            self._df=self._df[(self._df[name] > options['valueOne'])
                                             | (self._df[name] >= options['valueTwo'])]
                        else:
                            pass
                elif filterOne == ">=":
                    if operator == '&':
                        if filterTwo == "==":
                            self._df=self._df[(self._df[name] >= options['valueOne'])
                                             & (self._df[name] == options['valueTwo'])]
                        elif filterTwo == "!=":
                            self._df=self._df[(self._df[name] >= options['valueOne'])
                                             & (self._df[name] != options['valueTwo'])]
                        elif filterTwo == "<":
                            self._df=self._df[(self._df[name] >= options['valueOne'])
                                             & (self._df[name] < options['valueTwo'])]
                        elif filterTwo == "<=":
                            self._df=self._df[(self._df[name] >= options['valueOne'])
                                             & (self._df[name] <= options['valueTwo'])]
                        elif filterTwo == ">":
                            self._df=self._df[(self._df[name] >= options['valueOne'])
                                             & (self._df[name] > options['valueTwo'])]
                        elif filterTwo == ">=":
                            self._df=self._df[(self._df[name] >= options['valueOne'])
                                             & (self._df[name] >= options['valueTwo'])]
                        else:
                            pass
                    if operator == '|':
                        if filterTwo == "==":
                            self._df=self._df[(self._df[name] >= options['valueOne'])
                                             | (self._df[name] == options['valueTwo'])]
                        elif filterTwo == "!=":
                            self._df=self._df[(self._df[name] >= options['valueOne'])
                                             | (self._df[name] != options['valueTwo'])]
                        elif filterTwo == "<":
                            self._df=self._df[(self._df[name] >= options['valueOne'])
                                             | (self._df[name] < options['valueTwo'])]
                        elif filterTwo == "<=":
                            self._df=self._df[(self._df[name] >= options['valueOne'])
                                             | (self._df[name] <= options['valueTwo'])]
                        elif filterTwo == ">":
                            self._df=self._df[(self._df[name] >= options['valueOne'])
                                             | (self._df[name] > options['valueTwo'])]
                        elif filterTwo == ">=":
                            self._df=self._df[(self._df[name] >= options['valueOne'])
                                             | (self._df[name] >= options['valueTwo'])]
                        else:
                            pass
                else:
                    pass
        

        if err:
            QMessageBox.warning(self,"Filter Error","Error converting input to number.\n"
                                "Please ensure that you entered a numeric value.")
        else:
            self._df=self._df.copy()
            self._dirty = True          
            self.layoutChanged.emit()
            self.dataChanged.emit()            
            self.trackDataChange.emit()
        

    def fillNaN(self,options):
        if not self.editable:
            return False
            
        col=self._df.columns[options[2]]
        if options[0] == 'None':
            if options[1].isdigit():
                options[1]=int(options[1])
            elif options[1].find('.') == 0:
                if options[1][1:].isdigit():
                    options[1]=float(options[1])
            elif options[1].find('.') >= 0:
                if options[1][:options[1].find('.')].isdigit():
                    options[1]=float(options[1])
            else:
                pass
            self._df[col].fillna(value=options[1],inplace=True)
            self._dirty = True     
            self.layoutChanged.emit()
            self.dataChanged.emit()
            self.trackDataChange.emit()
        else:
            self._df[col].fillna(method=options[0],inplace=True)
            self._dirty = True            
            self.layoutChanged.emit()
            self.dataChanged.emit()
            self.trackDataChange.emit()
            
    def undo(self):
        if not self.editable:
            return False
            
        if self._currChange > 0:
            self._df = self._changes[self._currChange-1].copy()
            self._currChange = self._currChange - 1
            self.layoutChanged.emit()
            self.dataChanged.emit()
            self.dataFrameChanged.emit()
    
    def redo(self):
        if not self.editable:
            return False
            
        if self._currChange + 1 <= len(self._changes) - 1:
            self._df = self._changes[self._currChange + 1].copy()
            self._currChange = self._currChange + 1
            self.layoutChanged.emit()
            self.dataChanged.emit()
            self.dataFrameChanged.emit()
        
    def convertColumnsToNumeric(self,section):
        col=self._df.columns[section]
        self._df[col]=pd.to_numeric(self._df[col])
        self._dirty = True  
        self.dataChanged.emit()
    
    def convertColumnsToDate(self,section):
        col=self._df.columns[section]
        self._df[col]=pd.to_datetime(self._df[col])
        self._dirty = True  
        self.dataChanged.emit()
        
    def convertColumnsToTimeDeltas(self,section):
        col=self._df.columns[section]
        self._df[col]=pd.to_timedelta(self._df[col])
        self._dirty = True  
        self.dataChanged.emit()

###############################################################################        

    def enableEditing(self, editable):
        self.editable = editable

    def dataFrameColumns(self):
        return self._df.columns.tolist()
        
    def columnDtypeModel(self):

        return self._columnDtypeModel
        
    def sort(self, columnId, order=Qt.AscendingOrder):

        self.layoutAboutToBeChanged.emit()
        self.sortingStart.emit()
        column = self._df.columns[columnId]
        self._df.sort(column, ascending=bool(order), kind='mergesort', inplace=True)
        self.layoutChanged.emit()
        self.sortingFinish.emit()
        self.trackDataChange.emit()
                