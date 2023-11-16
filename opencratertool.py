# -*- coding: utf-8 -*-
"""
/***************************************************************************
 opencratertool
                                 A QGIS plugin
 A tool for crater size-frequency measurements
                              -------------------
        begin                : 2023-04-19
        copyright            : (C) 2023 by Thomas Heyer
        email                : thomas.heyer@uni-muenster.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from PyQt5.QtWidgets import QApplication, QWidget, QGraphicsScene
from PyQt5 import QtCore

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon, QColor
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QMenu

# --
from qgis.gui import QgsMapTool, QgsRubberBand,QgsModelGraphicsScene, QgsModelGraphicsView,QgsHighlight
from qgis.PyQt.QtCore import Qt, pyqtSignal, QVariant

from math import sqrt, pi, cos, sin
from qgis.core import QgsFeature, QgsGeometry, QgsWkbTypes, QgsVectorLayer, QgsField, QgsFields, QgsVectorFileWriter, QgsCoordinateReferenceSystem, QgsCoordinateTransform,QgsProject, Qgis, QgsWkbTypes, QgsPointXY,QgsSymbol,QgsRendererCategory,QgsCategorizedSymbolRenderer,QgsSimpleLineSymbolLayer,QgsSingleSymbolRenderer, QgsFeatureRequest,QgsRectangle
import datetime,time
import numpy as np
from pyproj import CRS

from . import pyqtgraph as pg
#from .pyqtgraph import exporters

# experimental
from qgis.PyQt.QtWidgets import QShortcut
from qgis.PyQt.QtGui import QKeySequence

# Initialize Qt resources from file resources.py
from .resources import *
# Import code for dialogs
from .opencratertool_dialog import con0,con1,con2,con3,con4,con5,con6,con7,con8
import os.path

def g_mean(x):
    a = np.log(x)
    return np.exp(a.mean())



class opencratertool:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):

        # Save reference to the QGIS interface
        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        # Initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # Initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'opencratertool_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&opencratertool')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None
        


    # noinspection PyMethodMayBeStatic
    def tr(self, message):
       # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('opencratertool', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip='OCT',
        whats_this=None,
        checkable=False,
        menu=None,
        parent=None):
 

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        action.setCheckable(checkable)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if menu is not None:
            action.setMenu(menu)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action
    
    # Create menu entries and toolbar icons inside the QGIS GUI
    def initGui(self):

        # Set version of the tool
        self.version='Version: 0.2 (2023-11-16)'

        # Create icon for two point tool
        icon_path = ':/plugins/opencratertool/ui/iconA.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Two Point Circle'),
            checkable=True,
            callback=self.main2,
            parent=self.iface.mainWindow())
        
        # Create icon for three point tool
        icon_path = ':/plugins/opencratertool/ui/iconB.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Three Point Circle'),
            checkable=True,
            callback=self.main3,
            parent=self.iface.mainWindow())
 
        # Create icon for mark crater tool
        icon_path = ':/plugins/opencratertool/ui/iconC.png'
        self.add_action(
            icon_path,
            text=self.tr('Mark/Unmark latest Crater or Selected Craters'),
            callback=self.main4,
            parent=self.iface.mainWindow())
            
        # Create icon for shapefile tool
        pointMenu = QMenu()
        pointMenu.addAction(
            QIcon(':/plugins/opencratertool/ui/icon1.png'),
            self.tr('Create Shapefiles'), self.opt1)
        # Create icon for crater export tool
        pointMenu.addAction(
            QIcon(':/plugins/opencratertool/ui/icon2.png'),
            self.tr('Export Craters'), self.opt2)
        pointMenu.addSeparator()    
        # Create icon for preview plot tool
        pointMenu.addAction(
            QIcon(':/plugins/opencratertool/ui/icon3.png'),
            self.tr('Preview Plot'), self.opt3)
        # Create icon for grid tool
        pointMenu.addAction(
            QIcon(':/plugins/opencratertool/ui/icon4.png'),
            self.tr('Create Grid'), self.opt4)
        # Create icon for map scale tool
        pointMenu.addAction(
            QIcon(':/plugins/opencratertool/ui/icon5.png'),
            self.tr('Set Map Scale'), self.opt5)
        pointMenu.addSeparator()
        # Create icon for crater import tool
        pointMenu.addAction(
            QIcon(':/plugins/opencratertool/ui/icon6.png'),
            self.tr('Import Craters'), self.opt6)
        # Create icon for area import tool
        pointMenu.addAction(
            QIcon(':/plugins/opencratertool/ui/icon7.png'),
            self.tr('Import Areas'), self.opt7)
        pointMenu.addSeparator()
        # Create icon for crater compare tool
        pointMenu.addAction(
            QIcon(':/plugins/opencratertool/ui/icon8.png'),
            self.tr('Compare Counts'), self.opt8)   
        
        # Create icon for tool description
        icon_path = ':/plugins/opencratertool/ui/icon0.png'
        self.add_action(
            icon_path,
            text=self.tr('OpenCraterTool'),
            menu=pointMenu,
            callback=self.main1,
            parent=self.iface.mainWindow())

        # Define number of segments of the shapefile circles
        self.iface.shapefilesegments=150
        
        # Define number segments of the rubberband circle
        self.iface.rubberbandsegments=100

        #
        self.first_start = True
        self.iface.drawmode=0
        self.draw2PointCrater = self.Draw2PointCrater(self.iface)
        self.draw3PointCrater = self.Draw3PointCrater(self.iface)

        # Load user interfaces 
        self.con0 = con0() # tool description
        self.con1 = con1() # shapefile tool
        self.con2 = con2() # crater export tool
        self.con3 = con3() # preview plot tool
        self.con4 = con4() # grid tool
        self.con5 = con5() # map scale tool
        self.con6 = con6() # crater import tool
        self.con7 = con7() # area import tool
        self.con8 = con8() # crater compare tool
        
        # Connect actions for tool description
        self.con0.info_version.setText(self.version)
        
        # Connect actions for shapefile tool
        self.con1.push_run.clicked.connect(self.opt1_run)
        
        # Connect actions for crater export tool
        self.con2.combo_fractions.currentIndexChanged.connect(self.change_con2_fractions)
        self.con2.combo_marked.currentIndexChanged.connect(self.change_con2_marked)
        self.con2.combo_export.currentIndexChanged.connect(self.change_con2_export) 
        self.con2.push_all.clicked.connect(self.click_expo_selectall)
        self.con2.push_none.clicked.connect(self.click_expo_selectnone)
        self.con2.combo_area.currentIndexChanged.connect(self.change_expo_area_list)
        self.con2.combo_crat.currentIndexChanged.connect(self.change_expo_crat_index)
        self.con2.push_run.clicked.connect(self.opt2_run)
        
        # Connect actions for preview plot tool
        self.con3.combo_fractions.currentIndexChanged.connect(self.change_con3_fractions)
        self.con3.combo_marked.currentIndexChanged.connect(self.change_con3_marked)
        self.con3.push_all.clicked.connect(self.click_plot_selectall)
        self.con3.push_none.clicked.connect(self.click_plot_selectnone)
        self.con3.combo_area.currentIndexChanged.connect(self.change_plot_area_list)
        self.con3.combo_crat.currentIndexChanged.connect(self.change_plot_crat_index)
        self.con3.push_plot.clicked.connect(self.plotstats)
        
        # Connect actions for grid tool
        self.con4.push_all.clicked.connect(self.click_grid_selectall)
        self.con4.push_none.clicked.connect(self.click_grid_selectnone)
        self.con4.combo_area.currentIndexChanged.connect(self.change_grid_area_list)
        self.con4.push_preview.clicked.connect(self.previewnet)
        self.con4.push_export.clicked.connect(self.exportnet)
        
        # Connect actions for map scale tool
        self.con5.push_run.clicked.connect(self.opt5_run)

        # Connect actions for import crater tool
        self.con6.push_run.clicked.connect(self.opt6_run)
        self.con6.combo_crat.currentIndexChanged.connect(self.change_con6_crat_index)
        
        # Connect actions for import area tool
        self.con7.push_run.clicked.connect(self.opt7_run)
        self.con7.combo_area.currentIndexChanged.connect(self.change_con7_area_index)
        
        # Connect actions for crater compare tool
        self.con8.combo_crat1.currentIndexChanged.connect(self.change_con8_crat_index)
        self.con8.combo_crat2.currentIndexChanged.connect(self.change_con8_refe_index)
        self.con8.push_plot.clicked.connect(self.opt8_run)
        self.con8.combo_mode.currentIndexChanged.connect(self.change_con8_mode_index)
        self.con8.push_expo.clicked.connect(self.exportcompare)
        self.con8.progressBar.hide()

        QApplication.setAttribute(QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
        
        #  Add shortcut to set the map scale
        shortcut = QShortcut(QKeySequence(Qt.ShiftModifier + Qt.Key_S), self.iface.mainWindow())
        shortcut.setContext(Qt.ApplicationShortcut)
        shortcut.activated.connect(self.setscale)


        # set options
        self.exportfractions=True
        self.excludemarked=False
        self.comparemodeindex=0
        self.exportformatindex=0
        self.scene=QGraphicsScene()

        # Create pseudo-log bins described in Neukum (1983) and Hartmann and Neukum (2001) 
        self.bins=np.array([])
        for n in range(7):
            self.bins=np.concatenate((self.bins, np.array([1.,1.1,1.2,1.3,1.4,1.5,1.7,2.,2.5,3.0,3.5,4.,4.5,5.,6.,7.,8.,9.])*(10**(n-2))))
        
        # Compare tool 
        self.diams=[]
        self.error=[]
        self.errorR=[]
        
        # Grid style
        self.nb = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
        self.nb.setColor(QColor(0, 197, 255))
        self.nb.setFillColor(QColor(0,0,0,0))
        self.nb.setWidth(1)
        
        # Create dateline object for north pole projection
        self.iface.datelineN = QgsGeometry.fromPolygonXY([[
                    QgsPointXY( -0.0001, -1),
                    QgsPointXY( -0.0001, -0.001),
                    QgsPointXY( -0.0001, -0.00001),
                    QgsPointXY(  0.0001, -0.00001),
                    QgsPointXY(  0.0001, -0.001),
                    QgsPointXY(  0.0001, -1),
                    QgsPointXY(  0.0001, -100000000), 
                    QgsPointXY( -0.0001, -100000000)]])
        
        # Create dateline object for south pole projection
        self.iface.datelineS = QgsGeometry.fromPolygonXY([[
                    QgsPointXY( 0.0001, 1),
                    QgsPointXY( 0.0001, 0.001),
                    QgsPointXY( 0.0001, 0.00001),
                    QgsPointXY(  -0.0001, 0.00001),
                    QgsPointXY(  -0.0001, 0.001),
                    QgsPointXY(  -0.0001, 1),
                    QgsPointXY(  -0.0001, 100000000), 
                    QgsPointXY( 0.0001, 100000000)]])
        
    # Removes the plugin menu item and icon from QGIS GUI
    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&opencratertool'),
                action)
            self.iface.removeToolBarIcon(action)

    # Function to plot the crater-size-frequency
    class craterPlotWidget(pg.PlotWidget):
        def __init__(self,os, **kwargs):
            super().__init__(**kwargs)
            self.os=os # original self

            for k in range(len(self.os.cum)):
                maxerror=(self.os.cum[k]+self.os.cum[k]**(1/2))/self.os.expo_area_all
                minerror=(self.os.cum[k]-self.os.cum[k]**(1/2))/self.os.expo_area_all
                if minerror==0:
                    minerror=0.2/self.os.expo_area_all
            
                x=np.array([self.os.middle[k],self.os.middle[k]])
                y=np.array([maxerror,minerror])
                errorbar = pg.PlotDataItem(x,y, pen=pg.mkPen((30,30,30), width=2)) #,antialias=True
                self.addItem(errorbar)
        
        
            self.cum_corrected=self.os.cum / self.os.expo_area_all
            
            self.s1 = pg.PlotDataItem(self.os.middle,self.cum_corrected, pen=None, symbol='o', symbolSize = 10, symbolBrush =(30,30,30),antialias=True)

            self.addItem(self.s1)
            self.s1.sigPointsClicked.connect(self.clickitem)

            self.setBackground((255,255,255))
            
            self.showGrid(x=True,y=True)
            self.setLabel('left', 'N[cum]/km²')
            self.setLabel('bottom', 'Crater Diameter [km]')
            self.setLogMode(True, True)
            self.resize(440, 330)
        def clickitem(self,e,p):
            try:
                self.removeItem(self.selectionplot)
            except:
                pass
     
            # Index of clicked item
            k=p[0].index()
            
            selection=[]
            for f in self.os.crater_data:
                diam=f.attribute('Diam_km')
                if diam > self.os.lower[k] and diam < self.os.upper[k]:
                    selection.append(f.id())
            self.os.iface.mainWindow().findChild(QAction, 'mActionDeselectAll').trigger()
            layer_crat = QgsProject.instance().mapLayersByName(self.os.crat_layer_list[self.os.crat_layer_index])[0]
            layer_crat.selectByIds(selection)

            temp_diam=self.os.middle[k]
            temp_cum=self.cum_corrected[k]
            self.selectionplot = pg.PlotDataItem([temp_diam],[temp_cum], pen=None, symbol='o', symbolSize = 11, symbolBrush =(51,153,255))
            self.addItem(self.selectionplot)
            
            # Add ui infos
            self.os.con3.info5.setText('Bin: '+'{:.3f} km'.format(self.os.lower[k])+' - {:.3f} km'.format(self.os.upper[k]))
            self.os.con3.info6.setText('Number of Craters: '+str(len(selection)))
            
    # Function to plot the crater comparison statistics
    class comparePlotWidget(pg.PlotWidget):
        def __init__(self,os, **kwargs):
            super().__init__(**kwargs)
            self.os=os # original self

            if self.os.comparemodeindex==0:
                #absolute values meter
                self.s1 = pg.PlotDataItem(self.os.middle,self.os.binnedmean, pen=None, symbol='s', symbolSize = 10, symbolBrush =(40,40,40))
                self.setLabel('left', 'Diameter - Reference Diameter [m]')
                self.s2 = pg.PlotDataItem(self.os.diams,self.os.error, pen=None, symbol='o', symbolSize = 7, symbolBrush =(200,200,200))
                self.addItem(self.s2) 
   
            elif self.os.comparemodeindex==1:
                #relative values %
                self.s1 = pg.PlotDataItem(self.os.middle,self.os.binnedP, pen=None, symbol='s', symbolSize = 10, symbolBrush =(40,40,40))
                self.setLabel('left', '(Diameter / Reference Diameter) - 1 [%]')
                self.s2 = pg.PlotDataItem(self.os.diams,self.os.errorP, pen=None, symbol='o', symbolSize = 7, symbolBrush =(200,200,200))
                self.addItem(self.s2) 
            else:
                #relative values ratio
                self.s1 = pg.PlotDataItem(self.os.middle,self.os.binnedR, pen=None, symbol='s', symbolSize = 10, symbolBrush =(40,40,40))
                self.setLabel('left', 'Diameter / Reference Diameter')
                self.s2 = pg.PlotDataItem(self.os.diams,self.os.errorR, pen=None, symbol='o', symbolSize = 7, symbolBrush =(200,200,200))
                self.addItem(self.s2) 

            self.s2.sigPointsClicked.connect(self.clickpair)
            self.s1.sigPointsClicked.connect(self.clickitem)
            self.addItem(self.s1)

            self.setBackground((255,255,255))
            self.showGrid(x=True,y=True)
            
            self.setLabel('bottom', 'Reference Crater Diameter [km]')
            self.setLogMode(True, False)
            
            self.last=''
            self.first=False
            self.resize(440, 330)
            
        # Function for
        def mouse_clicked(self, mouseClickEvent):
            pass
        
        # Function for
        def clickpair(self,e,p):
            try:
                self.removeItem(self.selectionplot)
            except:
                pass
            k=p[0].index()

            selection=[self.os.rid[k]]
            layer_crat = QgsProject.instance().mapLayersByName(self.os.crat_layer_list[self.os.refe_layer_index])[0]
            self.os.iface.mainWindow().findChild(QAction, 'mActionDeselectAll').trigger()
            layer_crat.selectByIds(selection)
            if self.os.comparemodeindex==0:
                self.selectionplot = pg.PlotDataItem([self.os.diams[k]],[self.os.error[k]], pen=None, symbol='o', symbolSize = 8, symbolBrush =(51,153,255))
                self.os.con8.info5.setText('Difference: {:.2f} m'.format(self.os.error[k]))
            elif self.os.comparemodeindex==1:
                self.selectionplot = pg.PlotDataItem([self.os.diams[k]],[self.os.errorP[k]], pen=None, symbol='o', symbolSize = 8, symbolBrush =(51,153,255))
                self.os.con8.info5.setText('Difference: {:.2f} %'.format(self.os.errorP[k]))
            else:
                self.selectionplot = pg.PlotDataItem([self.os.diams[k]],[self.os.errorR[k]], pen=None, symbol='o', symbolSize = 8, symbolBrush =(51,153,255))
                self.os.con8.info5.setText('Ratio: {:.2f}'.format(self.os.errorR[k]))
            self.addItem(self.selectionplot)

            box = layer_crat.boundingBoxOfSelected()
            self.os.iface.mapCanvas().setExtent(box)
            self.os.iface.mapCanvas().refresh()

        # Function for
        def clickitem(self,e,p):
            try:
                self.removeItem(self.selectionplot)
            except:
                pass
     
            k=p[0].index()
            selection=[]
            layer_crat = QgsProject.instance().mapLayersByName(self.os.crat_layer_list[self.os.refe_layer_index])[0]

            for f in layer_crat.getFeatures():
                
                diam=f.attribute('Diam_km')
                if diam > self.os.lower[k] and diam < self.os.upper[k]:
                    selection.append(f.id())
            self.os.iface.mainWindow().findChild(QAction, 'mActionDeselectAll').trigger()
            layer_crat.selectByIds(selection)

            temp_diam=self.os.middle[k]
            if self.os.comparemodeindex==0:
                temp_cum=self.os.binnedmean[k]
                self.os.con8.info5.setText('Number of Craters: '+'{:.0f}'.format(self.os.binnedcount[k])+'   Mean Difference: {:.2f} m'.format(self.os.binnedmean[k]))
            elif self.os.comparemodeindex==1:
                temp_cum=self.os.binnedP[k]
                self.os.con8.info5.setText('Number of Craters: '+'{:.0f}'.format(self.os.binnedcount[k])+'   Mean Difference: {:.2f} %'.format(self.os.binnedP[k]))
            else:
                temp_cum=self.os.binnedR[k]
                self.os.con8.info5.setText('Number of Craters: '+'{:.0f}'.format(self.os.binnedcount[k])+'   Mean Ratio: {:.4f}'.format(self.os.binnedR[k]))
            
            self.selectionplot = pg.PlotDataItem([temp_diam],[temp_cum], pen=None, symbol='s', symbolSize = 11, symbolBrush =(51,153,255))
            self.addItem(self.selectionplot)
            

    # Function for drawing craters using two user-defined points ----------------------------------------------
    class Draw2PointCrater(QgsMapTool):   
  
        selectionDone = pyqtSignal()
        move = pyqtSignal()
        def __init__(self, iface):
            QgsMapTool.__init__(self, iface.mapCanvas())
            self.canvas = iface.mapCanvas() 
            self.iface = iface
            self.rb = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
            self.rb.setColor(QColor(0, 197, 255))
            
            self.rb.setFillColor(QColor(0,0,0,0))
            self.rb.setWidth(1)
            self.firstClick=False
            self.craterDone=False


        def twoPointCircle(self,segments):
            try:
                # Transform projection from source to latlon
                crs_source =QgsCoordinateReferenceSystem.fromProj4(self.iface.activeLayer().crs().toProj4())

                geod = str(CRS.from_proj4(self.iface.activeLayer().crs().toProj4()).get_geod()).split("'")[1]
                crs_lonlat = QgsCoordinateReferenceSystem.fromProj4('+proj=lonlat '+geod+' +no_defs +type=crs')
                SourceToLonlat = QgsCoordinateTransform(crs_source, crs_lonlat, QgsProject.instance().transformContext())

                # Calculate center of two points
                p1= SourceToLonlat.transform(self.point1)
                p2= SourceToLonlat.transform(self.point2)
                
                crs_AeqdCenter = QgsCoordinateReferenceSystem.fromProj4('+proj=aeqd +lat_0='+str(p1.y())+' +lon_0='+str(p1.x())+' +x_0=0 +y_0=0 '+geod+' +units=m +no_defs +type=crs')
                LonlatTocrs_AeqdS = QgsCoordinateTransform(crs_lonlat, crs_AeqdCenter, QgsProject.instance().transformContext())
                AeqdSToLonlat = QgsCoordinateTransform(crs_AeqdCenter, crs_lonlat, QgsProject.instance().transformContext())
                
                np1=LonlatTocrs_AeqdS.transform(p1)
                np2=LonlatTocrs_AeqdS.transform(p2)
                line = QgsGeometry.fromPolylineXY([np1, np2])
                center=line.centroid().asPoint()
                center_lonlat = AeqdSToLonlat.transform(center)
                self.center_lon = center_lonlat.x()
                self.center_lat = center_lonlat.y()

                crs_Aeqd = QgsCoordinateReferenceSystem.fromProj4('+proj=aeqd +lat_0='+str(self.center_lat)+' +lon_0='+str(self.center_lon)+' +x_0=0 +y_0=0 '+geod+' +units=m +no_defs +type=crs')
                SourceToAeqd = QgsCoordinateTransform(crs_source, crs_Aeqd, QgsProject.instance().transformContext())

                # Project points 
                point1 = QgsPointXY( 0,0)
                point2 = SourceToAeqd.transform(self.point2)

                # Calculate circle in projection
                diam = sqrt(point1.sqrDist(point2))
           
                points=[]

                for itheta in range(segments):
                    theta = itheta * (2.0 * pi / segments)
                    points.append((diam * cos(theta),diam * sin(theta)))
                polygon = QgsGeometry.fromMultiPolygonXY( [[[ QgsPointXY( p[0], p[1] ) for p in points ]]] )  

                diamx1=polygon.boundingBox().yMaximum()
                diamx2=polygon.boundingBox().yMinimum()
                self.diam=(diamx1-diamx2)/1000

                # Cut circles that intersect the dateline and the poles
                if center_lonlat.y()>0:
                    #North
                    crs_AqedNorth = QgsCoordinateReferenceSystem.fromProj4('+proj=aeqd +lat_0=90 +lon_0=180 +x_0=0 +y_0=0 '+geod+' +units=m +no_defs +type=crs')
                    AeqdToAqedNorth = QgsCoordinateTransform(crs_Aeqd, crs_AqedNorth, QgsProject.instance().transformContext())
                    AqedNorthToSource = QgsCoordinateTransform(crs_AqedNorth, crs_source, QgsProject.instance().transformContext())

                    polygon.transform(AeqdToAqedNorth)
                    polygonB=polygon.difference(self.iface.datelineN)

                    polygonB.transform(AqedNorthToSource)
                    self.rb.reset(QgsWkbTypes.PolygonGeometry)
                    self.rb.addGeometry(polygonB)
                    
                else:
                    #South
                    crs_AqedSouth = QgsCoordinateReferenceSystem.fromProj4('+proj=aeqd +lat_0=-90 +lon_0=180 +x_0=0 +y_0=0 '+geod+' +units=m +no_defs +type=crs')
                    AeqdToAqedSouth = QgsCoordinateTransform(crs_Aeqd, crs_AqedSouth, QgsProject.instance().transformContext())
                    AqedSouthToSource = QgsCoordinateTransform(crs_AqedSouth, crs_source, QgsProject.instance().transformContext())
                    
                    polygon.transform(AeqdToAqedSouth)
                    polygonB=polygon.difference(self.iface.datelineS)
                
                    polygonB.transform(AqedSouthToSource)
                    self.rb.reset(QgsWkbTypes.PolygonGeometry)
                    self.rb.addGeometry(polygonB)
            except:
                pass

        def canvasPressEvent(self, e):
            pass


        def canvasMoveEvent(self, e):
            # Build rubber band
            if self.firstClick==True:
                self.point2 = self.toMapCoordinates(e.pos())
                self.twoPointCircle(self.iface.rubberbandsegments)
                self.rb.show()
                self.move.emit()

        def canvasReleaseEvent(self, e):
            if(self.iface.activeLayer().name().upper().startswith('CRATER') or self.iface.activeLayer().name().upper().endswith('CRATER')):
                if e.button() == Qt.LeftButton:
                    if self.firstClick==False:
                        self.firstClick=True
                        self.craterDone=False
                        self.point1 = self.toMapCoordinates(e.pos())
                        self.iface.mainWindow().findChild(QAction, 'mActionDeselectAll').trigger()

                    else:
                        self.firstClick=False
                        self.point2 = self.toMapCoordinates(e.pos())
                        self.twoPointCircle(self.iface.shapefilesegments)

                        polygon=self.rb.asGeometry()

                        # Write circle to shapefile
                        layer = self.iface.activeLayer()                 
                        poly = QgsFeature(layer.fields())
                        poly.setGeometry(polygon)
                        try:
                            poly.setAttribute("Diam_km",self.diam)
                            poly.setAttribute("x_coord",self.center_lon)
                            poly.setAttribute("y_coord",self.center_lat)
                            poly.setAttribute("tag","standard")
                            layer.startEditing()
                            layer.addFeature(poly)
                            layer.commitChanges()
                            layer.startEditing()
                            
                            self.craterDone=True
                            self.rb.reset(QgsWkbTypes.PolygonGeometry)

                        except:
                            self.iface.messageBar().pushMessage("Wrong Shapefile", duration=3)         
                else:
                    self.rb.reset(QgsWkbTypes.PolygonGeometry)
                    self.firstClick=False
                    if self.craterDone:
                        layer = self.iface.activeLayer()
                        layer.startEditing()
                        layer.deleteFeature(layer.featureCount()-1)
                        layer.commitChanges()
                        layer.startEditing()
                        
                        self.craterDone=False
                    
            else:
                self.iface.messageBar().pushMessage("Select the 'CRATER' shapefile.", duration=3)


   # Function for drawing craters using three user-defined points ----------------------------------------------
    class Draw3PointCrater(QgsMapTool):   
  
        selectionDone = pyqtSignal()
        move = pyqtSignal()
        def __init__(self, iface):
            QgsMapTool.__init__(self, iface.mapCanvas())
            self.canvas = iface.mapCanvas() 
            self.iface = iface
            self.rb = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
            self.rb.setColor(QColor(0, 197, 255))
            self.rb.setFillColor(QColor(0,0,0,0))
            self.rb.setWidth(1)
            self.firstClick=False
            self.secondClick=False
            self.craterDone=False

        def threePointCircle(self,segments):
            try:
                # Transform projection from source to latlon
                crs_source =QgsCoordinateReferenceSystem.fromProj4(self.iface.activeLayer().crs().toProj4())
                
                geod = str(CRS.from_proj4(self.iface.activeLayer().crs().toProj4()).get_geod()).split("'")[1]
                crs_lonlat = QgsCoordinateReferenceSystem.fromProj4('+proj=lonlat '+geod+' +no_defs +type=crs')
                SourceToLonlat = QgsCoordinateTransform(crs_source, crs_lonlat, QgsProject.instance().transformContext())

                # Calculate center of two points
                point1= SourceToLonlat.transform(self.point1)
                point2= SourceToLonlat.transform(self.point2)
                point3= SourceToLonlat.transform(self.point3)
                
                x1=point1.x()
                y1=point1.y() 
                x2=point2.x()
                y2=point2.y() 
                x3=point3.x()
                y3=point3.y()

                c = (x1-x2)**2 + (y1-y2)**2
                a = (x2-x3)**2 + (y2-y3)**2
                b = (x3-x1)**2 + (y3-y1)**2
                s = 2*(a*b + b*c + c*a) - (a*a + b*b + c*c) 
                px = (a*(b+c-a)*x1 + b*(c+a-b)*x2 + c*(a+b-c)*x3) / s   # center x
                py = (a*(b+c-a)*y1 + b*(c+a-b)*y2 + c*(a+b-c)*y3) / s   # center y
                ar = a**0.5
                br = b**0.5
                cr = c**0.5 
                r = ar*br*cr / ((ar+br+cr)*(-ar+br+cr)*(ar-br+cr)*(ar+br-cr))**0.5
                self.center_lon=px
                self.center_lat=py
  
                crs_Aeqd = QgsCoordinateReferenceSystem.fromProj4('+proj=aeqd +lat_0='+str(self.center_lat)+' +lon_0='+str(self.center_lon)+' +x_0=0 +y_0=0 '+geod+' +units=m +no_defs +type=crs')
                SourceToAeqd = QgsCoordinateTransform(crs_source, crs_Aeqd, QgsProject.instance().transformContext())
                AeqdToSource = QgsCoordinateTransform(crs_Aeqd, crs_source, QgsProject.instance().transformContext())

                point1 = SourceToAeqd.transform(self.point1)
                point2 = SourceToAeqd.transform(self.point2)
                point3 = SourceToAeqd.transform(self.point3)

                x1=point1.x()
                y1=point1.y() 
                x2=point2.x()
                y2=point2.y() 
                x3=point3.x()
                y3=point3.y()

                c = (x1-x2)**2 + (y1-y2)**2
                a = (x2-x3)**2 + (y2-y3)**2
                b = (x3-x1)**2 + (y3-y1)**2
                s = 2*(a*b + b*c + c*a) - (a*a + b*b + c*c) 
                px = (a*(b+c-a)*x1 + b*(c+a-b)*x2 + c*(a+b-c)*x3) / s   # center x
                py = (a*(b+c-a)*y1 + b*(c+a-b)*y2 + c*(a+b-c)*y3) / s   # center y
                ar = a**0.5
                br = b**0.5
                cr = c**0.5 
                r = ar*br*cr / ((ar+br+cr)*(-ar+br+cr)*(ar-br+cr)*(ar+br-cr))**0.5    

                #segments=100
                points=[]
                for itheta in range(segments):
                    theta = itheta * (2.0 * pi / segments)
                    points.append((px + r * cos(theta),py + r * sin(theta)))
                polygon = QgsGeometry.fromMultiPolygonXY( [[[ QgsPointXY( p[0], p[1] ) for p in points ]]] ) 

                diamx1=polygon.boundingBox().yMaximum()
                diamx2=polygon.boundingBox().yMinimum()
                self.diam=(diamx1-diamx2)/1000

                if self.center_lon>0:
                    #North
                    crs_AqedNorth = QgsCoordinateReferenceSystem.fromProj4('+proj=aeqd +lat_0=90 +lon_0=180 +x_0=0 +y_0=0 '+geod+' +units=m +no_defs +type=crs')
                    AeqdToAqedNorth = QgsCoordinateTransform(crs_Aeqd, crs_AqedNorth, QgsProject.instance().transformContext())
                    AqedNorthToSource = QgsCoordinateTransform(crs_AqedNorth, crs_source, QgsProject.instance().transformContext())

                    polygon.transform(AeqdToAqedNorth)
                    polygonB=polygon.difference(self.iface.datelineN)

                    polygonB.transform(AqedNorthToSource)
                    self.rb.reset(QgsWkbTypes.PolygonGeometry)
                    self.rb.addGeometry(polygonB)
                    
                else:
                    #South
                    crs_AqedSouth = QgsCoordinateReferenceSystem.fromProj4('+proj=aeqd +lat_0=-90 +lon_0=180 +x_0=0 +y_0=0 '+geod+' +units=m +no_defs +type=crs')
                    AeqdToAqedSouth = QgsCoordinateTransform(crs_Aeqd, crs_AqedSouth, QgsProject.instance().transformContext())
                    AqedSouthToSource = QgsCoordinateTransform(crs_AqedSouth, crs_source, QgsProject.instance().transformContext())
                    
                    polygon.transform(AeqdToAqedSouth)
                    polygonB=polygon.difference(self.iface.datelineS)

                    polygonB.transform(AqedSouthToSource)
                    self.rb.reset(QgsWkbTypes.PolygonGeometry)
                    self.rb.addGeometry(polygonB)
            except:
                pass

        def canvasPressEvent(self, e):
            pass

        def canvasMoveEvent(self, e):
            if self.secondClick==True:
                self.point3 = self.toMapCoordinates(e.pos())
                self.threePointCircle(self.iface.rubberbandsegments)

            else:
                if self.firstClick==True:
                    polygon = QgsGeometry.fromPolylineXY([self.point1, self.toMapCoordinates(e.pos())])
                    self.rb.reset(QgsWkbTypes.PolygonGeometry)
                    self.rb.addGeometry(polygon)

        def canvasReleaseEvent(self, e):
            
            if(self.iface.activeLayer().name().upper().startswith('CRATER') or self.iface.activeLayer().name().upper().endswith('CRATER')):
                if e.button() == Qt.LeftButton:
                    if self.firstClick == False:
                       self.firstClick=True
                       # Do first click action
                       self.point1 = self.toMapCoordinates(e.pos())
                       self.iface.mainWindow().findChild(QAction, 'mActionDeselectAll').trigger()
                    else:
                        if self.secondClick == False: 
                            self.secondClick=True
                            # Do second click action
                            self.point2 = self.toMapCoordinates(e.pos())
                        else:
                            self.threePointCircle(self.iface.shapefilesegments)
                            self.firstClick=False
                            self.secondClick=False
                            polygon=self.rb.asGeometry()

                            # Write circle to shapefile
                            layer = self.iface.activeLayer()                 
                            poly = QgsFeature(layer.fields())
                            poly.setGeometry(polygon)
                            try:
                                poly.setAttribute("Diam_km",self.diam)
                                poly.setAttribute("x_coord",self.center_lon)
                                poly.setAttribute("y_coord",self.center_lat)
                                poly.setAttribute("tag","standard")
                                layer.startEditing()
                                layer.addFeature(poly)
                                layer.commitChanges()
                                #layer.selectByIds([layer.featureCount()-1])
                                layer.startEditing()
                                
                                self.craterDone=True
                                self.rb.reset(QgsWkbTypes.PolygonGeometry)
                            except:
                                self.iface.messageBar().pushMessage("Wrong Shapefile", duration=3)  
                else:
                    self.rb.reset(QgsWkbTypes.PolygonGeometry)
                    self.firstClick=False
                    self.secondClick=False
                    if self.craterDone:
                        layer = self.iface.activeLayer()
                        layer.startEditing()
                        layer.deleteFeature(layer.featureCount()-1)
                        layer.commitChanges()
                        layer.startEditing()
                        self.craterDone=False

    # Functions to list craters based on the user-defined settings
    def listcraters(self):    
        layer_area = QgsProject.instance().mapLayersByName(self.area_layer_list[self.area_layer_index])[0]
        layer_crat = QgsProject.instance().mapLayersByName(self.crat_layer_list[self.crat_layer_index])[0]
        
        crs_sourceA = QgsCoordinateReferenceSystem.fromProj4(layer_area.crs().toProj4())
        crs_sourceC = QgsCoordinateReferenceSystem.fromProj4(layer_crat.crs().toProj4())
        geod = str(CRS.from_proj4(layer_area.crs().toProj4()).get_geod()).split("'")[1]
        crs_lonlat = QgsCoordinateReferenceSystem.fromProj4('+proj=lonlat '+geod+' +no_defs +type=crs')
        SourceAToLonlat = QgsCoordinateTransform(crs_sourceA, crs_lonlat, QgsProject.instance().transformContext())
        SourceAToSourceC = QgsCoordinateTransform(crs_sourceA, crs_sourceC, QgsProject.instance().transformContext())
        
        layer_area.startEditing()
        
        self.expo_layer_crsinfo = layer_crat.crs().description()
        self.expo_area_info='unit_boundary = {vertex, sub_area, tag, lon, lat'
        self.expo_area_info_diam=''
 
        self.expo_area_all = 0
        self.expo_perimeter_all = 0
        area_vector_counter =0
        self.crater_data=[]
        
        for feat in layer_area.getFeatures():
            if feat.id() in self.area_list_selection:

                center=feat.geometry().centroid().asPoint()
                center_lonlat = SourceAToLonlat.transform(center)
                shapetemp=feat.geometry()      
                shapetemp.transform(SourceAToLonlat)
                shapepoints=shapetemp.asMultiPolygon()[0][0]
      
                # Build area vector information
                area_vectors=''
                for i in range(len(shapepoints)):
                    area_vector_counter=area_vector_counter+1
                    area_vectors=area_vectors+'\n'+str(area_vector_counter)+'\t'+str(feat.id()+1)+'\text\t'+'{:.14f}'.format(shapepoints[i].x())+'\t'+'{:.14f}'.format(shapepoints[i].y())
                
                crs_laea = QgsCoordinateReferenceSystem.fromProj4('+proj=laea +lat_ts=0 +lat_0='+str(round(center_lonlat.y()))+' +lon_0='+str(round(center_lonlat.x()))+' '+geod+' +units=m +no_defs +type=crs')
                
                SourceAToLaea  = QgsCoordinateTransform(crs_sourceA, crs_laea, QgsProject.instance().transformContext())
                SourceCToLaea  = QgsCoordinateTransform(crs_sourceC, crs_laea, QgsProject.instance().transformContext())

                areaLaea=feat.geometry()
                areaLaea.transform(SourceAToLaea)
                area_km2=areaLaea.area()/1000000 # area in (m2)
                perimeter_km=areaLaea.length()/1000 # perimeter in (m)
                feat.setAttribute("area",area_km2)
                layer_area.updateFeature(feat)

                self.expo_area_info=self.expo_area_info+'\n#\n# Area_name '+str(feat.id()+1)+' = '+str(feat.attribute('area_name'))+'\n' + '# Area_size ' +str(feat.id()+1)+' = {:.13f}'.format(area_km2)+' <km^2>\n'+ '# Area_perimeter ' +str(feat.id()+1)+' = {:.13f}'.format(perimeter_km)+' <km>\n#'+area_vectors
                self.expo_area_info_diam=self.expo_area_info_diam+'\n# '+str(feat.attribute('area_name'))+' = {:.13f}'.format(area_km2)+' <km^2>\n#' 
                self.expo_area_all = self.expo_area_all + area_km2
                self.expo_perimeter_all = self.expo_perimeter_all + perimeter_km

                # List craters 
                
                area=feat.geometry()
                area.transform(SourceAToSourceC)
                roughselectionbox=area.boundingBox()

                request = QgsFeatureRequest().setFilterRect(roughselectionbox)
                for featc in layer_crat.getFeatures(request):
                    crater=featc.geometry()
                    featc.perc='1'
                    #crater.transform(SourceCToLaea)

                    cratertag=str(featc.attribute('tag'))

                    if self.exportfractions == True:
                        # find fractions of all intersecting craters
                        if crater.intersects(area) == True:
                            #crater.transform(SourceCToLaea)
                            areabefore=crater.area()
                            
                            craterhalf=crater.difference(area)#areaLaea
                            areaafter=craterhalf.area()
                            perc=(areabefore-areaafter)/areabefore
                            if perc !=1:
                                featc.perc='{:.13f}'.format(perc)
                                
                            if self.excludemarked==False or cratertag == 'standard':
                                self.crater_data.append(featc)
                    else:
                        # find all craters with centers in area
                        crater_center=featc.geometry().centroid()
                        #crater_center.transform(SourceCToLaea)

                        if crater_center.within(area):
                            if self.excludemarked==False or cratertag == 'standard':
                                self.crater_data.append(featc)

        layer_area.commitChanges()
    
    # Functions to export crater-size-frequency measurements
    def exportstats(self):
        self.listcraters()
 
        layer = QgsProject.instance().mapLayersByName(self.crat_layer_list[self.crat_layer_index])[0]
        crs=CRS.from_proj4(layer.crs().toProj4())
        ellipsoid_info='\na-axis radius = {:.1f}'.format(crs.ellipsoid.semi_major_metre/1000)+' <km>\nb-axis radius = {:.1f}'.format(crs.ellipsoid.semi_minor_metre/1000)+' <km>\nc-axis radius = {:.1f}'.format(crs.ellipsoid.semi_major_metre/1000)+' <km>'
        
  
        crater_info=''
        for f in self.crater_data:
            crater_info=crater_info+'{:.13f}'.format(f.attribute('Diam_km'))+'\t'+f.perc+'\t'+'{:.13f}'.format(f.attribute('x_coord'))+'\t'+'{:.13f}'.format(f.attribute('y_coord'))+'\t'+'1'+'\n'
 
        # Combine all information for diam/scc export
        
        if self.exportformatindex==0:
            # Export scc file
            header = [
                    '# Spatial crater count',
                    '#',
                    '# Date of measurement = {}'.format(str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))),
                    '#',
                    '# Ellipsoid axes: {}'.format(ellipsoid_info),
                    'coordinate_system_name = {}'.format(self.expo_layer_crsinfo),
                    '#',
                    '# area_shapes:',
                    #'unit_boundary = {vertex, sub_area, tag, lon, lat',
                    '{}'.format(self.expo_area_info),
                    '}',
                    '#',
                    'Total_area = {:.13f} <km^2>'.format(self.expo_area_all),
                    'Total_perimeter = {:.13f} <km>'.format(self.expo_perimeter_all),
                    '#',
                    '# crater_diameters:',
                    'crater = {diam, fraction, lon, lat, topo_scale_factor',
                    '{}'.format(crater_info)+'}',
                ]
            export_content='\n'.join(header)
            
            with open(self.exportfile, 'w') as output_file:
                output_file.write(export_content)
                
        elif self.exportformatindex==1:
            # Export diam file
            header = [
                    '# Diam file for Craterstats',
                    '# Date of measurement export = {}'.format(str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))),
                    '# {}'.format(self.expo_area_info_diam),
                    '# Area, <km^2>',
                    'area = {:.13f}'.format(self.expo_area_all),
                    '#',
                    '# crater_diameters:',
                    'crater = {diam, fraction, lon, lat, topo_scale_factor',
                    '{}'.format(crater_info),
                ]
   
            export_content='\n'.join(header)
            
            with open(self.exportfile, 'w') as output_file:
                output_file.write(export_content)
                
        elif self.exportformatindex==2: 
            # Export crater shapefile
            layer_crat = QgsProject.instance().mapLayersByName(self.crat_layer_list[self.crat_layer_index])[0]
            crs=layer_crat.crs()
            layerFields = QgsFields()
            layerFields.append(QgsField('Diam_km', QVariant.Double))
            layerFields.append(QgsField('x_coord', QVariant.Double))
            layerFields.append(QgsField('y_coord', QVariant.Double))
            layerFields.append(QgsField('tag', QVariant.String))
            writer = QgsVectorFileWriter(self.exportfile, 'UTF-8', layerFields,QgsWkbTypes.Polygon,crs,'ESRI Shapefile')
            layer = self.iface.addVectorLayer(self.exportfile, '', 'ogr')
            del(writer)
            layer.startEditing()
            for f in self.crater_data:
                layer.addFeature(f)
            layer.commitChanges()
        elif self.exportformatindex==3:
            # Export crater as points shapefile
            
            layer_crat = QgsProject.instance().mapLayersByName(self.crat_layer_list[self.crat_layer_index])[0]
            crs=layer_crat.crs()
            
            layerFields = QgsFields()
            layerFields.append(QgsField('Diam_km', QVariant.Double))
            layerFields.append(QgsField('x_coord', QVariant.Double))
            layerFields.append(QgsField('y_coord', QVariant.Double))
            layerFields.append(QgsField('tag', QVariant.String))
            writer = QgsVectorFileWriter(self.exportfile, 'UTF-8', layerFields,QgsWkbTypes.Point,crs,'ESRI Shapefile')
            layer = self.iface.addVectorLayer(self.exportfile, '', 'ogr')
            del(writer)
            layer.startEditing()
            for f in self.crater_data:
                center=f.geometry().centroid()
                poly = QgsFeature(layer.fields())
                poly.setGeometry(center)
                poly.setAttribute("Diam_km",f.attribute('Diam_km'))
                poly.setAttribute("x_coord",f.attribute('x_coord'))
                poly.setAttribute("y_coord",f.attribute('y_coord'))
                poly.setAttribute("tag",f.attribute('tag'))
                layer.startEditing()
                layer.addFeature(poly)
            layer.commitChanges()

        pass



    # Function to plot statistics
    def plotstats(self):
        if len(self.area_list_selection)==0:
            self.iface.messageBar().pushMessage("Select area name", duration=2)
        else:    
            self.listcraters()
            
            self.con3.info1.setText(str(len(self.crater_data)))
            self.con3.info3.setText(str(len(self.area_list_selection)))
            self.con3.info4.setText('{:.2f} km²'.format(np.mean(self.expo_area_all)))

            self.iface.mainWindow().findChild(QAction, 'mActionDeselectAll').trigger()

            self.diams=[]
            self.ids=[]
            markedcounter=0
            for f in self.crater_data:
                self.diams.append(f.attribute('Diam_km'))
                self.ids.append(f.id())
                if f.attribute('tag')=='marked':
                    markedcounter=markedcounter+1
            
            self.con3.info2.setText(str(markedcounter))
            
            hist = np.histogram(self.diams, bins=self.bins)
            
            self.hist=np.array(hist[0])
            self.bins=np.array(hist[1])
            self.lower=self.bins[:-1]
            self.upper=self.bins[1:]
            
            out=self.hist>0
            
            self.hist=self.hist[out]
            self.upper=self.upper[out]
            self.lower=self.lower[out]
            self.middle=self.upper-(self.upper-self.lower)/2

            self.cum=np.flip(np.cumsum(np.flip(self.hist)))
            self.error=self.cum**0.5
            

            pl = self.craterPlotWidget(self)

            self.scene.clear()
            self.scene.addWidget(pl)
            
            self.con3.graphicsView.setScene(self.scene);

    
    # Function to highlight a user selected area
    def highlightarea(self):
        self.iface.mainWindow().findChild(QAction, 'mActionDeselectAll').trigger()
        layer_area = QgsProject.instance().mapLayersByName(self.area_layer_list[self.area_layer_index])[0]
        layer_area.selectByIds(self.area_list_selection)
    
    # Function to reset all info texts
    def resetinfos(self):
        self.con3.info1.setText('')
        self.con3.info2.setText('')
        self.con3.info3.setText('')
        self.con3.info4.setText('')
        self.con3.info5.setText('')
        
        self.con8.info1.setText('')
        self.con8.info2.setText('')
        self.con8.info3.setText('')
        self.con8.info4.setText('')
        self.con8.info5.setText('')

    # Function to create the crater-size-frequency shapefiles
    def createshapefiles(self):      
        self.con1.hide()
        fn=self.createfile
        if os.path.exists(fn) == True:
            shapetitle=os.path.basename(fn).split('.')
            layer = self.iface.addVectorLayer(fn,shapetitle[0], "ogr")
      
        else:
            crs=QgsProject.instance().crs()
            #pathtile=os.path.split(fn)
            craterfile=fn.split('.')[0]+'_CRATER.shp'
            areafile=fn.split('.')[0]+'_AREA.shp'

            if self.con1.check_create_crater.isChecked():
                layerFields = QgsFields()
                layerFields.append(QgsField('Diam_km', QVariant.Double))
                layerFields.append(QgsField('x_coord', QVariant.Double))
                layerFields.append(QgsField('y_coord', QVariant.Double))
                layerFields.append(QgsField('tag', QVariant.String))
                writer = QgsVectorFileWriter(craterfile, 'UTF-8', layerFields,QgsWkbTypes.Polygon,crs,'ESRI Shapefile')
                layer = self.iface.addVectorLayer(craterfile, '', 'ogr')
                del(writer)
                layer.startEditing()
                layer.commitChanges()
                self.layerstyle()
                layer.setRenderer(self.craterrenderer)
                layer.triggerRepaint()
            
            if self.con1.check_create_area.isChecked():
                layerFields = QgsFields()
                layerFields.append(QgsField('area', QVariant.Double))
                layerFields.append(QgsField('area_name', QVariant.String))
                writer = QgsVectorFileWriter(areafile, 'UTF-8', layerFields,QgsWkbTypes.Polygon,crs,'ESRI Shapefile')
                layer = self.iface.addVectorLayer(areafile, '', 'ogr')
                del(writer)
                layer.startEditing()
                layer.commitChanges()
                self.layerstyle()
                layer.setRenderer(self.arearenderer)
                layer.triggerRepaint()
    
    # Function to list the available crater and area files in all user interfaces
    def listlayers(self):
        layers = QgsProject.instance().layerTreeRoot().children()
        self.area_layer_list=[layer.name() for layer in layers if layer.name().upper().startswith('AREA') or layer.name().upper().endswith('AREA')]
        self.crat_layer_list=[layer.name() for layer in layers if layer.name().upper().startswith('CRATER') or layer.name().upper().endswith('CRATER')]

        self.con2.combo_area.clear() 
        self.con2.combo_crat.clear()      
        self.con3.combo_area.clear() 
        self.con3.combo_crat.clear()      
        self.con8.combo_crat1.clear()
        self.con8.combo_crat2.clear()
        self.con6.combo_crat.clear()
        self.con7.combo_area.clear()
        self.con4.combo_area.clear()
        
        if self.area_layer_list:
            self.con2.combo_area.addItems(self.area_layer_list)
            self.con3.combo_area.addItems(self.area_layer_list)
            self.con7.combo_area.addItems(self.area_layer_list)
            self.con4.combo_area.addItems(self.area_layer_list)
        
        if self.crat_layer_list:
            self.con2.combo_crat.addItems(self.crat_layer_list)
            self.con3.combo_crat.addItems(self.crat_layer_list)
            self.con8.combo_crat1.addItems(self.crat_layer_list)
            self.con8.combo_crat2.addItems(self.crat_layer_list)
            self.con6.combo_crat.addItems(self.crat_layer_list)

        self.area_layer_index=0
        self.crat_layer_index=0
        self.area_list_selection=[]

    # Function to mark or unmark craters 
    def mark_craters(self):
        layer = self.iface.activeLayer()
        layer.startEditing()
        if self.actions[0].isChecked() or self.actions[1].isChecked():
            if len(layer.selectedFeatures())==0:
                layer.selectByIds([layer.featureCount()-1])
                
        for feat in layer.selectedFeatures():
            if feat.attribute('tag')=='standard':
                feat.setAttribute("tag","marked")
            else:
                feat.setAttribute("tag","standard")
            layer.updateFeature(feat)
        layer.commitChanges()
        self.iface.messageBar().pushMessage(str(len(layer.selectedFeatures()))+" craters marked/unmarked", duration=2)
        self.iface.mainWindow().findChild(QAction, 'mActionDeselectAll').trigger()

    # Functions to set the user-selected options -----------------------------------------------------------------------
    def click_export_area_list(self):
        self.area_list_selection=[x.row() for x in self.con2.list_area.selectedIndexes()]
        self.highlightarea()
 
    def click_plot_area_list(self):
        self.area_list_selection=[x.row() for x in self.con3.list_area.selectedIndexes()]
        self.highlightarea()
   
    def click_grid_area_list(self):
        self.area_list_selection=[x.row() for x in self.con4.list_area.selectedIndexes()]
        self.highlightarea()

    def change_plot_area_list(self):
        self.area_layer_index=self.con3.combo_area.currentIndex()
        self.con3.list_area.clear()
        if self.area_layer_list:
            area_layer = QgsProject.instance().mapLayersByName(self.area_layer_list[self.area_layer_index])[0]
            self.con3.list_area.addItems([str(area.attribute('area_name')) for area in area_layer.getFeatures()])
        self.con3.list_area.clicked.connect(self.click_plot_area_list)

    def click_plot_selectall(self):
        [self.con3.list_area.item(x).setSelected(True) for x in range(self.con3.list_area.count())]
        self.click_plot_area_list()
    
    def click_expo_selectall(self):
        [self.con2.list_area.item(x).setSelected(True) for x in range(self.con2.list_area.count())]    
        self.click_export_area_list()
   
    def click_plot_selectnone(self):
        [self.con3.list_area.item(x).setSelected(False) for x in range(self.con3.list_area.count())]
        self.click_plot_area_list()
    
    def click_expo_selectnone(self):
        [self.con2.list_area.item(x).setSelected(False) for x in range(self.con2.list_area.count())]    
        self.click_export_area_list()

    def click_grid_selectnone(self):
        [self.con4.list_area.item(x).setSelected(False) for x in range(self.con4.list_area.count())]    
        self.click_export_area_list()

    def click_grid_selectall(self):
        [self.con4.list_area.item(x).setSelected(True) for x in range(self.con4.list_area.count())]    
        self.click_grid_area_list()        

    def change_grid_area_list(self):
        self.area_layer_index=self.con4.combo_area.currentIndex()
        self.con4.list_area.clear()
        if self.area_layer_list:
            area_layer = QgsProject.instance().mapLayersByName(self.area_layer_list[self.area_layer_index])[0]
            self.con4.list_area.addItems([str(area.attribute('area_name')) for area in area_layer.getFeatures()])
        self.con4.list_area.clicked.connect(self.click_grid_area_list)

    def change_expo_area_list(self):
        self.area_layer_index=self.con2.combo_area.currentIndex()
        self.con2.list_area.clear()
        if self.area_layer_list: 
            area_layer = QgsProject.instance().mapLayersByName(self.area_layer_list[self.area_layer_index])[0]
            self.con2.list_area.addItems([str(area.attribute('area_name')) for area in area_layer.getFeatures()])
        self.con2.list_area.clicked.connect(self.click_export_area_list)
    
    # Functions to set the user-selected layers -----------------------------------------------------------------------
    def change_expo_crat_index(self):
        self.crat_layer_index=self.con2.combo_crat.currentIndex()

    def change_plot_crat_index(self):
        self.crat_layer_index=self.con3.combo_crat.currentIndex()

    def change_con6_crat_index(self):
        self.crat_layer_index=self.con6.combo_crat.currentIndex()

    def change_con7_area_index(self):
        self.area_layer_index=self.con7.combo_area.currentIndex()

    def change_con8_crat_index(self):
        self.crat_layer_index=self.con8.combo_crat1.currentIndex()
 
    def change_con8_refe_index(self):
        self.refe_layer_index=self.con8.combo_crat2.currentIndex()

    def change_con8_mode_index(self):
        self.comparemodeindex=self.con8.combo_mode.currentIndex()
   
        try:
            self.scene.clear()
            pl = self.comparePlotWidget(self)
            self.scene.addWidget(pl)
            self.con8.graphicsView.setScene(self.scene)
            
            if self.comparemodeindex==0:
                self.con8.info2.setText('{:.2f} m'.format(self.overall_error))
            elif self.comparemodeindex==1:
                self.con8.info2.setText('{:.2f} %'.format(self.overall_errorP))    
            else:
                self.con8.info2.setText('{:.4f}'.format(self.overall_errorR))
        except:
            pass
    
    # Functions to set the user-selected options -----------------------------------------------------------------------

    def click_plot_marked(self):
        self.excludemarked=self.con3.checkmarked.isChecked()

    def change_con3_fractions(self):
        if self.con3.combo_fractions.currentIndex()==0:
            self.exportfractions=True
        else:
            self.exportfractions=False
      
    def change_con3_marked(self):
        if self.con3.combo_marked.currentIndex()==0:
            self.excludemarked=False
        else:
            self.excludemarked=True

    def change_con2_fractions(self):
        if self.con2.combo_fractions.currentIndex()==0:
            self.exportfractions=True
        else:
            self.exportfractions=False
      
    def change_con2_marked(self):
        if self.con2.combo_marked.currentIndex()==0:
            self.excludemarked=False
        else:
            self.excludemarked=True  
            
    def change_con2_export(self):
        self.exportformatindex=self.con2.combo_export.currentIndex()

    def importareas(self):
        temp = open(self.importfile,'r').read().splitlines()
        layer = QgsProject.instance().mapLayersByName(self.area_layer_list[self.area_layer_index])[0]
        
        geod = str(CRS.from_proj4(layer.crs().toProj4()).get_geod()).split("'")[1]
        crs_source =QgsCoordinateReferenceSystem.fromProj4(layer.crs().toProj4())
        crs_lonlat = QgsCoordinateReferenceSystem.fromProj4('+proj=lonlat '+geod+' +no_defs +type=crs')
        LonlatToSource = QgsCoordinateTransform(crs_lonlat, crs_source, QgsProject.instance().transformContext())
 
        readarea=False
        areacount=0
        points=[]
        tempname = ''
        tempsize = 0
        for line in temp:
            if readarea:
                tab=line.split('\t')
                if len(tab)==5:
                    points.append((float(tab[3]),float(tab[4])))
                    
                if line[0:11] == '# Area_name' or line[0:1]=='}':            
                    polygon = QgsGeometry.fromMultiPolygonXY( [[[ QgsPointXY( p[0], p[1] ) for p in points ]]] )
                    polygon.transform(LonlatToSource)
                    
                    # Write circle to shapefile               
                    poly = QgsFeature(layer.fields())
                    poly.setGeometry(polygon)
                    # try:

                    poly.setAttribute("area",tempsize)
                    poly.setAttribute("area_name",tempname)
                    layer.startEditing()
                    layer.addFeature(poly)
                    layer.commitChanges()
                    areacount=areacount+1
                    points=[]

            if line[0:11] == '# Area_name':
                readarea=True
                tempname = line.split('=')
                tempname=tempname[1]
                
            if line[0:11] == '# Area_size':
                tempsize = line.split('=')
                tempsize=tempsize[1].split(' ')
                tempsize=float(tempsize[1])
            if line[0:1]=='}':
                readarea=False
        self.iface.messageBar().pushMessage(" Areas ("+str(areacount)+") imported", duration=10)

    # Function to import craters from file
    def importcraters(self):
        temp = open(self.importfile,'r').read().splitlines()
        layer = QgsProject.instance().mapLayersByName(self.crat_layer_list[self.crat_layer_index])[0]
        
        readcrater=False
        count=0
        for line in temp:
            
            if readcrater:
                tab=line.split('\t')
                if len(tab)==5:
                    clon=tab[2]
                    clat=tab[3]
                    cdiam=float(tab[0])*1000

                    geod = str(CRS.from_proj4(layer.crs().toProj4()).get_geod()).split("'")[1]
                    crs_source = QgsCoordinateReferenceSystem.fromProj4(layer.crs().toProj4())
                    crs_Aeqd = QgsCoordinateReferenceSystem.fromProj4('+proj=aeqd +lat_0='+str(clat)+' +lon_0='+str(clon)+' +x_0=0 +y_0=0 '+geod+' +units=m +no_defs +type=crs')
                    AeqdToSource = QgsCoordinateTransform(crs_Aeqd, crs_source, QgsProject.instance().transformContext())

                    point1 = QgsPointXY( 0, cdiam/2)
                    point2 = QgsPointXY( 0, -cdiam/2)

                    # calculate circle in projection
                    diam = sqrt(point1.sqrDist(point2))/2
                    points=[]
                    nx=(point1.x()-point2.x())/2+point2.x()
                    ny=(point1.y()-point2.y())/2+point2.y()
                    segments=self.iface.shapefilesegments

                    for itheta in range(segments):
                        theta = itheta * (2.0 * pi / segments)
                        points.append((nx + diam * cos(theta),ny + diam * sin(theta)))
                    polygon = QgsGeometry.fromMultiPolygonXY( [[[ QgsPointXY( p[0], p[1] ) for p in points ]]] ) 

                    # split on poles and dateline
                    if float(clat)>0:
                        #North
                        crs_AqedNorth = QgsCoordinateReferenceSystem.fromProj4('+proj=aeqd +lat_0=90 +lon_0=180 +x_0=0 +y_0=0 '+geod+' +units=m +no_defs +type=crs')
                        AeqdToAqedNorth = QgsCoordinateTransform(crs_Aeqd, crs_AqedNorth, QgsProject.instance().transformContext())
                        AqedNorthToSource = QgsCoordinateTransform(crs_AqedNorth, crs_source, QgsProject.instance().transformContext())

                        polygon.transform(AeqdToAqedNorth)
                        polygonB=polygon.difference(self.iface.datelineN)
                        polygonB.transform(AqedNorthToSource)

                    else:
                        #South
                        crs_AqedSouth = QgsCoordinateReferenceSystem.fromProj4('+proj=aeqd +lat_0=-90 +lon_0=180 +x_0=0 +y_0=0 '+geod+' +units=m +no_defs +type=crs')
                        AeqdToAqedSouth = QgsCoordinateTransform(crs_Aeqd, crs_AqedSouth, QgsProject.instance().transformContext())
                        AqedSouthToSource = QgsCoordinateTransform(crs_AqedSouth, crs_source, QgsProject.instance().transformContext())
                        
                        polygon.transform(AeqdToAqedSouth)
                        polygonB=polygon.difference(self.iface.datelineS)
                        polygonB.transform(AqedSouthToSource)

                    # write circle to shapefile               
                    poly = QgsFeature(layer.fields())
                    poly.setGeometry(polygonB)
                    # try:
                        
                    poly.setAttribute("Diam_km",cdiam/1000)
                    poly.setAttribute("x_coord",clon)
                    poly.setAttribute("y_coord",clat)
                    poly.setAttribute("tag","standard")
                    
                    layer.startEditing()
                    layer.addFeature(poly)
                    layer.commitChanges()

                    count=count+1

            if line[0:8]=='crater =':
                readcrater=True 

        self.iface.messageBar().pushMessage(" Craters ("+str(count)+") imported", duration=10)
        
        
    # Function to export the crater comparison statistics
    def exportcompare(self):
        
        self.exportfile, _fil = QFileDialog.getSaveFileName(self.con2, "Select Output File ",QgsProject.instance().readPath("./")+"/comparison", 'text (*.txt);;All files (*.*)')
        if self.exportfile != '':
            
            self.comparestats()
            
            # Create header form
            header = [
                '# Comparative statistics of crater measurements',
                '#',
                '# Date of comparison = {}'.format(str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))),
                '#',
                '# Reference layer: '+self.crat_layer_list[self.refe_layer_index],
                '# Compared layer:  '+self.crat_layer_list[self.crat_layer_index],
                '#',
                '# Overall absolute error: {:.2f} m'.format(self.overall_error),
                '# Overall ratio: {:.4f}'.format(self.overall_errorR),
                '#',
                '# Compared craters:       '+str(self.compared),
                '# Overcounted craters:    '+str(self.overcount),
                '# Undercounted craters:   '+str(self.undercount),
                '#',
                '# Binned results = {bin number, bin lower limit [km], bin upper limit [km], bin absolute mean difference [m], bin relative mean difference [%]'
            ]
        
            export_content='\n'.join(header)
            
            line=''
            for i in range(0, len(self.hist)):
                line=line+str(i+1)+'\t'+'{:.3f}'.format(self.lower[i])+'\t'+'{:.3f}'.format(self.upper[i])+'\t'+'{:.6f}'.format(self.binnedmean[i])+'\t'+'{:.6f}'.format(self.binnedR[i])+'\n'

            export_content=export_content+'\n'+line+'}\n'
            
            #export_content=''

            export_content=export_content+'# Resulsts = {diameter [km], reference diameter [km], difference [m],  diameter/reference diameter, crater-ID, reference crater-ID \n'
            
            export_craters='\n'.join(self.coexportlist)
            
            export_content=export_content+export_craters+'\n}'

            with open(self.exportfile, 'w') as output_file:
                output_file.write(export_content)
        
  
        
    # Function to compare to sets of craters
    def comparestats(self):
        start_time = time.time()
        
        layer1 = QgsProject.instance().mapLayersByName(self.crat_layer_list[self.crat_layer_index])[0]
        layer2 = QgsProject.instance().mapLayersByName(self.crat_layer_list[self.refe_layer_index])[0]

        crs_source2 =QgsCoordinateReferenceSystem.fromProj4(layer2.crs().toProj4())
        
        geod = str(CRS.from_proj4(layer2.crs().toProj4()).get_geod()).split("'")[1]
        crs_lonlat = QgsCoordinateReferenceSystem.fromProj4('+proj=lonlat '+geod+' +no_defs +type=crs')
        LonlatToSource2 = QgsCoordinateTransform(crs_lonlat, crs_source2, QgsProject.instance().transformContext())

        self.con8.progressBar.show()
        outlist=[]

        cid=np.ones(layer2.featureCount())*(-1)
        rid=np.ones(layer2.featureCount())*(-1)

        cdist=np.full((layer2.featureCount()), np.inf)
        codiffA=np.zeros(layer2.featureCount())
        codiffR=np.zeros(layer2.featureCount())
        codiam=np.zeros(layer2.featureCount())
        rediam=np.zeros(layer2.featureCount())
         
        for feat in layer1.getFeatures():
            progress=int(feat.id()/layer1.featureCount()*100)
            self.con8.progressBar.setValue(progress)
            x=float(feat.attribute('x_coord'))
            y=float(feat.attribute('y_coord'))
            center = QgsGeometry.fromPointXY(QgsPointXY( x, y))
            center.transform(LonlatToSource2)
            indiam=float(feat.attribute('Diam_km'))
     
            diams=[]
            fids=[]
            dists=[]
            
            halfdiam=indiam*1000/2
            xMin=center.boundingBox().xMinimum()-halfdiam
            yMin=center.boundingBox().yMinimum()-halfdiam
            xMax=center.boundingBox().xMaximum()+halfdiam
            yMax=center.boundingBox().yMaximum()+halfdiam
            
            nbb = QgsRectangle(xMin, yMin, xMax, yMax)

            request = QgsFeatureRequest().setFilterRect(nbb)#.setFlags(QgsFeatureRequest.ExactIntersect)
            for f in layer2.getFeatures(request):

                diam=float(f.attribute('Diam_km'))
                # Check if the diameter is smaller than double or larger than half the size of the reference diameter
                if diam < indiam*2 and diam > indiam*0.5:

                    crs_Aeqd = QgsCoordinateReferenceSystem.fromProj4('+proj=aeqd +lat_0='+str(y)+' +lon_0='+str(x)+' +x_0=0 +y_0=0 '+geod+' +units=m +no_defs +type=crs')
                    LonlatToAeqd = QgsCoordinateTransform(crs_lonlat, crs_Aeqd, QgsProject.instance().transformContext())

                    center2 = QgsPointXY( float(f.attribute('x_coord')), float(f.attribute('y_coord')))
                    point2 = LonlatToAeqd.transform(center2)
                    point1 = QgsPointXY(0,0)
                    dist = sqrt(point2.sqrDist(point1))
    
                    # Check if the distance between crater centers is more than a quarter of the larger diameter
                    if indiam > diam:
                        t=indiam
                    else:
                        t=diam
                    if dist < t*1000/4:
                        if dist < cdist[int(f.id())]:
                            diams.append(diam)  
                            fids.append(float(f.id()))
                            dists.append(dist)

            if len(dists)>0:
                p=np.argmin(dists)
                diam=diams[p]
                fid=fids[p]
                tempdist=dists[p]
                n1=int(feat.id())
                n2=int(fid)

                if cid[n2]==-1:
                    cid[n2]=n1
                    rid[n2]=n2
                    cdist[n2]=tempdist
                    codiffA[n2]=indiam-diam
                    codiffR[n2]=(indiam/diam)#*100-100
                    codiam[n2]=diam
                    rediam[n2]=indiam
                else:
                    if tempdist <= cdist[n2]:

                        outlist.append(int(cid[n2]))
                        
                        cid[n2]=n1
                        cdist[n2]=tempdist
                        codiffA[n2]=indiam-diam
                        codiffR[n2]=(indiam/diam)#*100-100
                        codiam[n2]=diam
                        rediam[n2]=indiam
                        rid[n2]=n2

        request = QgsFeatureRequest().setFilterFids(outlist)
        outlist=[]
        
        for feat in layer1.getFeatures(request):
            progress=int(feat.id()/layer1.featureCount()*100)
            self.con8.progressBar.setValue(progress)
            x=float(feat.attribute('x_coord'))
            y=float(feat.attribute('y_coord'))
            center = QgsGeometry.fromPointXY(QgsPointXY( x, y))
            center.transform(LonlatToSource2)
            indiam=float(feat.attribute('Diam_km'))
     
            diams=[]
            fids=[]
            dists=[]
            halfdiam=indiam*1000/2
            xMin=center.boundingBox().xMinimum()-halfdiam
            yMin=center.boundingBox().yMinimum()-halfdiam
            xMax=center.boundingBox().xMaximum()+halfdiam
            yMax=center.boundingBox().yMaximum()+halfdiam
            
            nbb = QgsRectangle(xMin, yMin, xMax, yMax)

            request = QgsFeatureRequest().setFilterRect(nbb)
            for f in layer2.getFeatures(request):
                

                diam=float(f.attribute('Diam_km'))
                if diam < indiam*2 and diam > indiam*0.5:

                    crs_Aeqd = QgsCoordinateReferenceSystem.fromProj4('+proj=aeqd +lat_0='+str(y)+' +lon_0='+str(x)+' +x_0=0 +y_0=0 '+geod+' +units=m +no_defs +type=crs')
                    LonlatToAeqd = QgsCoordinateTransform(crs_lonlat, crs_Aeqd, QgsProject.instance().transformContext())

                    center2 = QgsPointXY( float(f.attribute('x_coord')), float(f.attribute('y_coord')))
                    point2 = LonlatToAeqd.transform(center2)
                    point1 = QgsPointXY(0,0)
                    dist = sqrt(point2.sqrDist(point1))
    
                    if indiam > diam:
                        t=indiam
                    else:
                        t=diam
                    if dist < t*1000/4:
                        if dist < cdist[int(f.id())]:
                            diams.append(diam)  
                            fids.append(float(f.id()))
                            dists.append(dist)

            if len(dists)>0:
                    p=np.argmin(dists)
                    diam=diams[p]
                    fid=fids[p]
                    tempdist=dists[p]
                    n1=int(feat.id())
                    n2=int(fid)

                    if cid[n2]==-1:
                        cid[n2]=n1
                        rid[n2]=n2
                        cdist[n2]=tempdist
                        codiffA[n2]=indiam-diam
                        codiffR[n2]=(indiam/diam)#*100-100
                        codiam[n2]=diam
                        rediam[n2]=indiam
                    else:
                        if tempdist <= cdist[n2]:

                            outlist.append(int(cid[n2]))
                            
                            cid[n2]=n1
                            cdist[n2]=tempdist
                            codiffA[n2]=indiam-diam
                            codiffR[n2]=(indiam/diam)#*100-100
                            codiam[n2]=diam
                            rediam[n2]=indiam
                            rid[n2]=n2

        sel=cid > -1
        self.error=codiffA[sel]
        self.error=self.error*1000
        self.errorR=codiffR[sel]
        self.errorP=self.errorR*100-100
        
        self.diams=codiam[sel]
        self.rediams=rediam[sel]

        self.cid=cid[sel]
        self.rid=rid[sel]

        self.compared=len(self.error)
        self.overcount=layer1.featureCount()-self.compared
        self.undercount=layer2.featureCount()-self.compared
        
        
        
        self.overall_error=np.mean(self.error)
        self.overall_errorP=(g_mean(self.errorR)*100)-100
        self.overall_errorR=g_mean(self.errorR)

        self.con8.info1.setText(str(self.compared))
        self.con8.info3.setText(str(self.overcount))
        self.con8.info4.setText(str(self.undercount))
        self.con8.progressBar.setValue(100)
        
                
        self.coexportlist=[]
        for i in range(0,len(self.cid)):
            #self.coexportlist.append('{:.5f}'.format(self.diams[i])+'\t{:.5f}'.format(self.rediams[i])+'\t{:.5f}'.format(self.error[i])+'\t{:.4f}'.format(self.errorR[i])+'\t{:.0f}'.format(self.cid[i]+1)+'\t{:.0f}'.format(self.rid[i]+1)+'\t{:.0f}'.format(self.overcount)+'\t{:.0f}'.format(self.undercount))
            self.coexportlist.append('{:.5f}'.format(self.diams[i])+'\t{:.5f}'.format(self.rediams[i])+'\t{:.5f}'.format(self.error[i])+'\t{:.4f}'.format(self.errorR[i])+'\t{:.0f}'.format(self.cid[i]+1)+'\t{:.0f}'.format(self.rid[i]+1))

        if self.comparemodeindex==0:
            self.con8.info2.setText('{:.2f} m'.format(self.overall_error))
            
        elif self.comparemodeindex==1:
            self.con8.info2.setText('{:.2f} %'.format(self.overall_errorP))
        else:
            self.con8.info2.setText('{:.4f}'.format(self.overall_errorR))

        hist = np.histogram(self.diams, bins=self.bins)
        self.hist=np.array(hist[0])
        self.bins=np.array(hist[1])
        self.lower=self.bins[:-1]
        self.upper=self.bins[1:]
        
        out=self.hist>0
        
        self.hist=self.hist[out]
        self.upper=self.upper[out]
        self.lower=self.lower[out]
        self.middle=self.upper-(self.upper-self.lower)/2
        
        self.binnedmean=[]
        self.binnedR=[]
        self.binnedP=[]

        self.binnedcount=[]
        for i in range(0, len(self.hist)):
            c=np.where(np.logical_and(self.diams>=self.lower[i], self.diams<self.upper[i]))
            self.binnedmean.append(np.mean(self.error[c[0]]))

            self.binnedR.append(g_mean(self.errorR[c[0]]))

            self.binnedP.append(g_mean(self.errorR[c[0]])*100-100)

            self.binnedcount.append(len(self.errorR[c[0]]))
        
        self.scene.clear()
        pl = self.comparePlotWidget(self)
        self.scene.addWidget(pl)
        self.con8.graphicsView.setScene(self.scene)
        self.con8.progressBar.hide()

    

    # Function to create a preview object of the grid
    def previewnet(self): 
        if self.checknumber(self.con4.line_gridsize.text()):
            gs=float(self.con4.line_gridsize.text())*1000
            layer_area = QgsProject.instance().mapLayersByName(self.area_layer_list[self.area_layer_index])[0]
            combinedarea=QgsGeometry().collectGeometry(p.geometry() for p in layer_area.selectedFeatures())
            
            # Calculates the bounding box of the combined area
            x1=combinedarea.boundingBox().xMinimum()
            x2=combinedarea.boundingBox().xMaximum()
            y1=combinedarea.boundingBox().yMinimum()
            y2=combinedarea.boundingBox().yMaximum()
            
            x1=x1-(gs/5)
            y1=y1-(gs/5)
            
            height=y2-y1
            width=x2-x1
            
            # Calculates the number of horizontal and vertical grid cells based on the height and width and the grid size
            hm=(height//gs)+1
            wm=(width//gs)+1
            
            # Calculates the total number of grid cells
            quadnumber=hm*wm
            if quadnumber <5000:
        
                self.nb.reset(QgsWkbTypes.PolygonGeometry)
                for i in range(int(hm)):
                    for k in range(int(wm)):

                        nx1=x1+k*gs
                        nx2=x1+(k+1)*gs
                        ny1=y1+i*gs
                        ny2=y1+(i+1)*gs

                        quad = QgsGeometry.fromPolygonXY([[
                        QgsPointXY( nx1, ny1),
                        QgsPointXY( nx1, ny2),
                        QgsPointXY( nx2, ny2),
                        QgsPointXY(  nx2, ny1),
                        QgsPointXY(  nx1, ny1)]])
                        if combinedarea.intersects(quad):
                            self.nb.addGeometry(quad)
            else:
                self.iface.messageBar().pushMessage("Too many grid cells", duration=3)
  
    # Function to export the measurement grid to a shapefile
    def exportnet(self):
        
        if self.checknumber(self.con4.line_gridsize.text()):

            gs=float(self.con4.line_gridsize.text())*1000
            layer_area = QgsProject.instance().mapLayersByName(self.area_layer_list[self.area_layer_index])[0]
            combinedarea=QgsGeometry().collectGeometry(p.geometry() for p in layer_area.selectedFeatures())
            
            # Calculates the bounding box of the combined area
            x1=combinedarea.boundingBox().xMinimum()
            x2=combinedarea.boundingBox().xMaximum()
            y1=combinedarea.boundingBox().yMinimum()
            y2=combinedarea.boundingBox().yMaximum()
            x1=x1-(gs/5)
            y1=y1-(gs/5)
            
            height=y2-y1
            width=x2-x1
    
            # Calculates the number of horizontal and vertical grid cells based on the height and width and the grid size
            hm=(height//gs)+1
            wm=(width//gs)+1

            # Calculates the total number of grid cells
            quadnumber=hm*wm
            if quadnumber <5000:
                self.exportfile, _fil = QFileDialog.getSaveFileName(self.con2, "Select Output File ",QgsProject.instance().readPath("./")+"/grid", 'Shapefiles(*.shp);;All files (*.*)')
                if self.exportfile != '':
            
                    layer_crat = QgsProject.instance().mapLayersByName(self.crat_layer_list[self.crat_layer_index])[0]
                    crs=layer_crat.crs()
                    
                    layerFields = QgsFields()
                    layerFields.append(QgsField('Grid_Cell', QVariant.String))
                    writer = QgsVectorFileWriter(self.exportfile, 'UTF-8', layerFields,QgsWkbTypes.Polygon,crs,'ESRI Shapefile')
                    layer = self.iface.addVectorLayer(self.exportfile, '', 'ogr')
                    del(writer)

                    layer.startEditing()

                    self.nb.reset(QgsWkbTypes.PolygonGeometry)
                    areacounter=0
                    for feat in layer_area.selectedFeatures():
                        quadcounter=0
                        areacounter=areacounter+1
                        area=feat.geometry()
                        
                        # Loops through each horizontal and vertical grid cell
                        for i in range(int(hm)):
                            for k in range(int(wm)):
                                nx1=x1+k*gs
                                nx2=x1+(k+1)*gs
                                ny1=y1+i*gs
                                ny2=y1+(i+1)*gs

                                quad = QgsGeometry.fromPolygonXY([[
                                QgsPointXY( nx1, ny1),
                                QgsPointXY( nx1, ny2),
                                QgsPointXY( nx2, ny2),
                                QgsPointXY(  nx2, ny1),
                                QgsPointXY(  nx1, ny1)]])

                                if area.intersects(quad):
                                    quadcounter=quadcounter+1
                                    info='Area: '+str(areacounter)+' Cell: '+str(quadcounter)
                                    poly = QgsFeature(layer.fields())
                                    poly.setGeometry(quad)
                                    poly.setAttribute("Grid_Cell",info)
                                    layer.addFeature(poly)
                    layer.commitChanges()
                    self.layerstyle()
                    layer.setRenderer(self.gridrenderer)
                    layer.triggerRepaint()
                    self.nb.reset(QgsWkbTypes.PolygonGeometry) 
            else:
                self.iface.messageBar().pushMessage("Too many grid cells", duration=3)

    # Function to define styles of the measurement layers
    def layerstyle(self):
        cratercategories = []
        val='standard'
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        layer_style = {}
        layer_style['color'] = '0,170,226'
        layer_style['width'] = '0.5'
        symbol_layer = QgsSimpleLineSymbolLayer.create(layer_style)
        symbol.changeSymbolLayer(0, symbol_layer)
        category = QgsRendererCategory(val, symbol, str(val))
        cratercategories.append(category)
        
        val='marked'
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        layer_style = {}
        layer_style['color'] = '220,20,60'
        layer_style['width'] = '0.5'
        symbol_layer = QgsSimpleLineSymbolLayer.create(layer_style)
        symbol.changeSymbolLayer(0, symbol_layer)
        category = QgsRendererCategory(val, symbol, str(val))
        cratercategories.append(category)
        self.craterrenderer = QgsCategorizedSymbolRenderer('tag',cratercategories)
        # area
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        layer_style = {}
        layer_style['color'] = '240,240,240'
        layer_style['width'] = '0.5'
        symbol_layer = QgsSimpleLineSymbolLayer.create(layer_style)
        symbol.changeSymbolLayer(0, symbol_layer)
        self.arearenderer =QgsSingleSymbolRenderer(symbol)
        # grid
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        layer_style = {}
        layer_style['color'] = '240,240,240'
        layer_style['width'] = '0.5'
        symbol_layer = QgsSimpleLineSymbolLayer.create(layer_style)
        symbol.changeSymbolLayer(0, symbol_layer)
        self.gridrenderer =QgsSingleSymbolRenderer(symbol)


    # Functions to execute the main functionality of the respective user interfaces --------------------------------------------------------------------
    
    def opt1_run(self):
        self.createfile, _fil = QFileDialog.getSaveFileName(self.con2, "Select   output file ",QgsProject.instance().readPath("./")+"/example", 'Shapefile(*.shp);;All files (*.*)')
        if self.createfile != '':
            self.createshapefiles()

    def opt2_run(self):
        if len(self.area_list_selection)==0:
            self.iface.messageBar().pushMessage("Select area name", duration=2)
        else: 
            area_layer = QgsProject.instance().mapLayersByName(self.area_layer_list[self.area_layer_index])[0]       
            all_areas=[str(area.attribute('area_name')) for area in area_layer.getFeatures()]
            sel_areas=[all_areas[index] for index in sorted(self.area_list_selection) if 0 <= index < len(all_areas)]

            #defaultname equals the shapefile name
            defaultfilename= QgsProject.instance().readPath("./")+'/'+self.area_layer_list[self.area_layer_index].lower().replace("_area", "").replace("area_", "")
            
            if len(sel_areas)!=len(all_areas):
                #add the selected areas to the defaultname
                defaultfilename=defaultfilename+'_'+ '_'.join(sel_areas).replace(" ", "_")
                
            if self.exportformatindex==0:
                self.exportfile, _fil = QFileDialog.getSaveFileName(self.con2, "Select Output File ",defaultfilename, 'Spatial crater count files(*.scc);;All files (*.*)')
            elif self.exportformatindex==1:
                self.exportfile, _fil = QFileDialog.getSaveFileName(self.con2, "Select Output File ",defaultfilename, 'Diameter files (*.diam);;All files (*.*)')
            else:
                self.exportfile, _fil = QFileDialog.getSaveFileName(self.con2, "Select Output File ",defaultfilename, 'Shapefile (*.shp);;All files (*.*)')
            if self.exportfile != '':
                self.iface.mainWindow().findChild(QAction, 'mActionDeselectAll').trigger()
                self.con2.hide()
                self.exportstats()


    def opt5_run(self):
        if self.con5.line_scale.text().isnumeric():
            self.iface.mapCanvas().zoomScale(float(self.con5.line_scale.text()))

    def opt8_run(self):
        if len(self.crat_layer_list)==0:
            self.iface.messageBar().pushMessage("Two CRATER layers are required", duration=3) 
        else:
            self.comparestats()
    
    def opt6_run(self):
        if len(self.crat_layer_list)==0:
            self.iface.messageBar().pushMessage("Load or create a target CRATER layer", duration=3) 
        else:
            self.importfile, _fil = QFileDialog.getOpenFileName(self.con7, "Select Input File ","", 'Spatial crater count files(*.scc);;All files (*.*)')
            if self.importfile != '':
                self.con6.hide()
                self.importcraters()

    def opt7_run(self):
        if len(self.area_layer_list)==0:
            self.iface.messageBar().pushMessage("Load or create a target AREA layer", duration=3) 
        else:
            self.importfile, _fil = QFileDialog.getOpenFileName(self.con7, "Select Input File ","", 'Spatial crater count files(*.scc);;All files (*.*)')
            if self.importfile != '':
                self.con7.hide()
                self.importareas()
        

    def checknumber(self,s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    # Functions to show the user interfaces of the respective tools --------------------------------------------------------------------
    
    def opt1(self):
        self.con1.show()
    
    def opt2(self):
        self.listlayers()  
        self.con2.show()
        r = self.con2.exec_()
        if r != 1:
            self.iface.mainWindow().findChild(QAction, 'mActionDeselectAll').trigger()
 
    def opt3(self):
        self.listlayers()
        self.scene.clear()
        self.resetinfos()
        self.con3.show()
        r = self.con3.exec_()
        if r != 1:
            self.iface.mainWindow().findChild(QAction, 'mActionDeselectAll').trigger()
  
    def opt4(self):
        self.listlayers()
        self.con4.show()
        
        r = self.con4.exec_()
        if r != 1:
            self.nb.reset(QgsWkbTypes.PolygonGeometry)

    def opt5(self):
        self.con5.show()


    def opt6(self):
        self.listlayers()
        self.con6.show()
  
    def opt7(self):    
        self.listlayers()
        self.con7.show()

    def opt8(self):
        self.listlayers()
        self.scene.clear()
        self.resetinfos()
        self.con8.show()

    # Function to show the tool description
    def main1(self):
        self.con0.show()

    # Function to activate the two-point crater drawing
    def main2(self):
        try:
            if(self.iface.activeLayer().name().upper().startswith('CRATER') or self.iface.activeLayer().name().upper().endswith('CRATER')):
                if self.actions[0].isChecked():
                    self.actions[1].setChecked(False)
                    self.canvas.setMapTool(self.draw2PointCrater)
                    self.canvas.unsetMapTool(self.draw3PointCrater)
                else:
                    self.canvas.unsetMapTool(self.draw2PointCrater)
                    self.iface.activeLayer().commitChanges()
                    self.iface.mainWindow().findChild(QAction, 'mActionDeselectAll').trigger()
            else:
                self.iface.messageBar().pushMessage("Select the 'CRATER' shapefile.", duration=3)
                self.actions[0].setChecked(False)
        except:
            pass
    
    # Function to activate the three-point crater drawing
    def main3(self):
        try:
            if(self.iface.activeLayer().name().upper().startswith('CRATER') or self.iface.activeLayer().name().upper().endswith('CRATER')):
                if self.actions[1].isChecked():
                    self.actions[0].setChecked(False)
                    self.canvas.unsetMapTool(self.draw2PointCrater)
                    self.canvas.setMapTool(self.draw3PointCrater)
                    
                else:
                    self.canvas.unsetMapTool(self.draw3PointCrater)
                    self.iface.activeLayer().commitChanges()
                    self.iface.mainWindow().findChild(QAction, 'mActionDeselectAll').trigger()
            else:
                self.iface.messageBar().pushMessage("Select the 'CRATER' shapefile.", duration=3)
                self.actions[1].setChecked(False)
        except:
            pass
    
    # Function to start marking/unmarking craters
    def main4(self):
        if self.iface.activeLayer() is not None:
            self.mark_craters()     

    def setscale(self):
        try:            
            self.iface.mapCanvas().zoomScale(float(self.con5.line_scale.text()))
        except:
            self.con5.show()

# End
