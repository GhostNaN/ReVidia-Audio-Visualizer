#!venv/bin/python
# -*- coding: utf-8 -*-

import ReverseFFT
import ReVidia
import sys
import time
import random
import subprocess
import threading as th
import multiprocessing as mp

from PyQt5.QtCore import Qt, QPoint, QRect, pyqtSignal
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


# A hollow window to contain ReVidiaMain window to incorporate docking
class MetaWindow(QMainWindow):
    def __init__(self, main):
        super(MetaWindow, self).__init__()

        self.main = main

        self.setWindowIcon(QIcon('docs/REV.png'))
        self.setWindowTitle('ReVidia')
        self.setMinimumSize(200, 150)
        self.setAttribute(Qt.WA_TranslucentBackground, True)  # Initial background is transparent

        self.setCentralWidget(self.main)

    # Forwarding Events to ReVidiaMain
    def keyPressEvent(self, event):
        ReVidiaMain.keyPressEvent(self.main, event)

    def closeEvent(self, event):
        self.main.close()

# Because using self.update() or self.repaint() in the main loop was too much to ask for... ¯\_(ツ)_/¯
class ForcePaint(QWidget):
    forcePaint = pyqtSignal()

# Create the self object and main window
class ReVidiaMain(QMainWindow):
    def __init__(self):
        super(ReVidiaMain, self).__init__()

        self.meta = MetaWindow(self)
        self.call = ForcePaint()
        self.call.forcePaint.connect(self.update)

        # Sets up window to be in the middle and to be half screen height
        screen = QApplication.desktop().screenNumber(
            QApplication.desktop().cursor().pos())
        screenSize = QApplication.desktop().screenGeometry(screen)
        self.width = screenSize.width() // 2
        self.height = screenSize.height() // 2
        self.left = screenSize.center().x() - self.width // 2
        self.top = screenSize.center().y() - self.height // 2

        # Default variables
        # [startPoint, startCurve, midPoint, midPointPos, endCurve, endPoint]
        self.pointsList = [0, 1, 1000, 0.66, 1, 12000]
        self.split = 0
        self.curvy = 0
        self.interp = 8
        self.audioBuffer = 4096
        self.backgroundColor = QColor(50, 50, 50, 255)  # R, G, B, Alpha 0-255
        self.mainColor = QColor(255, 255, 255, 255)
        self.outlineColor = QColor(0, 0, 0)
        self.lumen = 0
        self.stars = {}
        self.gradient = 0
        self.checkRainbow = 0
        self.plotWidth = 14
        self.gapWidth = 6
        self.outlineSize = 0
        self.dataCap = 0
        self.wholeWidth = self.plotWidth + self.gapWidth
        self.outlineOnly = 0
        self.cutout = 0
        self.checkFreq = 0
        self.checkNotes = 0
        self.checkDeadline = 0
        self.checkPlotNum = 0
        self.checkLatency = 0
        self.checkDB = 0
        self.mainMode = 'Bars'
        self.frameRate = 150

        self.initUI()

    # Setup main window
    def initUI(self, reload=False):
        self.meta.setGeometry(self.left, self.top, self.width, self.height)
        self.setTextPalette()
        if not reload:
            self.getDevice(True)  # Get Device before starting

        # Setup menu bar
        mainBar = QMenuBar()
        mainMenu = mainBar.addMenu('Main')
        mainMenu.setToolTipsVisible(True)
        designMenu = mainBar.addMenu('Design')
        designMenu.setToolTipsVisible(True)
        statsMenu = mainBar.addMenu('Stats')
        statsMenu.setToolTipsVisible(True)

        profilesMenu = QMenu('Profiles', self)
        profilesMenu.setToolTip('Save and Load Profiles')
        save = QAction('Save', self)
        save.triggered.connect(lambda triggered, request='save': self.setProfile(request))
        load = QAction('Load', self)
        load.triggered.connect(lambda triggered, request='load': self.setProfile(request))
        delete = QAction('Delete', self)
        delete.triggered.connect(lambda triggered, request='delete': self.setProfile(request))
        profilesMenu.addActions((save, load, delete))

        deviceDialog = QAction('Device', self)
        deviceDialog.setToolTip('Select Audio Device')
        deviceDialog.triggered.connect(self.getDevice)

        FFTAudDock = QAction('Reverse FFT', self)
        FFTAudDock.setToolTip('Listen to the Sound of the Visualizer')
        FFTAudDock.triggered.connect(self.getFFTAudDock)

        scaleDock = QAction('Freq Scale', self)
        scaleDock.setToolTip('Modify the Frequency Scale')
        scaleDock.triggered.connect(self.getScaleDock)

        splitCheck = QAction('Split Audio', self)
        splitCheck.setCheckable(True)
        splitCheck.setToolTip('Toggle to Split Audio Channels')
        splitCheck.toggled.connect(self.setSplit)
        splitCheck.setChecked(self.split)

        curvyMenu = QMenu('Curviness', self)
        curvyMenu.setToolTip('Set How Much the Plots Curves')
        curvySettings = ['No Curves', 'Sharp', 'Narrow', 'Loose', 'Flat']
        curveList = [0, (0.05, 3), (0.15, 3), (0.30, 3), (1, 3)]  # [0, (5,3), (11,3), (23,3), (43,3)]
        self.curvyDict = {}
        for f in range(5):
            curve = curveList[f]
            self.curvyDict[str(curve)] = QAction(curvySettings[f], self)
            self.curvyDict[str(curve)].setCheckable(True)
            self.curvyDict[str(curve)].triggered.connect(lambda checked, index=curve: self.setCurve(index))
            curvyMenu.addAction(self.curvyDict[str(curve)])
        self.curvyDict[str(self.curvy)].setChecked(True)
        self.curvyDict[str(self.curvy)].trigger()

        interpMenu = QMenu('Interpolation', self)
        interpMenu.setToolTip('Set Interp Amount (Noise)')
        interpSettings = ['No Interpolation', 'Low [4x]', 'Mid [8x]', 'High [16x]', 'Ultra [32x]']
        interpList = [0, 4, 8, 16, 32]
        interp = 0
        self.interpDict = {}
        for f in range(5):
            interp = interpList[f]
            self.interpDict[str(interp)] = QAction(interpSettings[f], self)
            self.interpDict[str(interp)].setCheckable(True)
            self.interpDict[str(interp)].triggered.connect(lambda checked, index=interp: self.setInterp(index))
            interpMenu.addAction(self.interpDict[str(interp)])
        self.interpDict[str(self.interp)].setChecked(True)
        self.interpDict[str(self.interp)].trigger()

        bufferMenu = QMenu('Audio Buffer', self)
        bufferMenu.setToolTip('Set the Audio Buffer Size')
        audioRate = 1024
        self.audioBufferDict = {}
        for f in range(5):
            self.audioBufferDict[str(audioRate)] = QAction(str(audioRate), self)
            self.audioBufferDict[str(audioRate)].setCheckable(True)
            self.audioBufferDict[str(audioRate)].triggered.connect(lambda checked, index=audioRate: self.setAudioBuffer(index))
            bufferMenu.addAction(self.audioBufferDict[str(audioRate)])
            audioRate *= 2
        self.audioBufferDict[str(self.audioBuffer)].setChecked(True)
        self.audioBufferDict[str(self.audioBuffer)].trigger()

        colorMenu = QMenu('Color', self)
        colorMenu.setToolTip('Select Colors and Transparency')
        mainColorDialog = QAction('Main Color', self)
        mainColorDialog.triggered.connect(self.setMainColor)
        backColorDialog = QAction('Background Color', self)
        backColorDialog.triggered.connect(self.setBackgroundColor)
        outColorDialog = QAction('Outline Color', self)
        outColorDialog.triggered.connect(self.setOutlineColor)
        rainbowCheck = QAction('Rainbow', self)
        rainbowCheck.setCheckable(True)
        rainbowCheck.triggered.connect(self.setRainbow)
        rainbowCheck.setChecked(self.checkRainbow)

        colorMenu.addAction(mainColorDialog)
        colorMenu.addAction(backColorDialog)
        colorMenu.addAction(outColorDialog)
        colorMenu.addAction(rainbowCheck)

        lumenMenu = QMenu('Illuminate', self)
        lumenMenu.setToolTip('Change the Bars Alpha Scale')
        lumenSettings = ['None', '1/4', '1/2', '3/4', 'Whole']
        lumenList = [0, 25, 50, 75, 100]
        self.lumenDict = {}
        for f in range(5):
            lumen = lumenList[f]
            self.lumenDict[str(lumen)] = QAction(lumenSettings[f], self)
            self.lumenDict[str(lumen)].setCheckable(True)
            self.lumenDict[str(lumen)].triggered.connect(lambda checked, index=lumen: self.setLumen(index))
            lumenMenu.addAction(self.lumenDict[str(lumen)])
        self.lumenDict[str(self.lumen)].setChecked(True)
        self.lumenDict[str(self.lumen)].trigger()

        starsDock = QAction('Stars', self)
        starsDock.setToolTip('Animate Background with Stars')
        starsDock.triggered.connect(self.getStarsDock)

        gradDock = QAction('Gradient', self)
        gradDock.setToolTip('Create a Gradient')
        gradDock.triggered.connect(self.getGradDock)

        sizesCheck = QAction('Dimensions', self)
        sizesCheck.setToolTip('Change the Bars Dimensions')
        sizesCheck.triggered.connect(self.getDimenDock)

        self.autoLevel = QAction('Auto Level', self)
        self.autoLevel.setCheckable(True)
        self.autoLevel.setToolTip('Auto Scale the Height to Fit the Data')
        self.autoLevel.triggered.connect(self.setAutoLevel)
        if not self.dataCap:
            self.autoLevel.setChecked(True)

        outlineCheck = QAction('Outline Only', self)
        outlineCheck.setCheckable(True)
        outlineCheck.setToolTip('Draw Only the Outline With Main Color')
        outlineCheck.toggled.connect(self.setOutlineOnly)
        outlineCheck.setChecked(self.outlineOnly)

        cutoutCheck = QAction('Cutout', self)
        cutoutCheck.setCheckable(True)
        cutoutCheck.setToolTip('Toggle to Cutout Background')
        cutoutCheck.toggled.connect(self.setCutout)
        cutoutCheck.setChecked(self.cutout)

        deadlineCheck = QAction('Deadline', self)
        deadlineCheck.setCheckable(True)
        deadlineCheck.setToolTip('Display FPS Deadline Ratio')
        deadlineCheck.toggled.connect(self.showDeadline)
        deadlineCheck.setChecked(self.checkDeadline)

        plotNumCheck = QAction('Plots', self)
        plotNumCheck.setCheckable(True)
        plotNumCheck.setToolTip('Display Amount of Plots Visible')
        plotNumCheck.toggled.connect(self.showPlotNum)
        plotNumCheck.setChecked(self.checkPlotNum)

        latencyCheck = QAction('Latency', self)
        latencyCheck.setCheckable(True)
        latencyCheck.setToolTip('Display Latency Between Display and Audio')
        latencyCheck.toggled.connect(self.showLatency)
        latencyCheck.setChecked(self.checkLatency)

        dbBarCheck = QAction('dB Bar', self)
        dbBarCheck.setCheckable(True)
        dbBarCheck.setToolTip('Display dB Bar Indicating Volume')
        dbBarCheck.toggled.connect(self.showDB)
        dbBarCheck.setChecked(self.checkDB)

        self.freqsCheck = QAction('Frequencies', self)
        self.freqsCheck.setCheckable(True)
        self.freqsCheck.setToolTip('Show Each Plot\'s Frequency')
        self.freqsCheck.toggled.connect(self.showFreq)
        self.freqsCheck.setChecked(self.checkFreq)

        self.notesCheck = QAction('Notes', self)
        self.notesCheck.setCheckable(True)
        self.notesCheck.setToolTip('Frequencies as Notes')
        self.notesCheck.toggled.connect(self.showNotes)
        self.notesCheck.setChecked(self.checkNotes)

        self.mainModeCheck = QPushButton(self.mainMode, self)
        self.mainModeCheck.pressed.connect(self.setMainMode)

        fpsSpinBox = QSpinBox()
        fpsSpinBox.setRange(1, 999)
        fpsSpinBox.setSuffix(' FPS')
        fpsSpinBox.valueChanged.connect(self.setFrameRate)
        fpsSpinBox.setValue(self.frameRate)
        fpsSpinBox.setKeyboardTracking(False)
        fpsSpinBox.setFocusPolicy(Qt.ClickFocus)

        mainMenu.addMenu(profilesMenu)
        mainMenu.addAction(deviceDialog)
        mainMenu.addAction(FFTAudDock)
        mainMenu.addAction(scaleDock)
        mainMenu.addAction(splitCheck)
        mainMenu.addMenu(curvyMenu)
        mainMenu.addMenu(interpMenu)
        mainMenu.addMenu(bufferMenu)
        designMenu.addMenu(colorMenu)
        designMenu.addMenu(lumenMenu)
        designMenu.addAction(starsDock)
        designMenu.addAction(gradDock)
        designMenu.addAction(sizesCheck)
        designMenu.addAction(self.autoLevel)
        designMenu.addAction(outlineCheck)
        designMenu.addAction(cutoutCheck)
        statsMenu.addAction(deadlineCheck)
        statsMenu.addAction(plotNumCheck)
        statsMenu.addAction(latencyCheck)
        statsMenu.addAction(dbBarCheck)
        statsMenu.addAction(self.freqsCheck)
        statsMenu.addAction(self.notesCheck)

        self.menuWidget = QWidget(self)
        menu = QHBoxLayout(self.menuWidget)

        menu.addWidget(mainBar)
        menu.addWidget(self.mainModeCheck)
        menu.addWidget(fpsSpinBox)
        menu.addStretch(10)

        self.setMenuWidget(self.menuWidget)

        self.meta.show()
        self.starterVars()
        if not reload:
            self.updateStack()
            self.startProcesses()

    def starterVars(self):
        # Define placeholder stater variables
        self.plotValues = [0]
        self.plotSplitValues = [0]
        self.delay = 0
        self.frames = 0
        self.paintBusy = 0
        self.paintTime = 0
        self.paintDelay = (1 / self.frameRate)
        self.reverseFFT = 0
        self.barsShape = [QRect()]
        self.barsOutlineShape = [QRect()]
        self.smoothShape = QPolygon()
        self.starsList = []
        self.loopTime = 0

    def startProcesses(self):
        self.blockLock = th.Lock()
        self.syncLock = mp.Lock()
        # Queues to change settings in process
        self.dataQ = mp.Queue()
        self.proQ = mp.Queue()
        self.mainQ = mp.Queue()
        # Values to carry timings
        dataTime = mp.Value('d')
        self.proTime = mp.Value('d')
        self.audioPeak = mp.Value('i', 0)
        # Arrays to transfer data between processes very fast
        self.dataArray = mp.Array('i', 16384)
        dataArray2 = mp.Array('i', 16384)
        self.proArray = mp.Array('i', 8192)
        self.proArray2 = mp.Array('i', 8192)

        # Create separate process for audio data collection
        self.T1 = mp.Process(target=ReVidia.collectData, args=(
            dataTime, self.dataArray, dataArray2, self.dataQ, self.ID, self.audioBuffer, self.split))

        # Create separate process for audio data processing
        self.P1 = mp.Process(target=ReVidia.processData, args=(
            self.syncLock, dataTime, self.proTime, self.audioPeak, self.dataArray, dataArray2, self.proArray, self.proArray2, self.proQ, self.dataQ,
            self.frameRate, self.audioBuffer, self.plotsList, self.split, self.curvyValue, self.interp))

        # Separate main thread from event loop
        self.mainThread = th.Thread(target=self.mainLoop)

        self.T1.daemon = True
        self.P1.daemon = True
        self.T1.start()
        self.P1.start()
        self.mainThread.start()

    def mainLoop(self):
        timer = time.time()
        while True:
            # Gets the real frametime for time sensitive objects
            self.loopTime = time.time() - timer
            timer = time.time()

            # Gets final results from processing
            self.delay = self.proTime.value
            plotsData = self.proArray[:self.plotsAmt]
            splitPlotData = self.proArray2[:self.plotsAmt]

            # Resize Data with user's defined height or the data's height
            self.plotValues = ReVidia.rescaleData(plotsData, self.dataCap, self.size().height())
            self.plotSplitValues = ReVidia.rescaleData(splitPlotData, self.dataCap, self.size().height())

            # Create the shapes for painter to draw
            if self.mainMode == 'Bars':
                self.barsShape = self.createBars()
                if self.outlineSize > 0:
                    self.barsOutlineShape = self.createBarsOutline()
            else:
                self.smoothShape = self.createSmooth()
            if self.stars:
                self.createStars()

            if not self.P1.is_alive():
                print('RIP Audio Processor, shutting down.')
                self.close()
            if not self.T1.is_alive():
                print('RIP Audio Data Collector, shutting down.')
                self.close()

            try:    # Avoid Crash
                self.syncLock.release()   # Start processing next frame
            except: pass

            if not self.paintBusy:    # Rare fail safe
                # self.update()
                self.call.forcePaint.emit()
                self.updateMiscObjects()

                blockTime = time.time()
                self.blockLock.acquire(timeout=1)
                if (time.time() - blockTime) >= 1:
                    print('QT refusing to paint, attempting revive...')
                    self.repaint()  # Revives painter

            if self.mainQ.qsize() > 0:
                break

    def updateMiscObjects(self):
        if self.reverseFFT:
            if not hasattr(self, 'waveFile'):
                self.waveFile = ReverseFFT.createFile(self.sampleRate)
                self.oldVolList = []
                self.oldTimes = []
                # Insert a Tiny bit of random to prevent overlap in freq's
                self.waveFreqList = list(map(lambda freq: freq + random.uniform(-0.1, 0.1), self.freqList[:-1]))

            self.oldVolList, self.oldTimes = ReverseFFT.start(self.waveFile, self.sampleRate, self.plotValues, self.loopTime,
                                                              self.size().height(), self.oldVolList, self.oldTimes, self.waveFreqList)
        else:
            if hasattr(self, 'waveFile'):
                self.waveFile.close()
                del self.waveFile

        if self.checkDeadline:

            block = self.frameRate // 10
            if block < 1: block = 1
            if self.frames % block == 0:
                self.latePercent = round(((1 / self.frameRate) / self.loopTime) * 100, 2)

            # print(1 / self.loopTime) testing frame times

        # Update height slider
        if hasattr(self, 'dimenDock'):
            if self.dimenDock.heightSlider.isSliderDown():
                self.dimenDock.setDataCap()
            else:
                self.dimenDock.heightSlider.setValue(0)

        if self.checkRainbow:
            self.setRainbow(1)

    # Convenience function to update all at once in the right order
    def updateStack(self):
        self.updatePlotsAmt()
        self.updatePlots()
        self.updateFreqList()

    def updatePlots(self):
        plot = self.sampleRate / self.audioBuffer

        startPoint = self.pointsList[0] / plot
        startCurve = startPoint * self.pointsList[1]
        midPoint = self.pointsList[2] / plot
        midPointPos = int(round(self.plotsAmt * self.pointsList[3]))
        endCurve = midPoint * self.pointsList[4]
        endPoint = self.pointsList[5] / plot

        startScale = ReVidia.quadBezier(startPoint, midPoint, startCurve, midPointPos)
        endScale = ReVidia.quadBezier(midPoint, endPoint, endCurve, self.plotsAmt - midPointPos, True)
        plots = startScale + endScale

        self.plotsList = list(map(int, ReVidia.dataPlotter(plots, 1, self.audioBuffer // 2)))
        if hasattr(self, 'proQ'):
            self.proQ.put(['plots', self.plotsList])

    def updatePlotsAmt(self):
        self.plotsAmt = self.size().width() // self.wholeWidth

        if self.plotsAmt > self.audioBuffer:   # Max of buffer to avoid crash
            self.plotsAmt = self.audioBuffer
        if self.plotsAmt < 2: self.plotsAmt = 2   # Min of 2 point to avoid crash

        if self.curvy:
            self.setCurve(self.curvy)

    def updateFreqList(self):
        # Assigns frequencies locations based on plots
        freq = self.sampleRate / self.audioBuffer
        self.freqList = list(map(lambda plot: plot * freq, self.plotsList))

    def setTextPalette(self):
        if not hasattr(self, 'textPalette'):
            self.textPalette = QPalette()
        # Sets the text color to better see it against background
        if self.backgroundColor.value() <= 128:
            self.textPalette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        else:
            self.textPalette.setColor(QPalette.WindowText, QColor(0, 0, 0))

        self.setPalette(self.textPalette)

    def createBars(self):
        spacing = (self.gapWidth // 2)
        xPoints = [((x * self.wholeWidth) + spacing) for x in range(len(self.plotValues))]

        floor = self.size().height()

        if self.split:
            floor //= 2
            yPoints = list(map(lambda y: int(floor - (y / 2)), self.plotValues))
            bars = list(map(lambda x, y, height, splitH: QRect(x, y, self.plotWidth, int((height + splitH) / 2)),
                             xPoints, yPoints, self.plotValues, self.plotSplitValues))
        else:
            yPoints = list(map(lambda y: int(floor - y), self.plotValues))
            bars = list(map(lambda x, y, height: QRect(x, y, self.plotWidth, height), xPoints, yPoints, self.plotValues))

        return bars

    # Hack way of making outline without the (Slow QPen)
    def createBarsOutline(self):
        outlineRects = []
        outlineSize = self.outlineSize
        if outlineSize > self.plotWidth // 2: outlineSize = self.plotWidth // 2
        for rect in self.barsShape:
            outlineRects.append(QRect(rect.x(), rect.y(), outlineSize, rect.height()))  # Left
            outlineRects.append(QRect(rect.x(), rect.y(), rect.width(), outlineSize))  # Top
            outlineRects.append(QRect(rect.x() + rect.width(), rect.y(), -outlineSize, rect.height()))  # Right
            outlineRects.append(QRect(rect.x(), rect.y() + rect.height(), rect.width(), -outlineSize))  # Bottom

        return outlineRects

    def createSmooth(self):
        # Plots Setup
        spacing = self.wholeWidth // 2
        xPoints = [((x * self.wholeWidth) + spacing) for x in range(len(self.plotValues))]

        height = self.size().height()
        start = -self.outlineSize
        end = self.outlineSize + self.size().width()

        if self.split:
            height //= 2
            yPoints = list(map(lambda y: int(height - (y / 2)), self.plotValues))
            ySplitPoints = list(map(lambda y: int(height + (y / 2)), self.plotSplitValues))
            floor = height
        else:
            yPoints = list(map(lambda y: int(height - y), self.plotValues))
            floor = height + self.outlineSize

        # Plot out points
        allPoints = [start, floor, start, yPoints[0]]
        [allPoints.extend(i) for i in zip(xPoints, yPoints)]
        allPoints.extend([end, yPoints[-1], end, floor])
        if self.split:  # Clockwise Loop to start
            allPoints.extend([end, ySplitPoints[-1]])
            [allPoints.extend(i) for i in zip(reversed(xPoints), reversed(ySplitPoints))]
            allPoints.extend([start, ySplitPoints[0], start, floor])

        shape = QPolygon(allPoints)
        return shape

    def createStars(self):
        # Parse star size range
        starSizes = self.stars['SizeRange']
        starSizes = [min(starSizes), max(starSizes) + 1]

        # Starting off with random spread of stars
        while len(self.starsList) < self.stars['Amount']:
            self.starsList.append((random.randrange(0, self.size().width()),
                                   random.randrange(0, self.size().height()),
                                   random.randrange(starSizes[0], starSizes[1])))
        while len(self.starsList) > self.stars['Amount']:
            self.starsList.remove(random.choice(self.starsList))

        # Parse star plot range
        plotRange = self.stars['PlotRange']
        plotMod = self.plotValues[min(plotRange) - 1:max(plotRange)]

        # Main modifier that effects speed and twinkle based on user defined plot range avg.
        modifier = (sum(plotMod) / len(plotMod)) / self.size().height()

        # Calculate speed and angle of stars
        import math
        angleX = -math.sin(self.stars['Angle'] * (math.pi / 180))
        angleY = math.cos(self.stars['Angle'] * (math.pi / 180))

        speed = self.stars['MinSpeed']
        speed += modifier * (self.stars['ModSpeed'] - self.stars['MinSpeed'])

        # Normalize speed with frametime
        speed *= self.loopTime

        # Apply speed and angle to stars while removing out of bounds stars
        newStarList = []
        for star in self.starsList:
            if (star[0] - star[2] > self.size().width()) or (star[0] + star[2] < 0):
                pass
            elif (star[1] - star[2] > self.size().height()) or (star[1] + star[2] < 0):
                pass
            else:
                starXPos = star[0] + (speed * angleX)
                StarYPos = star[1] + (speed * angleY)
                newStarList.append((starXPos, StarYPos, star[2]))

        self.starsList = newStarList

        # Weighted random for stars start side
        xSideSizeRatio = (self.size().width() / self.size().height())
        ySideSizeRatio = (self.size().height() / self.size().width())
        xWeight = int((abs(angleX) + (ySideSizeRatio * abs(angleX))) * 10)
        yWeight = int((abs(angleY) + (xSideSizeRatio * abs(angleY))) * 10)
        wieghtedSides = []
        for w in range(xWeight):
            wieghtedSides.append(0)
        for w in range(yWeight):
            wieghtedSides.append(1)

        # Create new stars on a edge
        while len(self.starsList) < self.stars['Amount']:

            side = random.choice(wieghtedSides)
            starSize = random.randrange(starSizes[0], starSizes[1])
            if side == 0:
                if angleX > 0:
                    starXPos = 0 - starSize
                else:
                    starXPos = self.size().width() + starSize
                starYPos = random.randrange(0, self.size().height())

            else:
                if angleY > 0:
                    starYPos = 0 - starSize
                else:
                    starYPos = self.size().height() + starSize
                starXPos = random.randrange(0, self.size().width())

            self.starsList.append((starXPos, starYPos, starSize))

    def paintEvent(self, event):
        if hasattr(self, 'blockLock'):  # Avoid painting too early
            self.paintBusy = 1

            painter = QPainter(self)
            painter.setPen(QPen(Qt.NoPen))  # Removes pen

            self.paintBackground(event, painter)
            if self.stars:
                self.paintStars(event, painter)
            if self.mainMode == 'Bars' and not self.cutout:
                self.paintBars(event, painter)
            elif not self.cutout:
                self.paintSmooth(event, painter)
            if self.checkFreq or self.checkNotes:
                self.paintFreq(event, painter)
            if self.checkDB:
                self.paintDB(event, painter)
            if self.checkDeadline or self.checkPlotNum or self.checkLatency:
                self.paintStats(event, painter)

            painter.end()
            self.paintBusy = 0

            # Frame Counter to scale timings
            if self.frames < 10000:
                self.frames += 1
            else:
                self.frames = 0

            if self.checkLatency:
                block = self.frameRate // 10
                if block < 1: block = 1
                if self.frames % block == 0:
                    self.latency = round(((time.time() - self.delay) * 1000))

            # Paint's Frame Time Delay Scalar
            delay = self.paintDelay - (time.time() - self.paintTime)
            if delay > 0:
                time.sleep(delay)
            # Auto correcting frame pacer to account for variance in os time
            framePace = time.time() - self.paintTime
            if framePace > (1 / self.frameRate):
                self.paintDelay -= (0.001 / self.frameRate)
            else:
                self.paintDelay += (0.001 / self.frameRate)
            self.paintTime = time.time()

            try:    # Avoid Crash
                if self.blockLock.locked:
                    self.blockLock.release()
            except: pass

    def paintBackground(self, event, painter):
        painter.setBrush(self.backgroundColor)
        background = QRect(0, 0, self.size().width(), self.size().height())
        if not self.cutout:     # Normal background
            painter.drawRect(background)
        else:       # Cutout background
            back = QPolygon(background)
            if self.mainMode == 'Smooth':
                cutout = back.subtracted(self.smoothShape)
                painter.drawPolygon(cutout)
            else:
                # barsPoints = []
                # for rect in self.barsShape:
                #     barsPoints.extend([rect.bottomLeft(), rect.topLeft(), rect.topRight(), rect.bottomRight()])
                # barsPoints.extend([background.bottomRight(), background.topRight(), background.topLeft(), background.bottomLeft()])
                # cutout = QPolygon(barsPoints)

                # This is still the fastest way to draw for bars
                xSize = self.plotWidth
                xPos = (self.gapWidth // 2)
                yPos = 0
                for y in range(len(self.plotValues)):
                    ySizeV = self.plotValues[y]
                    ySize = self.size().height() - ySizeV
                    painter.drawRect(xPos - self.gapWidth, yPos, self.gapWidth, self.size().height())   # Gap bar

                    if self.split:
                        ySplitV = self.plotSplitValues[y]
                        ySize = (self.size().height() // 2) - ySizeV
                        painter.drawRect(xPos, yPos, xSize, ySize)  # Top background
                        ySize = (self.size().height() // 2) - ySplitV
                        painter.drawRect(xPos, self.size().height(), xSize, -ySize)  # bottom background
                    else:
                        painter.drawRect(xPos, yPos, xSize, ySize)

                    xPos += self.wholeWidth

                painter.drawRect(xPos - self.wholeWidth + xSize, yPos,
                                 self.size().width() + self.wholeWidth - xPos, self.size().height())   # Last Gap bar

    def paintStars(self, event, painter):
        # Parse star plot range
        plotRange = self.stars['PlotRange']
        plotMod = self.plotValues[min(plotRange) - 1:max(plotRange)]
        modifier = (sum(plotMod) / len(plotMod)) / self.size().height()

        # Softens the stars and set brush
        if self.stars['Twinkle']:
            twinkle = modifier / 3
        else:
            twinkle = 0.33
        gradient = QRadialGradient()
        gradient.setCoordinateMode(QGradient.ObjectBoundingMode)
        gradient.setStops(((twinkle, self.stars['Color']), (0.5, QColor(0,0,0,0))))
        gradient.setCenter(0.5, 0.5)
        gradient.setFocalPoint(0.5, 0.5)
        painter.setBrush(gradient)

        # Paint Stars
        for star in self.starsList:
            starPosCenter = (int(star[0] - (star[2] / 2)), int(star[1] - (star[2] / 2)))
            painter.drawEllipse(starPosCenter[0], starPosCenter[1], star[2], star[2])

    def paintSmooth(self, event, painter):

        if not self.gradient:
            fillColor = self.mainColor
        else:
            fillColor = QGradient(self.gradient)
        painter.setBrush(fillColor)

        if self.outlineOnly:
            painter.setBrush(QColor(0, 0, 0, 0))

        if self.outlineSize:
            if not self.outlineOnly:
                penColor = self.outlineColor
            else:
                penColor = fillColor

            painter.setPen(QPen(penColor, self.outlineSize))

        # Draw
        # painter.setRenderHints(QPainter.Antialiasing) # Stupid expensive to run
        painter.drawPolygon(self.smoothShape)
        # painter.setRenderHints(QPainter.Antialiasing, False)

    def paintBars(self, event, painter):

        if self.lumen:
            lumReigen = 255 / (self.size().height() * (self.lumen / 100))
            lumList = []

        if not self.gradient:
            fillColor = self.mainColor
        else:
            fillColor = QGradient(self.gradient)

        painter.setBrush(fillColor)

        for rect in self.barsShape:

            if self.lumen:  # Lumen is applied per bar
                lumBright = int(rect.height() * lumReigen)
                if lumBright > 255: lumBright = 255
                if not self.gradient:
                    lumenColor = QColor(fillColor)
                    lumenColor.setAlpha(lumBright)
                else:
                    lumenColor = QGradient(fillColor)
                    for stop in fillColor.stops():
                        pos = stop[0]
                        point = stop[1]
                        point.setAlpha(lumBright)
                        lumenColor.setColorAt(pos, point)
                if self.outlineOnly:
                        lumList.append(lumenColor)

                painter.setBrush(lumenColor)  # Fill of bar color

            if not self.outlineOnly:
                painter.drawRect(rect)

        if self.outlineSize > 0 and len(self.barsOutlineShape) == len(self.barsShape)*4:
            if not self.outlineOnly:
                painter.setBrush(self.outlineColor)
            for i in range(len(self.barsOutlineShape)):
                if self.lumen and self.outlineOnly:
                    if not i % 4:
                        painter.setBrush(lumList[i // 4])
                painter.drawRect(self.barsOutlineShape[i])

    def paintFreq(self, event, painter):
        # Set pen color to contrast main color
        if self.mainColor.value() <= 128:
            textColor = QColor(255, 255, 255)
        else:
            textColor = QColor(0, 0, 0)
        painter.setPen(QPen(textColor))

        font = QFont()
        # Scale text with plot width
        fontSize = self.plotWidth - 1
        if fontSize < 1: fontSize = 1
        font.setPixelSize(fontSize)
        painter.setFont(font)

        ySize = int(fontSize * 1.5)
        xPos = self.gapWidth // 2
        yPos = self.size().height()
        if self.split:
            yPos = self.size().height() // 2

        # Paint frequency plot
        if self.checkFreq:
            for freq in self.freqList[:-1]:
                freq = round(freq)

                digits = 0
                number = freq
                if number == 0:
                    digits = 1
                while number > 0:
                    number //= 10
                    digits += 1

                xTextSize = fontSize
                yTextSize = ySize * digits
                xTextPos = xPos
                yTextPos = yPos - yTextSize

                painter.drawText(xTextPos, yTextPos, xTextSize, yTextSize, Qt.AlignCenter | Qt.TextWrapAnywhere, str(freq))
                xPos += self.wholeWidth

        # Instead of painting freq, give a approximation of notes
        elif self.checkNotes:
            notes = ReVidia.assignNotes(self.freqList[:-1])

            plotWidth = self.plotWidth + 1
            yTextPos = yPos - ySize
            for note in notes:
                painter.drawText(xPos, yTextPos, plotWidth, ySize, Qt.AlignCenter, note)
                xPos += self.wholeWidth

    # Draws a dB bar in right corner
    def paintDB(self, event, painter):
        dbValue = ReVidia.getDB(self.audioPeak.value)

        if dbValue < -1.0:
            painter.setPen(self.textPalette.color(QPalette.WindowText))
        else:
            painter.setPen(QColor(255, 30, 30))
        painter.setFont(QApplication.font())
        xPos = self.size().width() - 35
        yPos = 145

        if dbValue == -float('Inf'):
            painter.drawText(xPos, yPos, '-Inf')
            return

        painter.drawText(xPos, yPos, str(dbValue))

        xPos = self.size().width() - 15
        yPos = yPos - 15
        ySize = (-int(dbValue) - 50) * 2
        if ySize > 0:
            return
        gradient = QLinearGradient(xPos, yPos-35, xPos, yPos-100)    # xStart, yStart, xStop, yStop
        gradient.setColorAt(0, QColor(50, 255, 50))
        gradient.setColorAt(0.5, QColor(255, 200, 0))
        gradient.setColorAt(1, QColor(255, 50, 50))
        painter.setBrush(gradient)

        painter.drawRect(xPos, yPos, 5, ySize)

    # Draw simple Stats
    def paintStats(self, event, painter):
        painter.setPen(self.textPalette.color(QPalette.WindowText))
        painter.setFont(QApplication.font())
        yPos = 40
        if self.checkDeadline:
            if self.latePercent >= 10:    # Keep 3 digits long
                self.latePercent = round(self.latePercent, 1)
            if self.latePercent >= 100:
                self.latePercent = int(self.latePercent)

            text = str(self.latePercent) + '%'
            xPos = (self.size().width() // 2) - 88

            painter.drawText(xPos, yPos, text)
        if self.checkPlotNum:
            text = str(self.plotsAmt) + ' Plots'
            xPos = (self.size().width()//2) - 50

            painter.drawText(xPos, 26, 75, 15, Qt.AlignHCenter, text)

        if self.checkLatency:
            text = str(self.latency) + ' ms'
            xPos = (self.size().width() // 2) + 30

            painter.drawText(xPos, yPos, text)

    def setProfile(self, request):
        import pickle
        import os
        self.width = self.size().width()
        self.height = self.size().height()
        self.gradAttr = 0

        # Order Based Saving/Loading, adding new vars and changing vars names is fine as long as order is kept
        saveList = ['width', 'height', 'frameRate', 'pointsList', 'split', 'curvy', 'interp', 'audioBuffer', 'lumen',
                    'checkRainbow', 'plotWidth', 'gapWidth', 'outlineSize', 'dataCap', 'wholeWidth', 'outlineOnly',
                    'cutout', 'checkFreq', 'checkNotes', 'checkDeadline', 'checkPlotNum', 'checkLatency', 'checkDB',
                    'backgroundColor', 'mainColor', 'outlineColor', 'gradAttr', 'stars', 'mainMode']

        if request == 'save':
            profile, ok = QInputDialog.getText(self, "Save Profile", "Profile Name:")
            if ok and profile:
                # Special care for the gradient as it cannot be pickled
                if self.gradient:
                    grad = self.gradient
                    self.gradAttr = grad.start(), grad.finalStop(), grad.stops(), grad.coordinateMode()

                # Saving
                with open('profiles/' + profile + '.pkl', 'wb') as file:
                    for setting in saveList:
                        pickle.dump(getattr(self, setting), file)
        else:
            profileList = []
            for file in os.listdir('profiles'):
                profileList.append(file.replace('.pkl', ''))
            if not profileList:
                profileList.append('No Profiles Saved')

            if request == 'load':
                profile, ok = QInputDialog.getItem(self, "Load Profile", "Select Profile:", profileList, 0, False)
                if ok and profile and profileList != ['No Profiles Saved']:
                    with open('profiles/' + profile + '.pkl', 'rb') as file:
                        for setting in saveList:
                            try:
                                var = pickle.load(file)
                                setattr(self, setting, var)
                            except EOFError:
                                print("Warning Old Profile: Some settings might not be imported")
                                break

                        if self.gradAttr:
                            self.gradient = QLinearGradient(self.gradAttr[0], self.gradAttr[1])
                            self.gradient.setStops(self.gradAttr[2])
                            self.gradient.setCoordinateMode(self.gradAttr[3])
                        else:
                            self.gradient = 0
                    self.menuWidget.close()
                    self.initUI(True)

            elif request == 'delete':
                profile, ok = QInputDialog.getItem(self, "Delete Profile", "Select Profile:", profileList, 0, False)
                if ok and profile and profileList != ['No Profiles Saved']:
                    os.remove('profiles/' + profile + '.pkl')

    def getDevice(self, firstRun, pulseAudio=False):
        try:  # Get user default pulseaduio device
            result = subprocess.getoutput('pactl info | grep "Default Sink:"')
            self.userSink = result.split('Default Sink: ')[1] + '.monitor'
            result = subprocess.getoutput('pactl info | grep "Default Source:"')
            self.userSource = result.split('Default Source: ')[1]
        except:
            print('Can\'t find Pulseaudio: Outputs disabled')
            self.userSink = 0
            self.userSource = 0

        # Run device getter on separate Process because the other PA won't start if not done
        devQ = mp.Queue()
        D1 = mp.Process(target=ReVidia.deviceNames, args=(devQ, self.userSink))
        D1.start(), D1.join()
        deviceList = devQ.get()

        defaultList = []
        if self.userSink:
            defaultList.append('Default PulseAudio Output Device')
        if self.userSource:
            defaultList.append('Default PulseAudio Input Device')

        itemList = defaultList + deviceList[0]
        if 'Input: revidia_capture - ALSA' in itemList:  # Hide custom ALSA device
            itemList.remove('Input: revidia_capture - ALSA')

        if not pulseAudio:
            device, ok = QInputDialog.getItem(self, "ReVidia", "Select Audio Device:", itemList, 0, False)
        else:   # Auto select PulseAudio
            device = 'Input: revidia_capture - ALSA'
            ok = 1

        if ok and device:
            # Getting ID
            if device == 'Default PulseAudio Output Device':
                ID = self.userSink
            elif device == 'Default PulseAudio Input Device':
                ID = self.userSource
            else:
                ID = deviceList[1][deviceList[0].index(device)]

            if 'Input:' in device:  # If PortAudio Index Num, continue
                self.ID = ID
                self.sampleRate = deviceList[2][deviceList[0].index(device)]
            else:   # If PulseAudio input turn into ALSA input
                import os
                alsaFolder = os.getenv("HOME") + '/.asoundrc'

                # Check/Clean lines for an old "pcm.revidia_capture" device
                self.cleanLines = []
                skip = 0
                with open(alsaFolder, 'r') as alsaConf:
                    allLines = alsaConf.readlines()
                    for line in allLines:
                        if not skip:
                            if not 'pcm.revidia_capture' in line:
                                self.cleanLines.append(line)
                            else:
                                skip = 1
                        else:
                            if '}' in line:
                                skip = 0
                if allLines != self.cleanLines:
                    with open(alsaFolder, 'w') as alsaConf:
                        alsaConf.writelines(self.cleanLines)

                # Create ALSA device to connect to PulseAudio
                with open(alsaFolder, 'a') as alsaConf:
                    alsaConf.write('pcm.revidia_capture {'
                                   '\n    type pulse'
                                   '\n    device ' + ID +
                                   '\n}')
                # Rerun to select the device just created
                self.getDevice(True, True)

            if firstRun: return
            else:
                self.mainQ.put(1), self.mainThread.join()
                self.proQ.put(['kill'])
                self.dataQ.put(['kill'])
                self.startProcesses()

        elif firstRun: sys.exit()

    def getFFTAudDock(self):
        self.fftDock = FFTDock(self)
        self.meta.addDockWidget(Qt.LeftDockWidgetArea, self.fftDock)

        self.refitWindowForDock(self.fftDock)

    def getScaleDock(self):
        self.scaleDock = ScaleDock(self)
        self.meta.addDockWidget(Qt.BottomDockWidgetArea, self.scaleDock)

        self.refitWindowForDock(self.scaleDock)

    def setSplit(self, on):
        if on:
            self.split = 1
        else:
            self.split = 0

        self.dataQ.put(['split', self.split])
        self.proQ.put(['split', self.split])

    def setCurve(self, index):
        self.curvy = index  # Assign Dict value
        if index:
            window = int(self.plotsAmt * index[0])
            if (window % 2) == 0: window += 1
            if window < 5: window = 5
            self.curvyValue = (window, index[1])  # Only used to init process
        else:
            self.curvyValue = 0

        for f in self.curvyDict:
            if f != str(index):
                self.curvyDict[str(f)].setChecked(False)
            else:
                self.curvyDict[str(f)].setChecked(True)

        if hasattr(self, 'proQ'):
            self.proQ.put(['curvy', self.curvyValue])

    def setInterp(self, index):
        self.interp = index

        for f in self.interpDict:
            if int(f) != index:
                self.interpDict[str(f)].setChecked(False)
            else:
                self.interpDict[str(f)].setChecked(True)

        if hasattr(self, 'proQ'):
            self.proQ.put(['interp', self.interp])

    def setAudioBuffer(self, index):
        self.audioBuffer = index

        for f in self.audioBufferDict:
            if int(f) != index:
                self.audioBufferDict[str(f)].setChecked(False)
            else:
                self.audioBufferDict[str(f)].setChecked(True)

        if hasattr(self, 'dataQ'):
            # Update before buffer
            self.updateStack()
            self.dataQ.put(['buffer', self.audioBuffer])
            self.proQ.put(['buffer', self.audioBuffer])

    def setMainColor(self):
        self.mainColor = QColorDialog.getColor(self.mainColor,None,None,QColorDialog.ShowAlphaChannel)

    def setBackgroundColor(self):
        self.backgroundColor = QColorDialog.getColor(self.backgroundColor,None,None,QColorDialog.ShowAlphaChannel)
        self.setTextPalette()

    def setOutlineColor(self):
        self.outlineColor = QColorDialog.getColor(self.outlineColor, None, None, QColorDialog.ShowAlphaChannel)

    def setRainbow(self, on):
        if not hasattr(self, 'rainbowHue'):
            self.rainbowHue = self.mainColor.hue()
            self.checkRainbow = 1
            if self.mainColor.saturation() == 0:
                self.mainColor.setHsv(0,255,self.mainColor.value())
        if on:
            if self.rainbowHue < 359:
                self.rainbowHue += 1
            else:
                self.rainbowHue = 0

            self.mainColor.setHsv(self.rainbowHue,self.mainColor.saturation(),
                                 self.mainColor.value(),self.mainColor.alpha())
        else:
            self.checkRainbow = 0
            del self.rainbowHue

    def setLumen(self, index):
        self.lumen = index

        for f in self.lumenDict:
            if int(f) != index:
                self.lumenDict[str(f)].setChecked(False)
            else:
                self.lumenDict[str(f)].setChecked(True)

    def getStarsDock(self):
        self.starsDock = StarsDock(self)
        self.meta.addDockWidget(Qt.BottomDockWidgetArea, self.starsDock)
        self.refitWindowForDock(self.starsDock)

    def getGradDock(self):
        self.gradDock = GradientDock(self)
        self.meta.addDockWidget(Qt.RightDockWidgetArea, self.gradDock)

        self.refitWindowForDock(self.gradDock)

    def getDimenDock(self):
        self.dimenDock = DimenDock(self)
        self.meta.addDockWidget(Qt.LeftDockWidgetArea, self.dimenDock)

        self.refitWindowForDock(self.dimenDock)

    def setAutoLevel(self, on):
        if on:
            self.dataCap = 0
        else:
            self.dataCap = max(self.proArray[:self.plotsAmt])

    def setOutlineOnly(self, on):
        if on:
            self.outlineOnly = 1
        else:
            self.outlineOnly = 0

    def setCutout(self, on):
        if on:
            self.cutout = 1
        else:
            self.cutout = 0

    def showFreq(self, on):
        if on:
            self.checkFreq = 1
            self.checkNotes = 0
            self.notesCheck.setChecked(False)
        else:
            self.checkFreq = 0

    def showNotes(self, on):
        if on:
            self.checkNotes = 1
            self.checkFreq = 0
            self.freqsCheck.setChecked(False)
        else:
            self.checkNotes = 0

    def showDeadline(self, on):
        if on:
            self.checkDeadline = 1
            self.latePercent = 0
        else:
            self.checkDeadline = 0

    def showPlotNum(self, on):
        if on:
            self.checkPlotNum = 1
        else:
            self.checkPlotNum = 0

    def showLatency(self, on):
        if on:
            self.checkLatency = 1
            self.latency = 0
        else:
            self.checkLatency = 0

    def showDB(self, on):
        if on:
            self.checkDB = 1
        else:
            self.checkDB = 0

    def setMainMode(self):
        if self.mainModeCheck.text() == 'Bars':
            self.mainMode = 'Smooth'
        else:
            self.mainMode = 'Bars'

        self.mainModeCheck.setText(self.mainMode)

    def setFrameRate(self, value):
        self.repaint()
        self.frameRate = value
        self.paintDelay = (1 / self.frameRate)

        if hasattr(self, 'proQ'):
            self.proQ.put(['frameRate', self.frameRate])

    # When a dock is added or removed the main window size will remain the same
    def refitWindowForDock(self, dock):
        self.dockMod = dock
        # Semi-fix for background color when docked
        color = self.palette().color(self.backgroundRole())
        # Hex colors are a no go so...
        colorStr = 'rgb(' + str(color.red()) +','+ str(color.blue()) +','+ str(color.green()) + ')'
        dock.setStyleSheet(".QWidget {background-color: " + colorStr + "}")
        dock.setAutoFillBackground(True)

    # Adds keyboard inputs
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.meta.close()
        # Toggle menu showing with tab
        if event.key() == Qt.Key_Tab:
            if self.menuWidget.isVisible():
                self.menuWidget.hide()
            else:
                self.menuWidget.show()
        # Toggle frameless mode with shift
        if event.key() == Qt.Key_Shift:
            if not hasattr(self, 'framelessToggle'):
                self.framelessToggle = 0

            if self.framelessToggle == 0:
                self.framelessToggle = 1

                self.meta.setWindowFlags(Qt.FramelessWindowHint)
                self.meta.show()
                return
            
            if self.framelessToggle == 1:
                self.framelessToggle = 0

                self.meta.setWindowFlags(self.windowFlags() & ~Qt.FramelessWindowHint)
                self.meta.show()
                return

    def mousePressEvent(self, event):
        if event.button() == 2:  # Right click
            self.mouseGrab = [event.x(), event.y()]
            self.setCursor(Qt.SizeAllCursor)

    def mouseMoveEvent(self, event):
        if hasattr(self, 'mouseGrab'):
            xPos = event.globalX() - self.mouseGrab[0]
            yPos = event.globalY() - self.mouseGrab[1]
            self.meta.move(xPos, yPos)

    def mouseReleaseEvent(self, event):
        if hasattr(self, 'mouseGrab'):
            del self.mouseGrab
            self.unsetCursor()

    # Allows to adjust data cap by scrolling on window
    def wheelEvent(self, event):
        mouseDir = event.angleDelta().y()

        if not self.dataCap:
            self.autoLevel.trigger()

        if mouseDir < 0:
            if self.dataCap < 10**10:
                self.dataCap *= 1.5
            else:
                self.dataCap = 10**10
        elif mouseDir > 0:
            if self.dataCap > 1:
                self.dataCap /= 1.5
            else:
                self.dataCap = 1

        if hasattr(self, 'dimenDock'):
            self.dimenDock.heightText.setText('Height \n' + str(int(self.dataCap**(1/2))))

    def resizeEvent(self, event):
        self.updateStack()

        if hasattr(self, 'dockMod'):
            del self.dockMod
            sizeDiff = event.oldSize() - event.size()
            self.meta.resize(self.meta.size() + sizeDiff)

    # Makes sure the processes are not running in the background after closing
    def closeEvent(self, event):
        try:
            self.mainQ.put(1)   # End main thread
            self.P1.terminate()   # Kill Processes
            self.T1.terminate()
            if hasattr(self, 'cleanLines'):  # Clean up ~/.asoundrc
                import os
                alsaFolder = os.getenv("HOME") + '/.asoundrc'
                with open(alsaFolder, 'w') as alsaConf:
                    alsaConf.writelines(self.cleanLines)
        except RuntimeError:
            print('Some processes won\'t close properly, closing anyway.')


class DimenDock(QDockWidget):
    def __init__(self, main):
        super(DimenDock, self).__init__()
        self.main = main
        self.setWindowTitle('Dimensions')

        self.intiUI()

    def intiUI(self):
        UI = QWidget(self)
        layout = QGridLayout(UI)

        self.plotWidthText = QLabel(self)
        self.plotWidthText.setText('Plot Width ' + str(self.main.plotWidth))
        plotWidthSlider = QSlider(Qt.Horizontal, self)
        plotWidthSlider.setMinimum(1)
        plotWidthSlider.setValue(self.main.plotWidth)
        plotWidthSlider.valueChanged.connect(self.setPlotSize)

        self.gapWidthText = QLabel(self)
        self.gapWidthText.setText('Gap Width ' + str(self.main.gapWidth))
        gapWidthSlider = QSlider(Qt.Horizontal, self)
        gapWidthSlider.setValue(self.main.gapWidth)
        gapWidthSlider.valueChanged.connect(self.setGapSize)

        self.outlineWidthText = QLabel(self)
        self.outlineWidthText.setText('Out Width ' + str(self.main.outlineSize))
        self.outlineWidthSlider = QSlider(Qt.Horizontal, self)
        self.outlineWidthSlider.setMaximum(50)
        self.outlineWidthSlider.setValue(self.main.outlineSize)
        self.outlineWidthSlider.valueChanged.connect(self.setOutlineSize)

        self.heightText = QLabel(self)
        self.heightText.setText('Height \n' + str(int(self.main.dataCap ** (1 / 2))))
        self.heightText.setGeometry(30, 65, 50, 40)
        self.heightSlider = QSlider(Qt.Vertical, self)
        self.heightSlider.setMinimum(-100)
        self.heightSlider.setMaximum(100)
        self.heightSlider.setMinimumSize(0, 150)
        self.heightSlider.setValue(0)
        self.heightSlider.valueChanged.connect(self.setDataCap)

        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(5)

        layout.addWidget(self.heightText, 0, 0, 2, 1, Qt.AlignTop)
        layout.addWidget(self.plotWidthText, 0, 1, Qt.AlignCenter)
        layout.addWidget(self.gapWidthText, 2, 1, Qt.AlignCenter)
        layout.addWidget(self.outlineWidthText, 4, 1, Qt.AlignCenter)

        layout.addWidget(self.heightSlider, 2, 0, 4, 0)
        layout.addWidget(plotWidthSlider, 1, 1)
        layout.addWidget(gapWidthSlider, 3, 1)
        layout.addWidget(self.outlineWidthSlider, 5, 1)
        layout.setRowStretch(6, 1)

        self.setWidget(UI)

    def setPlotSize(self, value):
        self.main.plotWidth = value
        self.main.wholeWidth = self.main.plotWidth + self.main.gapWidth
        self.main.updateStack()

        self.plotWidthText.setText('Plot Width ' + str(self.main.plotWidth))

    def setGapSize(self, value):
        self.main.gapWidth = value
        self.main.wholeWidth = self.main.plotWidth + self.main.gapWidth
        self.main.updateStack()

        self.gapWidthText.setText('Gap Width ' + str(self.main.gapWidth))

    def setOutlineSize(self, value):
        self.main.outlineSize = value

        self.outlineWidthText.setText('Out Width ' + str(self.main.outlineSize))

    def setDataCap(self):
        if not self.main.dataCap:
            self.main.autoLevel.trigger()

        value = self.heightSlider.value()
        if value > 0:
            value = 1 + value / (self.main.frameRate * 10)
            if self.main.dataCap > 1:
                self.main.dataCap /= value
            else:
                self.main.dataCap = 1

        elif value < 0:
            value = 1 + -value / (self.main.frameRate * 10)
            if self.main.dataCap < 10**10:
                self.main.dataCap *= value
            else:
                self.main.dataCap = 10**10

        self.heightText.setText('Height \n' + str(int(self.main.dataCap**(1/2))))

    def closeEvent(self, event):
        ReVidiaMain.refitWindowForDock(self.main, self)


class FFTDock(QDockWidget):
    def __init__(self, main):
        super(FFTDock, self).__init__()
        self.setWindowTitle('Reverse FFT')
        self.main = main

        self.intiUI()

    def intiUI(self):
        UI = QWidget(self)
        layout = QVBoxLayout(UI)

        self.record = QPushButton('Record', self)
        self.record.setFixedSize(100, 50)
        self.record.setCheckable(True)
        self.record.clicked.connect(self.setRecord)

        self.play = QPushButton('Play', self)
        self.play.setFixedSize(100, 50)
        self.play.setCheckable(True)
        self.play.clicked.connect(self.setPlay)

        layout.addWidget(self.record)
        layout.addWidget(self.play)
        layout.addStretch(1)

        self.setWidget(UI)

    def setRecord(self, on):
        if self.play.isChecked():
            self.play.click()

        if on:
            self.record.setText('Recording')
            self.main.reverseFFT = 1
        else:
            self.record.setText('Stopped')
            self.main.reverseFFT = 0

    def setPlay(self, on):
        from PyQt5.QtMultimedia import QSound
        if self.main.reverseFFT:
            self.record.setText('Stopped')
            self.record.setChecked(False)
            self.main.reverseFFT = 0

        if on:
            self.play.setText('Playing')
            self.player = QSound('reverseFFT.wav')
            self.player.play()
        else:
            self.play.setText('Stopped')
            self.player.stop()
            del self.player

    def closeEvent(self, event):
        # Cleanup
        self.main.reverseFFT = 0
        if hasattr(self, 'player'):
            self.player.stop()
            del self.player

        ReVidiaMain.refitWindowForDock(self.main, self)


class ScaleDock(QDockWidget):
    def __init__(self, main):
        super(ScaleDock, self).__init__()
        self.setWindowTitle('Scale')
        self.setMinimumHeight(100)

        self.main = main
        self.child = ScaleWidget(self.main, self)

        self.intiUI()

    def intiUI(self):
        UI = QWidget(self)
        layout = QVBoxLayout(UI)
        menuBar = QHBoxLayout()

        self.scaleModeCheck = QPushButton('Bezier')
        self.scaleModeCheck.pressed.connect(self.child.setScaleMode)


        self.startPointSpinBox = QSpinBox()
        self.startPointSpinBox.setRange(0, int(self.main.sampleRate // 2))
        self.startPointSpinBox.setSuffix(' HZ')
        self.startPointSpinBox.valueChanged.connect(self.child.setStartPoint)
        self.startPointSpinBox.setValue(self.child.startPoint)
        self.startPointSpinBox.setKeyboardTracking(False)
        self.startPointSpinBox.setFocusPolicy(Qt.ClickFocus)

        self.midPointSpinBox = QSpinBox()
        self.midPointSpinBox.setRange(0, int(self.main.sampleRate // 2))
        self.midPointSpinBox.setSuffix(' HZ')
        self.midPointSpinBox.valueChanged.connect(self.child.setMidPoint)
        self.midPointSpinBox.setValue(self.child.midPoint)
        self.midPointSpinBox.setKeyboardTracking(False)
        self.midPointSpinBox.setFocusPolicy(Qt.ClickFocus)

        self.endPointSpinBox = QSpinBox()
        self.endPointSpinBox.setRange(0, int(self.main.sampleRate // 2))
        self.endPointSpinBox.setSuffix(' HZ')
        self.endPointSpinBox.valueChanged.connect(self.child.setEndPoint)
        self.endPointSpinBox.setValue(self.child.endPoint)
        self.endPointSpinBox.setKeyboardTracking(False)
        self.endPointSpinBox.setFocusPolicy(Qt.ClickFocus)

        menuBar.addWidget(self.scaleModeCheck)
        menuBar.addWidget(self.startPointSpinBox)
        menuBar.addWidget(self.midPointSpinBox)
        menuBar.addWidget(self.endPointSpinBox)
        menuBar.addStretch(10)

        layout.addLayout(menuBar, 1)
        layout.addWidget(self.child, 10)

        self.setWidget(UI)

    def closeEvent(self, event):
        ReVidiaMain.refitWindowForDock(self.main, self)


class ScaleWidget(QWidget):
    def __init__(self, main, parent):
        super(ScaleWidget, self).__init__()
        self.setMinimumSize(100, 100)
        self.main = main
        self.parent = parent

        self.border = 10
        self.pRad = 5  # Point radius
        self.holdStartPoint = 0
        self.holdMidPoint = 0
        self.holdEndPoint = 0
        self.scaleMode = 0

        self.startPoint = self.main.pointsList[0]
        self.startCurve = self.main.pointsList[1]
        self.midPoint = self.main.pointsList[2]
        self.midPointPos = self.main.pointsList[3]
        self.endCurve = self.main.pointsList[4]
        self.endPoint = self.main.pointsList[5]

    def setScaleMode(self):
        if self.parent.scaleModeCheck.text() == 'Real':
            self.scaleMode = 0
            self.parent.scaleModeCheck.setText('Bezier')
        else:
            self.scaleMode = 1
            self.parent.scaleModeCheck.setText('Real')

        self.resizeEvent(0)
        self.update()

    def setStartPoint(self, value):
        self.startPoint = value
        self.updatePoints()

    def setMidPoint(self, value):
        self.midPoint = value
        self.updatePoints()

    def setEndPoint(self, value):
        self.endPoint = value
        self.updatePoints()

    def updatePoints(self):
        self.main.pointsList = [self.startPoint, self.startCurve, self.midPoint,
                                self.midPointPos, self.endCurve, self.endPoint]
        self.main.updateStack()
        self.update()

    def resizeEvent(self, event):
        xSize = self.size().width() - self.border * 2
        ySize = self.size().height() - self.border * 2
        self.boundry = QRect(self.border, self.border, xSize, ySize)

        if self.scaleMode == 1:
            steps = (self.main.sampleRate / 2) / (ySize-1)
            self.freqScale = ReVidia.realScale(0, (self.main.sampleRate // 2), steps)
        else:
            self.freqScale = ReVidia.quadBezier(0, (self.main.sampleRate // 2), 0, (ySize-1), True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(self.main.backgroundColor.rgb()))
        painter.drawRect(0, 0, self.size().width(), self.size().height())

        painter.setRenderHints(QPainter.Antialiasing)
        linePen = QPen()
        linePen.setColor(QColor(self.main.mainColor.rgb()))
        linePen.setWidth(3)
        linePen.setCapStyle(Qt.RoundCap)
        painter.setPen(linePen)

        painter.drawRect(self.boundry)

        widthScale = self.boundry.width() / self.main.plotsAmt
        xPos1 = self.border - widthScale
        xPos2 = self.border

        midPoint = int(round(self.main.plotsAmt * self.midPointPos))
        for i in range(len(self.main.freqList)):
            freq = self.main.freqList[i]

            for n in range(self.boundry.height()):
                if freq - self.freqScale[n] <= 0:
                    index = self.freqScale.index(min(self.freqScale[n], self.freqScale[n - 1], key=lambda x: abs(x - freq)))
                    yPos2 = self.size().height() - index - self.border
                    break
            if i > 0:
                xPos1 += widthScale
                xPos2 += widthScale
                painter.drawLine(int(round(xPos1)), yPos1, int(round(xPos2)), yPos2)
            else:
                startYPos = yPos2
            if i == midPoint:
                midXPos = xPos2
                midYPos = yPos2

            yPos1 = yPos2

        xPos = self.border
        yPos = startYPos
        self.startCenterPoint = QPoint(xPos, yPos)
        painter.drawEllipse(self.startCenterPoint, self.pRad, self.pRad)

        xTextPos = self.startCenterPoint.x() + self.pRad + 1
        yTextPos = self.startCenterPoint.y() - self.pRad
        painter.drawText(xTextPos, yTextPos, str(round(self.startPoint)) + ' HZ')

        xPos = int(midXPos)
        yPos = midYPos
        self.midCenterPoint = QPoint(xPos, yPos)
        painter.drawEllipse(self.midCenterPoint, self.pRad, self.pRad)

        xTextPos = self.midCenterPoint.x() - 30
        yTextPos = self.midCenterPoint.y() - (self.pRad * 2)
        painter.drawText(xTextPos, yTextPos, str(round(self.midPoint)) + ' HZ')

        xPos = (self.size().width() - self.border)
        yPos = yPos2
        self.endCenterPoint = QPoint(xPos, yPos)

        painter.drawEllipse(self.endCenterPoint, self.pRad, self.pRad)

        digits = 0
        number = self.endPoint
        if number == 0: digits = 1
        while number > 0:
            number //= 10
            digits += 1
        xTextPos = self.endCenterPoint.x() - (digits * 9) - (self.pRad * 4)
        yTextPos = self.endCenterPoint.y() - self.pRad

        painter.drawText(xTextPos, yTextPos, str(round(self.endPoint)) + ' HZ')

        painter.end()

    def mousePressEvent(self, event):
        self.holding = 1
        field = self.pRad * 2
        if (event.x() < self.startCenterPoint.x() + field) and (event.x() > self.startCenterPoint.x() - field) \
                and (event.y() < self.startCenterPoint.y() + field) and (event.y() > self.startCenterPoint.y() - field):
            self.holdStartPoint = 1

        if (event.x() < self.midCenterPoint.x() + field) and (event.x() > self.midCenterPoint.x() - field) \
                and (event.y() < self.midCenterPoint.y() + field) and (event.y() > self.midCenterPoint.y() - field):
            self.holdMidPoint = 1

        if (event.x() < self.endCenterPoint.x() + field) and (event.x() > self.endCenterPoint.x() - field) \
                and (event.y() < self.endCenterPoint.y() + field) and (event.y() > self.endCenterPoint.y() - field):
            self.holdEndPoint = 1

    def mouseMoveEvent(self, event):
        if self.holding:
            if self.holdStartPoint:
                index = self.size().height() - event.y() - self.border
                if index > self.boundry.height()-1: index = self.boundry.height()-1
                if index < 0: index = 0

                self.startPoint = int(self.freqScale[index])
                self.parent.startPointSpinBox.setValue(self.startPoint)

            if self.holdMidPoint:
                midX = (event.x() - self.border) / self.boundry.width()
                if midX > 0.9: midX = 0.9
                if midX < 0.1: midX = 0.1

                self.midPointPos = midX

                index = self.size().height() - event.y() - self.border
                if index > self.boundry.height()-1: index = self.boundry.height()-1
                if index < 0: index = 0

                self.midPoint = int(self.freqScale[index])
                self.parent.midPointSpinBox.setValue(self.midPoint)

            if self.holdEndPoint:
                index = self.size().height() - event.y() - self.border
                if index > self.boundry.height()-1: index = self.boundry.height()-1
                if index < 0: index = 0

                self.endPoint = int(self.freqScale[index])
                self.parent.endPointSpinBox.setValue(self.endPoint)

            self.updatePoints()
            self.update()

    def wheelEvent(self, event):
        mouseDir = event.angleDelta().y()
        if self.holdStartPoint:
            if mouseDir > 0:
                if self.startCurve < 3:
                    self.startCurve += 0.1
            elif mouseDir < 0:
                if self.startCurve > -2:
                    self.startCurve -= 0.1
        if self.holdMidPoint:
            if mouseDir > 0:
                if self.endCurve < 3:
                    self.endCurve += 0.1
            elif mouseDir < 0:
                if self.endCurve > -2:
                    self.endCurve -= 0.1

        self.updatePoints()
        self.update()

    def mouseReleaseEvent(self, event):
        self.holding = 0
        self.holdStartPoint = 0
        self.holdMidPoint = 0
        self.holdEndPoint = 0


class StarsDock(QDockWidget):
    def __init__(self, main):
        super(StarsDock, self).__init__()
        self.main = main
        self.setWindowTitle('Stars')

        if not self.main.stars:
            self.starsStats = {'Amount': 100, 'Angle': 300, 'Color': QColor(255, 255, 255), 'MinSpeed': 25,
                               'ModSpeed': 100, 'SizeRange': (1, 5), 'PlotRange': (1, 10), 'Twinkle': 1}
        else:
            self.starsStats = self.main.stars
        self.main.stars = self.starsStats

        self.intiUI()

    def intiUI(self):
        UI = QWidget(self)
        layout = QGridLayout(UI)

        self.toggleStars = QPushButton('Enabled')
        self.toggleStars.setCheckable(True)
        self.toggleStars.clicked.connect(self.setToggleStars)

        starsAmountSpin = QSpinBox()
        starsAmountSpin.setRange(1, 9999)
        starsAmountSpin.setSuffix(' Stars')
        starsAmountSpin.valueChanged.connect(self.setStarsAmount)
        starsAmountSpin.setKeyboardTracking(False)
        starsAmountSpin.setFocusPolicy(Qt.ClickFocus)
        starsAmountSpin.setValue(self.starsStats['Amount'])

        starsAmount = QVBoxLayout()
        starsAmount.addWidget(QLabel('Stars Drawn'), 0, Qt.AlignCenter)
        starsAmount.addWidget(starsAmountSpin, 1)

        self.starAngleText = QLabel(self)
        self.starAngleText.setText('Angle ' + str(self.starsStats['Angle']) + '°')
        starsAngleDial = QDial()
        starsAngleDial.setMaximum(359)
        starsAngleDial.setValue(self.starsStats['Angle'])
        starsAngleDial.valueChanged.connect(self.setStarsAngle)

        starsColor = QPushButton("Color")
        starsColor.clicked.connect(self.setStarsColor)

        starMinSpeedSpin = QSpinBox()
        starMinSpeedSpin.setRange(0, 9999)
        starMinSpeedSpin.setSuffix(' PixelsPerSec')
        starMinSpeedSpin.valueChanged.connect(self.setStarMinSpeed)
        starMinSpeedSpin.setKeyboardTracking(False)
        starMinSpeedSpin.setFocusPolicy(Qt.ClickFocus)
        starMinSpeedSpin.setValue(self.starsStats['MinSpeed'])
        starMinSpeed = QVBoxLayout()
        starMinSpeed.addWidget(QLabel('Normal Speed'), 0, Qt.AlignCenter)
        starMinSpeed.addWidget(starMinSpeedSpin, 1)

        starModSpeedSpin = QSpinBox()
        starModSpeedSpin.setRange(0, 9999)
        starModSpeedSpin.setSuffix(' PixelsPerSec')
        starModSpeedSpin.valueChanged.connect(self.setStarModSpeed)
        starModSpeedSpin.setKeyboardTracking(False)
        starModSpeedSpin.setFocusPolicy(Qt.ClickFocus)
        starModSpeedSpin.setValue(self.starsStats['ModSpeed'])

        starModSpeed = QVBoxLayout()
        starModSpeed.addWidget(QLabel('Modified Speed'), 0, Qt.AlignCenter)
        starModSpeed.addWidget(starModSpeedSpin, 1)

        self.twinkleToggle = QPushButton('Twinkle On')
        if not self.starsStats['Twinkle']:
            self.twinkleToggle.setText('Twinkle Off')
        self.twinkleToggle.setCheckable(True)
        self.twinkleToggle.clicked.connect(self.setTwinkle)
        self.twinkleToggle.setChecked(self.starsStats['Twinkle'])

        starSizeA = QSpinBox()
        starSizeA.setRange(1, 999)
        starSizeA.setSuffix(' Pixels')
        starSizeA.valueChanged.connect(self.setStarSizeA)
        starSizeA.setKeyboardTracking(False)
        starSizeA.setFocusPolicy(Qt.ClickFocus)
        starSizeA.setValue(self.starsStats['SizeRange'][0])

        starSizeB = QSpinBox()
        starSizeB.setRange(1, 999)
        starSizeB.setSuffix(' Pixels')
        starSizeB.valueChanged.connect(self.setStarSizeB)
        starSizeB.setKeyboardTracking(False)
        starSizeB.setFocusPolicy(Qt.ClickFocus)
        starSizeB.setValue(self.starsStats['SizeRange'][1])

        starSizeRangeSpins = QSplitter()
        starSizeRangeSpins.addWidget(starSizeA)
        starSizeRangeSpins.addWidget(starSizeB)
        starSizeRange = QVBoxLayout()
        starSizeRange.addWidget(QLabel('Star Size'), 0, Qt.AlignCenter)
        starSizeRange.addWidget(starSizeRangeSpins, 1)

        starModifierA = QSpinBox()
        starModifierA.setRange(1, self.main.plotsAmt)
        starModifierA.setPrefix('Plot ')
        starModifierA.valueChanged.connect(self.setStarModifierA)
        starModifierA.setKeyboardTracking(False)
        starModifierA.setFocusPolicy(Qt.ClickFocus)
        starModifierA.setValue(self.starsStats['PlotRange'][0])

        starModifierB = QSpinBox()
        starModifierB.setRange(1, self.main.plotsAmt)
        starModifierB.setPrefix('Plot ')
        starModifierB.valueChanged.connect(self.setStarModifierB)
        starModifierB.setKeyboardTracking(False)
        starModifierB.setFocusPolicy(Qt.ClickFocus)
        starModifierB.setValue(self.starsStats['PlotRange'][1])

        plotModRangeSpins = QSplitter()
        plotModRangeSpins.addWidget(starModifierA)
        plotModRangeSpins.addWidget(starModifierB)
        plotModRange = QVBoxLayout()
        plotModRange.addWidget(QLabel('Modifier Range'), 0, Qt.AlignCenter)
        plotModRange.addWidget(plotModRangeSpins, 1)

        layout.addWidget(self.toggleStars, 0, 0)
        layout.addLayout(starsAmount, 0, 1)
        layout.addWidget(starsAngleDial, 0, 3, 2, 2)

        layout.addWidget(starsColor, 1, 0)
        layout.addLayout(starMinSpeed, 1, 1)
        layout.addLayout(starModSpeed, 1, 2)
        layout.addWidget(self.starAngleText, 1, 3, 2, 2, Qt.AlignCenter)

        layout.addWidget(self.twinkleToggle, 2, 0)
        layout.addLayout(starSizeRange, 2, 1)
        layout.addLayout(plotModRange, 2, 2)
        layout.setRowStretch(3, 10)

        self.setWidget(UI)

    def setToggleStars(self, mode):
        if mode == 0:
            self.toggleStars.setText('Enabled')
            self.main.stars = self.starsStats
        else:
            self.toggleStars.setText('Disabled')
            self.main.stars = 0

    def setStarsAmount(self, value):
        self.starsStats['Amount'] = value
        self.main.stars = self.starsStats

    def setStarsAngle(self, value):
        self.starsStats['Angle'] = value
        self.starAngleText.setText('Angle ' + str(value) + '°')

        self.main.stars = self.starsStats

    def setStarsColor(self):
        color = QColorDialog.getColor(self.starsStats['Color'],None,None,QColorDialog.ShowAlphaChannel)
        self.starsStats['Color'] = color
        self.main.stars = self.starsStats

    def setStarMinSpeed(self, value):
        self.starsStats['MinSpeed'] = value
        self.main.stars = self.starsStats

    def setStarModSpeed(self, value):
        self.starsStats['ModSpeed'] = value
        self.main.stars = self.starsStats

    def setTwinkle(self, on):
        if on:
            self.twinkleToggle.setText('Twinkle On')
            self.starsStats['Twinkle'] = 1
        else:
            self.twinkleToggle.setText('Twinkle Off')
            self.starsStats['Twinkle'] = 0

        self.main.stars = self.starsStats

    def setStarSizeA(self, value):
        B = self.starsStats['SizeRange'][1]
        self.starsStats['SizeRange'] = (value, B)
        self.main.stars = self.starsStats

    def setStarSizeB(self, value):
        A = self.starsStats['SizeRange'][0]
        self.starsStats['SizeRange'] = (A, value)
        self.main.stars = self.starsStats

    def setStarModifierA(self, value):
        B = self.starsStats['PlotRange'][1]
        self.starsStats['PlotRange'] = (value, B)
        self.main.stars = self.starsStats

    def setStarModifierB(self, value):
        A = self.starsStats['PlotRange'][0]
        self.starsStats['PlotRange'] = (A, value)
        self.main.stars = self.starsStats

    def closeEvent(self, event):
        ReVidiaMain.refitWindowForDock(self.main, self)


class GradientDock(QDockWidget):
    def __init__(self, main):
        super(GradientDock, self).__init__()
        self.setWindowTitle('Gradient')
        self.setMinimumWidth(100)

        self.main = main
        self.child = GradientWidget(self.main, self)

        self.intiUI()

        if self.main.gradient:
            self.child.colorPoints = self.main.gradient.stops()
            if self.main.gradient.start().y() > 0:
                self.child.dirMode = 0
                self.dirModeCheck.setText('Vertical')
            else:
                self.child.dirMode = 1
                self.dirModeCheck.setText('Horizontal')

            if self.main.gradient.coordinateMode() == 1:
                self.child.fillMode = 0
                self.fillModeCheck.setText('Whole')
            else:
                self.child.fillMode = 1
                self.fillModeCheck.setText('Per-Obj')

        else:
            self.child.colorPoints = []
            self.child.fillMode = 0
            self.child.dirMode = 0

        self.child.setGradient()

    def intiUI(self):
        UI = QWidget(self)
        self.layout = QBoxLayout(QBoxLayout.LeftToRight, UI)
        self.menuBar = QBoxLayout(QBoxLayout.TopToBottom)

        self.dirModeCheck = QPushButton('Vertical')
        self.dirModeCheck.pressed.connect(self.child.setDirMode)

        self.fillModeCheck = QPushButton('Whole')
        self.fillModeCheck.pressed.connect(self.child.setFillMode)

        clear = QPushButton('Clear')
        clear.pressed.connect(self.child.runClear)

        self.enabled = QPushButton('Enabled')
        self.enabled.pressed.connect(self.child.setEnabled)

        self.menuBar.addWidget(self.dirModeCheck)
        self.menuBar.addWidget(self.fillModeCheck)
        self.menuBar.addWidget(clear)
        self.menuBar.addWidget(self.enabled)
        self.menuBar.addStretch(10)

        self.layout.addLayout(self.menuBar, 1)
        self.layout.addWidget(self.child, 10)

        self.setWidget(UI)

    def closeEvent(self, event):
        ReVidiaMain.refitWindowForDock(self.main, self)


class GradientWidget(QWidget):
    def __init__(self, main, parent):
        super(GradientWidget, self).__init__()
        self.setMinimumWidth(100)
        self.main = main
        self.parent = parent

        self.disabled = 0

    def setDirMode(self):
        if self.parent.dirModeCheck.text() == 'Horizontal':
            self.dirMode = 0
            self.parent.dirModeCheck.setText('Vertical')
        else:
            self.dirMode = 1
            self.parent.dirModeCheck.setText('Horizontal')

        self.setGradient()

    def setFillMode(self):
        if self.parent.fillModeCheck.text() == 'Per-Obj':
            self.fillMode = 0
            self.parent.fillModeCheck.setText('Whole')
        else:
            self.fillMode = 1
            self.parent.fillModeCheck.setText('Per-Obj')

        self.setGradient()

    def runClear(self):
        self.colorPoints = []
        self.setGradient()

    def setEnabled(self):
        if self.parent.enabled.text() == 'Disabled':
            self.parent.enabled.setText('Enabled')
            self.disabled = 0
            self.setGradient()
        else:
            self.parent.enabled.setText('Disabled')
            self.main.gradient = 0
            self.disabled = 1

    def setGradient(self):
        gradient = QLinearGradient()
        if self.fillMode == 0:
            gradient.setCoordinateMode(QGradient.StretchToDeviceMode)
        else:
            gradient.setCoordinateMode(QGradient.ObjectBoundingMode)

        gradient.setStops(self.colorPoints)

        if self.dirMode == 0:
            start = 0, 1
            end = 0, 0
        else:
            start = 0, 0
            end = 1, 0
        gradient.setStart(start[0], start[1])
        gradient.setFinalStop(end[0], end[1])

        if not self.disabled:
            self.main.gradient = gradient
            self.gradient = gradient

        self.update()

    def resizeEvent(self, event):
        self.GW = self.size().width()   # Graphics Width
        self.GH = self.size().height()     # Graphics Height
        if self.GW > self.GH:
            self.parent.layout.setDirection(QBoxLayout.TopToBottom)
            self.parent.menuBar.setDirection(QBoxLayout.LeftToRight)
        else:
            self.parent.layout.setDirection(QBoxLayout.LeftToRight)
            self.parent.menuBar.setDirection(QBoxLayout.TopToBottom)

    def paintEvent(self, event):
        painter = QPainter(self)
        yPos = 0

        gradient = QLinearGradient(self.gradient)
        gradient.setCoordinateMode(QGradient.ObjectBoundingMode)
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawRect(0, yPos, self.GW, self.GH + yPos)

        painter.setPen(QPen(QColor(0, 0, 0), 3, Qt.DotLine))

        for point in self.colorPoints:
            if self.dirMode == 0:
                pos = int((self.GH - (point[0] * self.GH)) + yPos)
                painter.drawLine(0, pos, self.GW, pos)
            else:
                pos = int(point[0] * self.GW)
                painter.drawLine(pos, yPos, pos, self.GH)

    def mouseDoubleClickEvent(self, event):
        if event.button() == 1:
            if self.dirMode == 0:
                point = 1 - ((event.y()) / self.GH)
            else:
                point = event.x() / self.GW

            color = QColorDialog.getColor(QColor(255,255,255),None,None,QColorDialog.ShowAlphaChannel)

            self.colorPoints.append((point, color))
            self.setGradient()

    def mousePressEvent(self, event):
        if event.button() == 2:
            if self.dirMode == 0:
                posF = 1 - ((event.y()) / self.GH)
            else:
                posF = event.x() / self.GW

            for point in self.colorPoints:
                if (point[0] - 0.01 < posF) and (point[0] + 0.01 > posF):
                    self.colorPoints.remove(point)

            self.setGradient()


# Starts program
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ReVidiaMain()
    sys.exit(app.exec())
