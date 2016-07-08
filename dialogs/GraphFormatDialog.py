import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

__author__  = "Stephen Terry"
__version__ = "1.0.0"


class GraphFormatDialog(QDialog):
    
    def __init__(self,options,parent=None):
        
        super(GraphFormatDialog,self).__init__(parent)
        ## Set some variables
        self.colors={'blue':'b','green':'g','red':'r','cyan':'c','magenta':'m',
                     'yellow':'y','black':'k','white':'w'}
        self.line_options={'none':'','solid':'-','dashed':'--','dotted':':','dashdot':'-.'}
        self.markers={'none':'','point':'.','pixel':',','circle':'o','triangle_down':'v',
                      'triangle_up':'^','triangle_right':'>','triangle_left':'<',
                      'square':'s','pentagon':'p','star':'*','hex1':'h','hex2':'H',
                      'plus':'+','x':'x','diamond':'D','thin diamond':'d'}
        self.histDrawn=False
        self.tables = options
        
        self.initUI()

    def initUI(self):        
        self.setWindowTitle(self.tr("DataFrame Graph Generator"))
        self.setModal(True)
        #self.resize(366, 274)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setSizePolicy(sizePolicy)
        
        self.gridLayout=QGridLayout()
        
        self.xDataSourceLabel = QLabel(self.tr('Choose a DataFrame for the X-Data'),self)
        self.yDataSourceLabel = QLabel(self.tr('Choose a DataFrame for the Y-Data'),self)
        
        self.xSourceList = QListView(self)
        self.ySourceList = QListView(self)
        
        model = QStandardItemModel()
        for key in self.tables.keys():
            item = QStandardItem(key)
            model.appendRow(item)
            
        self.xSourceList.setModel(model)
        self.ySourceList.setModel(model)
        self.xSourceList.clicked.connect(self.updateXDataCombo)
        self.ySourceList.clicked.connect(self.updateYDataCombo)
        
        self.xDataComboLabel=QLabel(self.tr("X-Axis Data"))
        self.xDataCombo=QComboBox()
        self.yDataComboLabel=QLabel(self.tr("Y-Axis Data"))
        self.yDataCombo=QComboBox()
        
        self.graphTitleLabel=QLabel(self.tr("Graph Title"))
        self.graphTitleLineEdit=QLineEdit()
        self.graphXTitleLabel=QLabel(self.tr("X Title"))
        self.graphXTitleLineEdit=QLineEdit()
        self.graphYTitleLabel=QLabel(self.tr("Y Title"))
        self.graphYTitleLineEdit=QLineEdit()
        
        self.graphInputGroupBox=QGroupBox(self.tr("Graph Input"))
        self.graphInputBox=QGridLayout()
        
        self.dataGroupBox=QGroupBox(self.tr("Data Options"))
        self.dataBox=QGridLayout()
        
        self.dataBox.addWidget(self.xDataComboLabel,0,0)
        self.dataBox.addWidget(self.xDataCombo,0,1)
        self.dataBox.addWidget(self.yDataComboLabel,1,0)
        self.dataBox.addWidget(self.yDataCombo,1,1)
        self.dataGroupBox.setLayout(self.dataBox)
        
        self.titleGroupBox=QGroupBox(self.tr("Title Options"))
        self.titleBox=QGridLayout()
        
        self.titleBox.addWidget(self.graphTitleLabel,0,0)
        self.titleBox.addWidget(self.graphTitleLineEdit,0,1)
        self.titleBox.addWidget(self.graphXTitleLabel,1,0)
        self.titleBox.addWidget(self.graphXTitleLineEdit,1,1)
        self.titleBox.addWidget(self.graphYTitleLabel,2,0)
        self.titleBox.addWidget(self.graphYTitleLineEdit,2,1)
        self.titleGroupBox.setLayout(self.titleBox)
        
        self.tabWidget=QTabWidget()
        self.plotWidget=QWidget()
        self.scatterWidget=QWidget()
        self.histWidget=QWidget()
        
        self.plotGrid=QGridLayout()
        self.scatterGrid=QGridLayout()
        self.histGrid=QGridLayout()
        
        self.lineComboLabel=QLabel(self.tr('Line Style'))
        self.lineStyleCombo=QComboBox()
        self.lineStyleCombo.addItems(list(self.line_options.keys()))
        self.colorComboLabel=QLabel(self.tr('Color'))
        self.colorCombo=QComboBox()
        self.colorCombo.addItems(list(self.colors.keys()))
        self.markerComboLabel=QLabel(self.tr('Markers'))
        self.markerCombo=QComboBox()
        self.markerCombo.addItems(list(self.markers.keys()))
        
        self.plotGrid.addWidget(self.lineComboLabel,0,0)
        self.plotGrid.addWidget(self.lineStyleCombo,0,1)
        self.plotGrid.addWidget(self.colorComboLabel,1,0)
        self.plotGrid.addWidget(self.colorCombo,1,1)
        self.plotGrid.addWidget(self.markerComboLabel,2,0)
        self.plotGrid.addWidget(self.markerCombo,2,1)
        self.plotWidget.setLayout(self.plotGrid)
        self.tabWidget.addTab(self.plotWidget,"Plot")
        
        self.scattercolorComboLabel=QLabel(self.tr('Color'))
        self.scattercolorCombo=QComboBox()
        self.scattercolorCombo.addItems(list(self.colors.keys()))
        self.scattermarkerComboLabel=QLabel(self.tr('Markers'))
        self.scattermarkerCombo=QComboBox()
        self.scattermarkerCombo.addItems(list(self.markers.keys()))
        self.scatterXYlineCheckBox=QCheckBox(self.tr("Add XY Line"))
        
        self.scatterGrid.addWidget(self.scattercolorComboLabel,0,0)
        self.scatterGrid.addWidget(self.scattercolorCombo,0,1)
        self.scatterGrid.addWidget(self.scattermarkerComboLabel,1,0)
        self.scatterGrid.addWidget(self.scattermarkerCombo,1,1)
        self.scatterGrid.addWidget(self.scatterXYlineCheckBox,2,0)
        self.scatterWidget.setLayout(self.scatterGrid)
        self.tabWidget.addTab(self.scatterWidget,"Scatter")
        
        self.histLabel=QLabel(self.tr("Bins"))
        self.histMinRangeTextLabel=QLabel(self.tr('Range (min)'))
        self.histMaxRangeTextLabel=QLabel(self.tr('Range (max)'))
        self.histMinRangeText=QLineEdit()
        self.histMaxRangeText=QLineEdit()
        self.histSlider=QSlider(Qt.Horizontal)
        self.histSlider.setRange(1,100)
        self.histSlider.setValue(10)
        self.histValue=QLineEdit()
        self.histValue.setReadOnly(True)
        self.histValue.setText(str(self.histSlider.value()))
        self.connect(self.histSlider,SIGNAL("valueChanged(int)"),self.setBins)
        
        self.histGrid.addWidget(self.histLabel,0,0)
        self.histGrid.addWidget(self.histSlider,0,1)
        self.histGrid.addWidget(self.histValue,0,2)
        self.histGrid.addWidget(self.histMinRangeTextLabel,1,0)
        self.histGrid.addWidget(self.histMinRangeText,1,1)
        self.histGrid.addWidget(self.histMaxRangeTextLabel,2,0)
        self.histGrid.addWidget(self.histMaxRangeText,2,1)
        self.histWidget.setLayout(self.histGrid)
        self.tabWidget.addTab(self.histWidget,"Histogram")

        self.drawButton=QPushButton('Draw')
        self.clearButton=QPushButton('Clear')
        self.drawButton.clicked.connect(self.drawFigure)
        self.clearButton.clicked.connect(self.clearFigure)
        self.buttonBox = QHBoxLayout()
        self.buttonBox.addWidget(self.drawButton)
        self.buttonBox.addWidget(self.clearButton)        
        
        self.graphInputBox.addWidget(self.dataGroupBox,0,0)
        self.graphInputBox.addWidget(self.titleGroupBox,1,0)
        self.graphInputBox.addWidget(self.tabWidget,2,0)
        self.graphInputBox.addLayout(self.buttonBox,3,0)
        self.graphInputGroupBox.setLayout(self.graphInputBox)
        
        self.vBox=QVBoxLayout()
        self.graphFrame=QWidget()
        
        self.figure=plt.figure()
        self.ax=self.figure.add_subplot(111)
        self.canvas=FigureCanvas(self.figure)
        self.toolbar=NavigationToolbar(self.canvas,self)
        
        self.vBox.addWidget(self.canvas)
        self.vBox.addWidget(self.toolbar)
        self.graphFrame.setLayout(self.vBox)
        
        self.gridLayout.addWidget(self.xDataSourceLabel,0,0,1,1)
        self.gridLayout.addWidget(self.yDataSourceLabel,0,1,1,1)
        self.gridLayout.addWidget(self.graphInputGroupBox,1,2,1,1)
        self.gridLayout.addWidget(self.xSourceList,1,0,1,1)
        self.gridLayout.addWidget(self.ySourceList,1,1,1,1)
        self.gridLayout.addWidget(self.graphFrame,2,0,3,3)
        
        self.setLayout(self.gridLayout)                
    
    def doNothing(self):
        pass
    
    def updateXDataCombo(self):
        selection = self.xSourceList.selectedIndexes()
        for index in selection:
            self.xSource = index.data(Qt.DisplayRole)
        self.xDataCombo.clear()
        self.xDataCombo.addItems(self.tables[self.xSource].columns)
    
    def updateYDataCombo(self):
        selection = self.ySourceList.selectedIndexes()
        for index in selection:
            self.ySource = index.data(Qt.DisplayRole)
        self.yDataCombo.clear()
        self.yDataCombo.addItems(self.tables[self.ySource].columns)
        
    def drawFigure(self):
        plot = self.tabWidget.tabText(self.tabWidget.currentIndex())
        if plot == 'Plot':
            self.drawPlot()
        if plot == 'Scatter':
            self.drawScatter()
        if plot == 'Histogram':
            self.drawHist()
    
    def drawPlot(self):
        xdata=self.xDataCombo.currentText()
        ydata=self.yDataCombo.currentText()
        line=self.lineStyleCombo.currentText()
        color=self.colorCombo.currentText()
        markers=self.markerCombo.currentText()
        
        if self.graphTitleLineEdit.text() != '':
            self.ax.set_title(self.graphTitleLineEdit.text())
        if self.graphXTitleLineEdit.text() != '':
            self.ax.set_xlabel(self.graphXTitleLineEdit.text())
        if self.graphYTitleLineEdit.text() != '':
            self.ax.set_ylabel(self.graphYTitleLineEdit.text())
            
        if markers == 'none':
            self.ax.plot(pd.to_numeric(self.tables[self.xSource][xdata]),
                         pd.to_numeric(self.tables[self.ySource][ydata]),
                            color=color,linestyle=line)
        elif line == 'none':
            self.ax.plot(pd.to_numeric(self.tables[self.xSource][xdata]),
                         pd.to_numeric(self.tables[self.ySource][ydata]),
                            color=color,marker=self.markers[markers])
        else:
            self.ax.plot(pd.to_numeric(self.tables[self.xSource][xdata]),
                         pd.to_numeric(self.tables[self.ySource][ydata]),
                            color=color,linestyle=line,marker=self.markers[markers])
            
        self.update_figure()
        
    def drawScatter(self):
        xdata=self.xDataCombo.currentText()
        ydata=self.yDataCombo.currentText()
        color=self.scattercolorCombo.currentText()
        markers=self.scattermarkerCombo.currentText()
        
        if self.graphTitleLineEdit.text() != '':
            self.ax.set_title(self.graphTitleLineEdit.text())
        if self.graphXTitleLineEdit.text() != '':
            self.ax.set_xlabel(self.graphXTitleLineEdit.text())
        if self.graphYTitleLineEdit.text() != '':
            self.ax.set_ylabel(self.graphYTitleLineEdit.text())
            
        self.ax.scatter(pd.to_numeric(self.tables[self.xSource][xdata]),
                        pd.to_numeric(self.tables[self.ySource][ydata]),
                                      color=color,marker=self.markers[markers])
        
        if self.scatterXYlineCheckBox.isChecked():
            max_x=0
            max_y=0
            if np.max(pd.to_numeric(self.tables[self.xSource][xdata])) > max_x:
                max_x=np.max(pd.to_numeric(self.tables[self.xSource][xdata]))
            if np.max(pd.to_numeric(self.tables[self.ySource][ydata])) > max_y:
                max_y=np.max(pd.to_numeric(self.tables[self.ySource][ydata]))
            max_val=np.max([max_x,max_y])
            self.ax.plot([0,max_val],[0,max_val],linewidth=2,linestyle='--',c='k',alpha=.4)
            
        self.update_figure()
    
    def setBins(self,value):
        if self.histDrawn:
            self.histValue.setText(str(self.histSlider.value()))
            self.clearFigure()
            self.drawHist()
        else:
            self.histValue.setText(str(self.histSlider.value()))
    
    def drawHist(self):
        self.histDrawn=True
        xdata=self.xDataCombo.currentText()
        
        if self.graphTitleLineEdit.text() != '':
            self.ax.set_title(self.graphTitleLineEdit.text())
        if self.graphXTitleLineEdit.text() != '':
            self.ax.set_xlabel(self.graphXTitleLineEdit.text())
        if self.graphYTitleLineEdit.text() != '':
            self.ax.set_ylabel(self.graphYTitleLineEdit.text())
        
        if self.histMinRangeText.text() != '':
            rMin=float(histMinRangeText.text())
        else:
            rMin=np.min(self.tables[self.xSource][xdata])
        if self.histMaxRangeText.text() != '':
            rMax=float(histMaxRangeText.text())
        else:
            rMax=np.max(self.tables[self.xSource][xdata])
        
        #if self.histDensityCheckBox.isChecked():
        #    self.ax.histogram(self.df[xdata].convert_objects(convert_numeric=True),bins=int(self.histSlider.value()),
        #                      range=(rMin,rMax),density=True)
        #else:
        #self.ax.hist(self.tables[self.xSource][xdata].convert_objects(convert_numeric=True),
        #             bins=int(self.histSlider.value()),range=(rMin,rMax))
        self.ax.hist(pd.to_numeric(self.tables[self.xSource][xdata]),
                     bins=int(self.histSlider.value()),range=(rMin,rMax))
            
        self.update_figure()
    
    def clearFigure(self):
        self.histDrawn=False
        self.figure.clf()
        self.ax=self.figure.add_subplot(111)
        self.update_figure()
        
    def update_figure(self):
        self.canvas.draw()
        
if __name__ == "__main__":
    app=QApplication(sys.argv)
    form=GraphFormatDialog(options={})
    form.show()
    app.exec_()