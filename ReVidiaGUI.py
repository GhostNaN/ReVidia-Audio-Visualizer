#!venv/bin/python
# -*- coding: utf-8 -*-

import ReVidia
import sys
import time
import subprocess
import threading as th
import multiprocessing as mp
from PyQt5.QtCore import Qt, QPoint, QRect
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


# Create the self object and main window
class ReVidiaMain(QMainWindow):
    def __init__(self):
        super(ReVidiaMain, self).__init__()

        try:    # Get user default pulseaduio device
            result = subprocess.getoutput('pactl info | grep "Default Sink:"')
            self.userSink = result.split('Default Sink: ')[1]
            result = subprocess.getoutput('pactl info | grep "Default Source:"')
            self.userSource = result.split('Default Source: ')[1]
        except:
            print('Can\'t find Pulseaudio: Outputs disabled')
            self.userSink = 0
            self.userSource = 0

        # Sets up window to be in the middle and to be half screen height
        screen = QApplication.desktop().screenNumber(
            QApplication.desktop().cursor().pos())
        screenSize = QApplication.desktop().screenGeometry(screen)
        self.width = screenSize.width() // 2
        self.height = screenSize.height() // 2
        self.left = screenSize.center().x() - self.width // 2
        self.top = screenSize.center().y() - self.height // 2

        # Default variables
        self.title = 'ReVidia'
        self.frameRate = 150
        # [startPoint, startCurve, midPoint, midPointPos, endCurve, endPoint]
        self.pointsList = [0, 1, 1000, 0.66, 1, 12000]
        self.split = 0
        self.curvy = 0
        self.interp = 2
        self.audioBuffer = 4096
        self.backgroundColor = QColor(50, 50, 50, 255)  # R, G, B, Alpha 0-255
        self.barColor = QColor(255, 255, 255, 255)
        self.outlineColor = QColor(0, 0, 0)
        self.gradient = 0
        self.lumen = 0
        self.checkRainbow = 0
        self.barWidth = 14
        self.gapWidth = 6
        self.outlineSize = 0
        self.barHeight = 0.001
        self.wholeWidth = self.barWidth + self.gapWidth
        self.outline = 0
        self.cutout = 0
        self.checkFreq = 0
        self.checkNotes = 0
        self.checkDeadline = 0
        self.checkBarNum = 0
        self.checkLatency = 0
        self.checkDB = 0

        self.initUI()

    # Setup main window
    def initUI(self, reload=False):
        self.setWindowIcon(QIcon('docs/REV.png'))
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.setMinimumSize(200, 150)
        self.setAttribute(Qt.WA_TranslucentBackground, True)    # Initial background is transparent
        self.setTextPalette()
        if not reload:
            self.getDevice(True)  # Get Device before starting

        # Setup menu bar
        self.mainBar = self.menuBar()
        mainMenu = self.mainBar.addMenu('Main')
        mainMenu.setToolTipsVisible(True)
        designMenu = self.mainBar.addMenu('Design')
        designMenu.setToolTipsVisible(True)
        statsMenu = self.mainBar.addMenu('Stats')
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

        scaleDialog = QAction('Scale', self)
        scaleDialog.setToolTip('Modify the Scale')
        scaleDialog.triggered.connect(self.getScaleDialog)

        splitCheck = QAction('Split Audio', self)
        splitCheck.setCheckable(True)
        splitCheck.setToolTip('Toggle to Split Audio Channels')
        splitCheck.toggled.connect(self.setSplit)
        splitCheck.setChecked(self.split)

        curvyMenu = QMenu('Curviness', self)
        curvyMenu.setToolTip('Set How Much the Bars Curve')
        curvySettings = ['No Curves', 'Sharp', 'Narrow', 'Loose', 'Flat']
        curveList = [0, (5,2), (11,3), (23,4), (43,5)]
        self.curvyDict = {}
        for f in range(5):
            curve = curveList[f]
            self.curvyDict[str(curve)] = QAction(curvySettings[f], self)
            self.curvyDict[str(curve)].setCheckable(True)
            self.curvyDict[str(curve)].triggered.connect(lambda checked, index=curve: self.setCurve(index))
            curvyMenu.addAction(self.curvyDict[str(curve)])
        self.curvyDict[str(self.curvy)].setChecked(True)

        interpMenu = QMenu('Interpolation', self)
        interpMenu.setToolTip('Set Interp Amount (Noise)')
        interpSettings = ['No Interpolation', 'Low [1x]', 'Mid [2x]', 'High [4x]', 'Ultra [6x]']
        interpList = [0, 1, 2, 4, 6]
        interp = 0
        self.interpDict = {}
        for f in range(5):
            interp = interpList[f]
            self.interpDict[str(interp)] = QAction(interpSettings[f], self)
            self.interpDict[str(interp)].setCheckable(True)
            self.interpDict[str(interp)].triggered.connect(lambda checked, index=interp: self.setInterp(index))
            interpMenu.addAction(self.interpDict[str(interp)])
        self.interpDict[str(self.interp)].setChecked(True)

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

        colorMenu = QMenu('Color', self)
        colorMenu.setToolTip('Select Colors and Transparency')
        barColorDialog = QAction('Bar Color', self)
        barColorDialog.triggered.connect(self.setBarColor)
        backColorDialog = QAction('Background Color', self)
        backColorDialog.triggered.connect(self.setBackgroundColor)
        outColorDialog = QAction('Outline Color', self)
        outColorDialog.triggered.connect(self.setOutlineColor)
        rainbowCheck = QAction('Rainbow', self)
        rainbowCheck.setCheckable(True)
        rainbowCheck.triggered.connect(self.setRainbow)
        rainbowCheck.setChecked(self.checkRainbow)

        colorMenu.addAction(barColorDialog)
        colorMenu.addAction(backColorDialog)
        colorMenu.addAction(outColorDialog)
        colorMenu.addAction(rainbowCheck)

        gradDialog = QAction('Gradient', self)
        gradDialog.setToolTip('Create a Gradient')
        gradDialog.triggered.connect(self.getGradDialog)

        sizesCheck = QAction('Dimensions', self)
        sizesCheck.setCheckable(True)
        sizesCheck.setToolTip('Change the Bars Dimensions')
        sizesCheck.toggled.connect(self.showBarSliders)

        lumenCheck = QAction('Illuminate', self)
        lumenCheck.setCheckable(True)
        lumenCheck.setToolTip('Change the Bars Alpha Scale')
        lumenCheck.triggered.connect(self.showLumenSlider)

        outlineCheck = QAction('Outline Only', self)
        outlineCheck.setCheckable(True)
        outlineCheck.setToolTip('Toggle Outline/Turn Off Fill')
        outlineCheck.toggled.connect(self.setOutline)
        outlineCheck.setChecked(self.outline)

        cutoutCheck = QAction('Cutout', self)
        cutoutCheck.setCheckable(True)
        cutoutCheck.setToolTip('Toggle to Cutout Background with Bars')
        cutoutCheck.toggled.connect(self.setCutout)
        cutoutCheck.setChecked(self.cutout)

        deadlineCheck = QAction('Deadline', self)
        deadlineCheck.setCheckable(True)
        deadlineCheck.setToolTip('Display FPS Deadline Ratio')
        deadlineCheck.toggled.connect(self.showDeadline)
        deadlineCheck.setChecked(self.checkDeadline)

        barNumCheck = QAction('Bars', self)
        barNumCheck.setCheckable(True)
        barNumCheck.setToolTip('Display Amount of Bars')
        barNumCheck.toggled.connect(self.showBarNum)
        barNumCheck.setChecked(self.checkBarNum)

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
        self.freqsCheck.setToolTip('Show Each Bar\'s Frequency')
        self.freqsCheck.toggled.connect(self.showFreq)
        self.freqsCheck.setChecked(self.checkFreq)

        self.notesCheck = QAction('Notes', self)
        self.notesCheck.setCheckable(True)
        self.notesCheck.setToolTip('Frequencies as Notes')
        self.notesCheck.toggled.connect(self.showNotes)
        self.notesCheck.setChecked(self.checkNotes)

        self.fpsSpinBox = QSpinBox()
        self.fpsSpinBox.setRange(1, 999)
        self.fpsSpinBox.setSuffix(' FPS')
        self.fpsSpinBox.setMaximumWidth(70)
        self.fpsSpinBox.setMaximumHeight(20)
        self.fpsSpinBox.valueChanged.connect(self.setFrameRate)
        self.fpsSpinBox.setValue(self.frameRate)
        self.fpsSpinBox.setKeyboardTracking(False)
        self.fpsSpinBox.setFocusPolicy(Qt.ClickFocus)
        fpsDock = QDockWidget(self)
        fpsDock.move(155, -20)
        fpsDock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        fpsDock.setWidget(self.fpsSpinBox)
        fpsDock.show()

        mainMenu.addMenu(profilesMenu)
        mainMenu.addAction(deviceDialog)
        mainMenu.addAction(scaleDialog)
        mainMenu.addAction(splitCheck)
        mainMenu.addMenu(curvyMenu)
        mainMenu.addMenu(interpMenu)
        mainMenu.addMenu(bufferMenu)
        designMenu.addMenu(colorMenu)
        designMenu.addAction(gradDialog)
        designMenu.addAction(sizesCheck)
        designMenu.addAction(lumenCheck)
        designMenu.addAction(outlineCheck)
        designMenu.addAction(cutoutCheck)
        statsMenu.addAction(deadlineCheck)
        statsMenu.addAction(barNumCheck)
        statsMenu.addAction(latencyCheck)
        statsMenu.addAction(dbBarCheck)
        statsMenu.addAction(self.freqsCheck)
        statsMenu.addAction(self.notesCheck)

        if reload:  # Manual setting trigger after a reload
            self.curvyDict[str(self.curvy)].trigger()
            self.interpDict[str(self.interp)].trigger()
            self.audioBufferDict[str(self.audioBuffer)].trigger()

        self.show()
        self.starterVars()
        if not reload:
            self.updatePlots()
            self.startProcesses()

    def starterVars(self):
        # Define placeholder stater variables
        self.barsAmt = self.size().width() // self.wholeWidth
        self.barValues = [0]
        self.splitBarValues = [0]
        self.dataList = [0]
        self.delay = 0
        self.frames = 0
        self.paintBusy = 0
        self.paintTime = 0
        self.paintDelay = (1 / self.frameRate)

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
            self.syncLock, dataTime, self.proTime, self.dataArray, dataArray2, self.proArray, self.proArray2, self.proQ, self.dataQ,
            self.frameRate, self.audioBuffer, self.plotsList, self.split, self.curvy, self.interp))

        # Separate main thread from event loop
        self.mainThread = th.Thread(target=self.mainLoop)

        self.T1.daemon = True
        self.P1.daemon = True
        self.T1.start()
        self.P1.start()
        self.mainThread.start()

    def mainLoop(self):
        while True:
            # Gets final results from processing
            self.delay = self.proTime.value
            self.barValues = self.proArray[:self.barsAmt]
            self.splitBarValues = self.proArray2[:self.barsAmt]
            if self.checkDB:
                self.dataList = self.dataArray[:self.audioBuffer]

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
                self.update()
                self.updateObjects()

                blockTime = time.time()
                self.blockLock.acquire(timeout=1)
                if (time.time() - blockTime) >= 1:
                    self.repaint()  # Revives painter

            if self.mainQ.qsize() > 0:
                break

    def updateObjects(self):
        if self.checkDeadline:
            if not hasattr(self, 'loopTime'):   # Start loop here so percent starts at 0
                self.loopTime = time.time()

            block = self.frameRate // 10
            if block < 1: block = 1
            if self.frames % block == 0:
                self.latePercent = round(((1 / self.frameRate) / (time.time() - self.loopTime)) * 100, 2)

            # print(1 / (time.time() - self.loopTime))
            self.loopTime = time.time()

        # Update height slider
        if hasattr(self, 'showHeightSlider'):
            if self.showHeightSlider.isSliderDown():
                self.setBarHeight()
            else:
                self.showHeightSlider.setValue(0)

        if self.checkRainbow:
            self.setRainbow(1)

    def updatePlots(self):
        plot = self.sampleRate / self.audioBuffer

        startPoint = self.pointsList[0] / plot
        startCurve = startPoint * self.pointsList[1]
        midPoint = self.pointsList[2] / plot
        midPointPos = int(round(self.barsAmt * self.pointsList[3]))
        endCurve = midPoint * self.pointsList[4]
        endPoint = self.pointsList[5] / plot

        startScale = ReVidia.quadBezier(startPoint, midPoint, startCurve, midPointPos)
        endScale = ReVidia.quadBezier(midPoint, endPoint, endCurve, self.barsAmt - midPointPos, True)
        plots = startScale + endScale

        self.plotsList = list(map(int, ReVidia.dataPlotter(plots, 1, self.audioBuffer // 2)))
        if hasattr(self, 'proQ'):
            self.proQ.put(['plots', self.plotsList])

    def setTextPalette(self):
        if not hasattr(self, 'textPalette'):
            self.textPalette = QPalette()
        # Sets the text color to better see it against background
        if self.backgroundColor.value() <= 128:
            self.textPalette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        else:
            self.textPalette.setColor(QPalette.WindowText, QColor(0, 0, 0))

        self.setPalette(self.textPalette)

    def paintEvent(self, event):
        self.paintBusy = 1

        painter = QPainter(self)
        painter.setPen(QPen(Qt.NoPen))  # Removes pen
        self.paintBackground(event, painter)
        if not self.cutout:
            self.paintBars(event, painter)
        if self.checkFreq or self.checkNotes:
            self.paintFreq(event, painter)
        if self.checkDB:
            self.paintDB(event, painter)
        if self.checkDeadline or self.checkBarNum or self.checkLatency:
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
        if not self.cutout:     # Normal background
            painter.drawRect(0, 0, self.size().width(), self.size().height())
        else:       # Cutout background
            xSize = self.barWidth
            xPos = (self.gapWidth // 2)
            yPos = 0
            for y in range(len(self.barValues)):
                ySizeV = int(self.barValues[y] * self.barHeight)
                ySize = self.size().height() - ySizeV
                painter.drawRect(xPos - self.gapWidth, yPos, self.gapWidth, self.size().height())   # Gap bar

                if self.split:
                    ySplitV = int(self.splitBarValues[y] * self.barHeight)
                    ySize = (self.size().height() // 2) - ySizeV
                    painter.drawRect(xPos, yPos, xSize, ySize)  # Top background
                    ySize = (self.size().height() // 2) - ySplitV
                    painter.drawRect(xPos, self.size().height(), xSize, -ySize)  # bottom background
                else:
                    painter.drawRect(xPos, yPos, xSize, ySize)

                xPos += self.wholeWidth

            painter.drawRect(xPos - self.wholeWidth + xSize, yPos,
                             self.size().width() + self.wholeWidth - xPos, self.size().height())   # Last Gap bar

    def paintBars(self, event, painter):
        ySizeList = []
        yPosList = []
        xSize = self.barWidth
        xPos = (self.gapWidth // 2)
        yPos = self.size().height()
        viewHeight = self.size().height()
        if self.lumen:
            lumReigen = 255 / (viewHeight * (self.lumen / 100))

        if not self.gradient:
            barColor = self.barColor
        else:
            barColor = QGradient(self.gradient)

        painter.setBrush(barColor)

        if len(self.barValues) == self.barsAmt:
            for y in range(len(self.barValues)):
                ySize = int(self.barValues[y] * self.barHeight)

                if self.split and len(self.splitBarValues) == self.barsAmt:
                    if ySize > viewHeight // 2:
                        ySize = viewHeight // 2
                    ySplitV = int(self.splitBarValues[y] * self.barHeight)
                    if ySplitV > viewHeight // 2:
                        ySplitV = viewHeight // 2
                    yPos = (self.size().height() // 2) + ySplitV
                    ySize = ySplitV + ySize
                # Place boundary
                if ySize > viewHeight:
                    ySize = viewHeight
                if ySize < 0: ySize = 0

                if self.lumen:
                    color = barColor
                    lumBright = int(ySize * lumReigen)
                    if lumBright > 255: lumBright = 255
                    if not self.gradient:
                        color.setAlpha(lumBright)
                    else:
                        for stop in barColor.stops():
                            pos = stop[0]
                            point = stop[1]
                            point.setAlpha(lumBright)
                            color.setColorAt(pos, point)
                    painter.setBrush(color)  # Fill of bar color

                if not self.outline:
                    painter.drawRect(xPos, yPos, xSize, -ySize)

                xPos += self.wholeWidth
                if self.outlineSize:
                    ySizeList.append(ySize)
                    yPosList.append(yPos)

            if self.outlineSize:
                xPos = (self.gapWidth // 2)

                if self.gradient and self.outline:
                    painter.setBrush(self.gradient)
                else:
                    painter.setBrush(self.outlineColor)  # Fill of outline color
                for y in range(len(self.barValues)):
                    ySize = ySizeList[y]
                    yPos = yPosList[y]
                    if ySize > 0:    # Hack way of making outline without the (Slow QPen)
                        painter.drawRect(xPos, yPos, self.outlineSize, -ySize)  # Left
                        painter.drawRect(xPos, yPos-ySize, self.barWidth,  self.outlineSize)  # Top
                        painter.drawRect(xPos + self.barWidth, yPos-ySize, -self.outlineSize, ySize)  # Right
                        painter.drawRect(xPos, yPos, self.barWidth, -self.outlineSize)  # Bottom

                    xPos += self.wholeWidth

    def paintFreq(self, event, painter):
        # Set pen color to contrast bar color
        pen = QPen()
        if self.barColor.value() <= 128:
            pen.setColor(QColor(255, 255, 255))
        else:
            pen.setColor(QColor(0, 0, 0))
        painter.setPen(pen)
        font = QFont()
        # Scale text with bar size
        fontSize = self.barWidth - (self.outlineSize * 2) - 1
        if fontSize < 1: fontSize = 1
        font.setPixelSize(fontSize)
        painter.setFont(font)

        freqList = ReVidia.assignFreq(self.audioBuffer, self.sampleRate, self.plotsList)

        ySize = int(fontSize * 1.5)
        xPos = self.gapWidth // 2
        yPos = self.size().height() - self.outlineSize
        if self.split:
            yPos = self.size().height() // 2

        # Paint frequency plot
        if self.checkFreq:
            for freq in freqList:
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
                xTextPos = xPos + self.outlineSize
                yTextPos = yPos - yTextSize

                painter.drawText(xTextPos, yTextPos, xTextSize, yTextSize, Qt.AlignCenter | Qt.TextWrapAnywhere, str(freq))
                xPos += self.wholeWidth

        # Instead of painting freq, give a approximation of notes
        elif self.checkNotes:
            notes = ReVidia.assignNotes(freqList)

            xSize = self.barWidth + 1
            yTextPos = yPos - ySize
            for note in notes:
                painter.drawText(xPos, yTextPos, xSize, ySize, Qt.AlignCenter, note)
                xPos += self.wholeWidth

    # Draws a dB bar in right corner
    def paintDB(self, event, painter):
        dbValue = ReVidia.getDB(self.dataList)

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
        if self.checkBarNum:
            text = str(self.barsAmt) + ' Bars'
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
        saveList = ['width', 'height', 'frameRate', 'pointsList', 'split', 'curvy', 'interp', 'audioBuffer', 'lumen',
                    'checkRainbow', 'barWidth', 'gapWidth', 'outlineSize', 'barHeight', 'wholeWidth', 'outline',
                    'cutout', 'checkFreq', 'checkNotes', 'checkDeadline', 'checkBarNum', 'checkLatency', 'checkDB',
                    'backgroundColor', 'barColor', 'outlineColor']

        if request == 'save':
            profile, ok = QInputDialog.getText(self, "Save Profile", "Profile Name:")
            if ok and profile:
                with open('profiles/' + profile + '.pkl', 'wb') as file:
                    for setting in saveList:
                        pickle.dump(getattr(self, setting), file)
                    if self.gradient:
                        grad = self.gradient
                        gradAttr = grad.start(), grad.finalStop(), grad.stops(), grad.coordinateMode()
                        pickle.dump(gradAttr, file)
                    else:
                        pickle.dump(0, file)
        else:
            profileList = []
            for file in os.listdir('profiles'):
                profileList.append(file.strip('.pkl'))
            if not profileList:
                profileList.append('No Profiles Saved')

            if request == 'load':
                profile, ok = QInputDialog.getItem(self, "Load Profile", "Select Profile:", profileList, 0, False)
                if ok and profile and profileList != ['No Profiles Saved']:
                    with open('profiles/' + profile + '.pkl', 'rb') as file:
                        for setting in saveList:
                            var = pickle.load(file)
                            setattr(self, setting, var)
                        gradAttr = pickle.load(file)
                        if gradAttr:
                            self.gradient = QLinearGradient(gradAttr[0], gradAttr[1])
                            self.gradient.setStops(gradAttr[2])
                            self.gradient.setCoordinateMode(gradAttr[3])
                        else:
                            self.gradient = 0
                    self.mainBar.clear()
                    self.fpsSpinBox.close()
                    self.initUI(True)

            elif request == 'delete':
                profile, ok = QInputDialog.getItem(self, "Delete Profile", "Select Profile:", profileList, 0, False)
                if ok and profile and profileList != ['No Profiles Saved']:
                    os.remove('profiles/' + profile + '.pkl')

    def getDevice(self, firstRun, output=False):
        # Find default devices for PyAudio
        defaultHWOut = ''
        defaultHWIn = ''
        if self.userSink:
            result = subprocess.getoutput(
                'pactl list sinks | sed -n /' + self.userSink + '/,/"Sink #"/p | grep -e "alsa.card =" -e "alsa.device"')
            if result:
                card = result.split('alsa.card = "')[1].split('"')[0]
                device = result.split('alsa.device = "')[1].split('"')[0]
                defaultHWOut = 'hw:' + card + ',' + device

        if self.userSource:
            result = subprocess.getoutput(
                'pactl list sources | sed -n /' + self.userSource + '/,/"Source #"/p | grep -e "alsa.card =" -e "alsa.device"')
            if result:
                card = result.split('alsa.card = "')[1].split('"')[0]
                device = result.split('alsa.device = "')[1].split('"')[0]
                defaultHWIn = 'hw:' + card + ',' + device

        if defaultHWOut or defaultHWIn:
            # Free up default audio device so it can be detected
            subprocess.run('pactl suspend-sink "' + self.userSink + '" 1', shell=True)

        # Run device getter on separate Process because the other PA won't start if not done
        devQ = mp.Queue()
        D1 = mp.Process(target=ReVidia.deviceNames, args=(devQ, self.userSink))
        D1.start(), D1.join()
        deviceList = devQ.get()
        if defaultHWOut or defaultHWIn:
            subprocess.run('pactl suspend-sink "' + self.userSink + '" 0', shell=True)

        defaultList = []
        if defaultHWOut:
            defaultList.append('Default ALSA Output Device')
        if defaultHWIn:
            defaultList.append('Default ALSA Input Device')

        itemList = defaultList + deviceList[0]
        if not output:
            device, ok = QInputDialog.getItem(self, "ReVidia", "Select Audio Device:", itemList, 0, False)
        else:   # Auto select JACK
            device = 'Input: PulseAudio JACK Sink - JACK Audio Connection Kit'
            ok = 1

        if ok and device:
            if defaultHWOut in device and 'Output' in device:
                device = 'Default ALSA Output Device'
            # Getting ID
            if device == 'Default ALSA Output Device':
                ID = defaultHWOut
            elif device == 'Default ALSA Input Device':
                ID = defaultHWIn
                for device in deviceList[0]:
                    if defaultHWOut in device and 'Input' in device:
                        ID = deviceList[1][deviceList[0].index(device)]
            else:
                ID = deviceList[1][deviceList[0].index(device)]

            if isinstance(ID, int):  # If PortAudio Index Num, continue
                self.ID = ID
                self.sampleRate = deviceList[2][deviceList[0].index(device)]
            else:   # If hw:x,y run JACK
                if not firstRun:    # Kill JACK if already running
                    if hasattr(self, 'jack'):
                        subprocess.run('pactl set-default-sink "' + self.userSink + '"',
                                       shell=True)  # Restore user's default
                        self.jack.kill()
                        del self.jack

                # Free up default audio device so it can be used
                subprocess.run('pactl suspend-sink "' + self.userSink + '" 1', shell=True)

                # Start Jack and change Pulseaudio device to Jack_Sink to collect data
                self.jack = subprocess.Popen('jackd -T -d alsa -d' + ID, shell=True)
                subprocess.run('pactl load-module module-jack-sink sink_name="Jack_Sink" ', shell=True)
                subprocess.run('pactl suspend-sink "' + self.userSink + '" 0', shell=True)

                if device == 'Default ALSA Output Device':
                    subprocess.run('pactl set-default-sink "Jack_Sink"', shell=True)

                # Moving over streams to Default Sink
                result = subprocess.getoutput('pactl list sink-inputs | grep "Sink Input #"')
                if result:
                    streams = result.split('\n')
                    result = subprocess.getoutput('pactl info | grep "Default Sink:"')
                    defaultSink = result.split('Default Sink: ')[1]
                    for stream in streams:
                        index = stream.split('Sink Input #')[1]
                        subprocess.run('pactl move-sink-input ' + index + ' "' + defaultSink + '"', shell=True)

                if firstRun:
                    self.getDevice(True, True)
                else:
                    self.getDevice(False, True)

            if firstRun: return
            else:
                self.mainQ.put(1), self.mainThread.join()
                self.proQ.put(['kill'])
                self.dataQ.put(['kill'])
                self.startProcesses()

        elif firstRun: sys.exit()

    def getScaleDialog(self):
        self.scaleDialog = ScaleDialog(self)
        self.scaleDialog.setMinimumSize(150, 100)
        self.scaleDialog.setGeometry(self.pos().x(), self.pos().y(), self.size().width()//2, self.size().height()//2)
        self.scaleDialog.show()

    def setSplit(self, on):
        if on:
            self.split = 1
        else:
            self.split = 0

        self.dataQ.put(['split', self.split])
        self.proQ.put(['split', self.split])

    def setCurve(self, index):
        self.curvy = index
        for f in self.curvyDict:
            if f != str(index):
                self.curvyDict[str(f)].setChecked(False)
            else:
                self.curvyDict[str(f)].setChecked(True)

        self.proQ.put(['curvy', self.curvy])

    def setFrameRate(self, value):
        self.frameRate = value
        self.paintDelay = (1 / self.frameRate)

        if hasattr(self, 'proQ'):
            self.proQ.put(['frameRate', self.frameRate])

    def setInterp(self, index):
        self.interp = index

        for f in self.interpDict:
            if int(f) != index:
                self.interpDict[str(f)].setChecked(False)
            else:
                self.interpDict[str(f)].setChecked(True)

        self.proQ.put(['interp', self.interp])

    def setAudioBuffer(self, index):
        self.audioBuffer = index

        for f in self.audioBufferDict:
            if int(f) != index:
                self.audioBufferDict[str(f)].setChecked(False)
            else:
                self.audioBufferDict[str(f)].setChecked(True)

        self.dataQ.put(['buffer', self.audioBuffer])
        self.proQ.put(['buffer', self.audioBuffer])
        self.updatePlots()

    def setBarColor(self):
        self.barColor = QColorDialog.getColor(self.barColor,None,None,QColorDialog.ShowAlphaChannel)

    def setBackgroundColor(self):
        self.backgroundColor = QColorDialog.getColor(self.backgroundColor,None,None,QColorDialog.ShowAlphaChannel)
        self.setTextPalette()

    def setOutlineColor(self):
        self.outlineColor = QColorDialog.getColor(self.outlineColor, None, None, QColorDialog.ShowAlphaChannel)

    def setRainbow(self, on):
        if not hasattr(self, 'rainbowHue'):
            self.rainbowHue = self.barColor.hue()
            self.checkRainbow = 1
            if self.barColor.saturation() == 0:
                self.barColor.setHsv(0,255,self.barColor.value())
        if on:
            if self.rainbowHue < 359:
                self.rainbowHue += 1
            else:
                self.rainbowHue = 0

            self.barColor.setHsv(self.rainbowHue,self.barColor.saturation(),
                                 self.barColor.value(),self.barColor.alpha())
            if self.outline:
                self.outlineColor.setHsv(self.rainbowHue, self.barColor.saturation(),
                                     self.barColor.value(), self.barColor.alpha())
        else:
            self.checkRainbow = 0
            del self.rainbowHue

    def getGradDialog(self):
        self.gradDialog = GradientDialog(self)
        self.gradDialog.setMinimumSize(150, 100)
        posX = self.pos().x() + self.size().width() // 2
        self.gradDialog.setGeometry(posX, self.pos().y(), self.size().width() // 2,
                                     self.size().height() // 2)
        self.gradDialog.show()

    def showBarSliders(self, on):
        if on:
            self.showBarText = QLabel(self)
            self.showBarText.setText('Bar Width ' + str(self.barWidth))
            self.showBarText.setGeometry(5, 25, 100, 20)
            self.showBarText.show()
            self.showBarWidth = QSlider(Qt.Horizontal, self)
            self.showBarWidth.setMinimum(1)
            self.showBarWidth.setValue(self.barWidth)
            self.showBarWidth.setGeometry(0, 40, 90, 30)
            self.showBarWidth.valueChanged.connect(self.setBarSize)
            self.showBarWidth.show()

            self.showGapText = QLabel(self)
            self.showGapText.setText('Gap Width ' + str(self.gapWidth))
            self.showGapText.setGeometry(105, 25, 100, 20)
            self.showGapText.show()
            self.showGapWidth = QSlider(Qt.Horizontal, self)
            self.showGapWidth.setValue(self.gapWidth)
            self.showGapWidth.setGeometry(100, 40, 90, 30)
            self.showGapWidth.valueChanged.connect(self.setGapSize)
            self.showGapWidth.show()

            self.showOutlineText = QLabel(self)
            self.showOutlineText.setText('Out Width ' + str(self.outlineSize))
            self.showOutlineText.setGeometry(205, 25, 100, 20)
            self.showOutlineText.show()
            self.showOutWidth = QSlider(Qt.Horizontal, self)
            self.showOutWidth.setMaximum(50)
            self.showOutWidth.setValue(self.outlineSize)
            self.showOutWidth.setGeometry(200, 40, 90, 30)
            self.showOutWidth.valueChanged.connect(self.setOutlineSize)
            self.showOutWidth.show()

            self.showHeightText = QLabel(self)
            self.showHeightText.setText('Height \n' + str(round(self.barHeight * 1000, 2)))
            self.showHeightText.setGeometry(30, 65, 50, 40)
            self.showHeightText.show()
            self.showHeightSlider = QSlider(Qt.Vertical, self)
            self.showHeightSlider.setMinimum(-100)
            self.showHeightSlider.setMaximum(100)
            self.showHeightSlider.setValue(0)
            self.showHeightSlider.setGeometry(0, 70, 30, 150)
            self.showHeightSlider.valueChanged.connect(self.setBarHeight)
            self.showHeightSlider.show()
        else:
            # Clean up
            self.showBarWidth.close()
            self.showGapWidth.close()
            self.showOutWidth.close()
            self.showHeightSlider.close()
            self.showBarText.close()
            self.showGapText.close()
            self.showOutlineText.close()
            self.showHeightText.close()
            del self.showBarWidth
            del self.showGapWidth
            del self.showOutWidth
            del self.showHeightSlider
            del self.showBarText
            del self.showGapText
            del self.showOutlineText
            del self.showHeightText

    def setBarSize(self, value):
        self.barWidth = value
        self.wholeWidth = self.barWidth + self.gapWidth
        self.barsAmt = self.size().width() // self.wholeWidth
        self.updatePlots()
        if self.outlineSize > self.barWidth // 2:
            self.setOutlineSize(self.outlineSize)

        self.showBarText.setText('Bar Width ' + str(self.barWidth))

    def setGapSize(self, value):
        self.gapWidth = value
        self.wholeWidth = self.barWidth + self.gapWidth
        self.barsAmt = self.size().width() // self.wholeWidth
        self.updatePlots()

        self.showGapText.setText('Gap Width ' + str(self.gapWidth))

    def setOutlineSize(self, value):
        if value <= self.barWidth // 2:
            self.outlineSize = value
        else:
            self.outlineSize = self.barWidth // 2
            self.showOutWidth.setValue(self.outlineSize)

        self.showOutlineText.setText('Out Width ' + str(self.outlineSize))

    def setBarHeight(self):

        value = self.showHeightSlider.value()
        if value > 0:
            value = 1 + value / (self.frameRate * 10)
            if self.barHeight < 10:
                self.barHeight *= value
        elif value < 0:
            value = 1 + -value / (self.frameRate * 10)
            if self.barHeight > 0.000001:
                self.barHeight /= value

        self.showHeightText.setText('Height \n' + str(round(self.barHeight * 1000, 2)))

    def showLumenSlider(self, on):
        if on:
            self.showLumenText = QLabel(self)
            self.showLumenText.setText('Light Limit \n' + str(self.lumen) + '%')
            self.showLumenText.setGeometry(30, 235, 75, 40)
            self.showLumenText.show()
            self.lumenSlider = QSlider(Qt.Vertical, self)
            self.lumenSlider.setMaximum(100)
            self.lumenSlider.setValue(self.lumen)
            self.lumenSlider.setGeometry(0, 240, 30, 100)
            self.lumenSlider.valueChanged.connect(self.setLumen)
            self.lumenSlider.show()
        else:
            self.showLumenText.close()
            self.lumenSlider.close()
            del self.showLumenText
            del self.lumenSlider

    def setLumen(self, value):
        self.lumen = value

        self.showLumenText.setText('Light Limit \n' + str(self.lumen) + '%')

    def setOutline(self, on):
        if on:
            self.outline = 1
        else:
            self.outline = 0

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

    def showBarNum(self, on):
        if on:
            self.checkBarNum = 1
        else:
            self.checkBarNum = 0

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

    # Adds keyboard inputs
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        if event.key() == Qt.Key_Shift:
            if not hasattr(self, 'menuToggle'):
                self.menuToggle = 0

            if self.menuToggle == 0:
                self.menuToggle = 1
                self.menuBar().hide()
                self.fpsSpinBox.hide()
                return
            if self.menuToggle == 1:
                self.menuToggle = 2
                self.oldX = self.x()
                self.oldY = self.y()
                self.setWindowFlags(Qt.FramelessWindowHint)
                self.show()
                return
            if self.menuToggle == 2:
                self.menuToggle = 0
                self.setWindowFlags(self.windowFlags() & ~Qt.FramelessWindowHint)
                self.menuBar().show()
                self.fpsSpinBox.show()
                self.show()
                self.move(self.oldX + 1, self.oldY + 1)  # Fixes a weird bug with the window
                self.move(self.oldX, self.oldY)
                return

    # Allows to adjust bars height by scrolling on window
    def wheelEvent(self, event):
        mouseDir = event.angleDelta().y()
        if mouseDir > 0:
            if self.barHeight < 10:
                self.barHeight *= 1.5
        elif mouseDir < 0:
            if self.barHeight > 0.000001:
                self.barHeight /= 1.5

        if hasattr(self, 'showHeightText'):
            self.showHeightText.setText('Height \n' + str(round(self.barHeight * 1000, 2)))

    def resizeEvent(self, event):
        if hasattr(self, 'barsAmt'):
            self.barsAmt = self.size().width() // self.wholeWidth
            self.updatePlots()

    # Makes sure the processes are not running in the background after closing
    def closeEvent(self, event):
        try:
            self.mainQ.put(1)   # End main thread
            self.P1.terminate()   # Kill Processes
            self.T1.terminate()
            if hasattr(self, 'jack'):
                subprocess.run('pactl set-default-sink "' + self.userSink + '"', shell=True)  # Restore user's default
                self.jack.kill()
        except RuntimeError:
            print('Some processes won\'t close properly, closing anyway.')


class ScaleDialog(QMainWindow):
    def __init__(self, main):
        super(ScaleDialog, self).__init__()
        self.main = main
        self.setWindowTitle('Scale')
        self.border = 10
        self.pRad = 5   # Point radius
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

        self.intiUI()

    def intiUI(self):
        mainBar = self.menuBar()
        mainBar.heightForWidth(20)

        self.scaleModeCheck = QAction('Bezier', self)
        self.scaleModeCheck.setCheckable(True)
        self.scaleModeCheck.triggered.connect(self.setScaleMode)

        mainBar.addAction(self.scaleModeCheck)

        self.startPointSpinBox = QSpinBox()
        self.startPointSpinBox.setRange(0, int(self.main.sampleRate // 2))
        self.startPointSpinBox.setSuffix(' HZ')
        self.startPointSpinBox.setMaximumWidth(90)
        self.startPointSpinBox.setMaximumHeight(20)
        self.startPointSpinBox.valueChanged.connect(self.setStartPoint)
        self.startPointSpinBox.setValue(self.startPoint)
        self.startPointSpinBox.setKeyboardTracking(False)
        self.startPointSpinBox.setFocusPolicy(Qt.ClickFocus)
        startPointDock = QDockWidget(self)
        startPointDock.move(55, -20)
        startPointDock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        startPointDock.setWidget(self.startPointSpinBox)
        startPointDock.show()

        self.midPointSpinBox = QSpinBox()
        self.midPointSpinBox.setRange(0, int(self.main.sampleRate // 2))
        self.midPointSpinBox.setSuffix(' HZ')
        self.midPointSpinBox.setMaximumWidth(90)
        self.midPointSpinBox.setMaximumHeight(20)
        self.midPointSpinBox.valueChanged.connect(self.setMidPoint)
        self.midPointSpinBox.setValue(self.midPoint)
        self.midPointSpinBox.setKeyboardTracking(False)
        self.midPointSpinBox.setFocusPolicy(Qt.ClickFocus)
        midPointDock = QDockWidget(self)
        midPointDock.move(160, -20)
        midPointDock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        midPointDock.setWidget(self.midPointSpinBox)
        midPointDock.show()

        self.endPointSpinBox = QSpinBox()
        self.endPointSpinBox.setRange(0, int(self.main.sampleRate // 2))
        self.endPointSpinBox.setSuffix(' HZ')
        self.endPointSpinBox.setMaximumWidth(90)
        self.endPointSpinBox.setMaximumHeight(20)
        self.endPointSpinBox.valueChanged.connect(self.setEndPoint)
        self.endPointSpinBox.setValue(self.endPoint)
        self.endPointSpinBox.setKeyboardTracking(False)
        self.endPointSpinBox.setFocusPolicy(Qt.ClickFocus)
        endPointDock = QDockWidget(self)
        endPointDock.move(265, -20)
        endPointDock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        endPointDock.setWidget(self.endPointSpinBox)
        endPointDock.show()

    def setScaleMode(self, mode):
        if mode == 0:
            self.scaleMode = 0
            self.scaleModeCheck.setText('Bezier')
        else:
            self.scaleMode = 1
            self.scaleModeCheck.setText('Real')

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
        self.main.updatePlots()
        self.update()

    def resizeEvent(self, event):
        xSize = self.size().width() - self.border * 2
        ySize = self.size().height() - self.border * 2 - 25
        self.boundry = QRect(self.border, self.border + 25, xSize, ySize)

        if self.scaleMode == 1:
            steps = (self.main.sampleRate / 2) / (ySize-1)
            self.freqScale = ReVidia.realScale(0, (self.main.sampleRate // 2), steps)
        else:
            self.freqScale = ReVidia.quadBezier(0, (self.main.sampleRate // 2), 0, (ySize-1), True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.main.backgroundColor)
        painter.drawRect(0, 0, self.size().width(), self.size().height())

        painter.setRenderHints(QPainter.Antialiasing)
        linePen = QPen()
        linePen.setColor(self.main.barColor)
        linePen.setWidth(3)
        linePen.setCapStyle(Qt.RoundCap)
        painter.setPen(linePen)

        painter.drawRect(self.boundry)

        widthScale = self.boundry.width() / self.main.barsAmt
        xPos1 = self.border - widthScale
        xPos2 = self.border

        freqList = (ReVidia.assignFreq(self.main.audioBuffer, self.main.sampleRate, self.main.plotsList, True))

        midPoint = int(round(self.main.barsAmt * self.midPointPos))
        for i in range(len(freqList)):
            freq = freqList[i]

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
                self.startPointSpinBox.setValue(self.startPoint)

            if self.holdMidPoint:
                midX = (event.x() - self.border) / self.boundry.width()
                if midX > 0.9: midX = 0.9
                if midX < 0.1: midX = 0.1

                self.midPointPos = midX

                index = self.size().height() - event.y() - self.border
                if index > self.boundry.height()-1: index = self.boundry.height()-1
                if index < 0: index = 0

                self.midPoint = int(self.freqScale[index])
                self.midPointSpinBox.setValue(self.midPoint)

            if self.holdEndPoint:
                index = self.size().height() - event.y() - self.border
                if index > self.boundry.height()-1: index = self.boundry.height()-1
                if index < 0: index = 0

                self.endPoint = int(self.freqScale[index])
                self.endPointSpinBox.setValue(self.endPoint)

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


class GradientDialog(QMainWindow):
    def __init__(self, main):
        super(GradientDialog, self).__init__()
        self.main = main
        self.setWindowTitle('Gradient')
        self.disabled = 0

        self.intiUI()

        if self.main.gradient:
            self.colorPoints = self.main.gradient.stops()
            if self.main.gradient.start().y() > 0:
                self.dirMode = 0
                self.dirModeCheck.setText('Vertical')
            else:
                self.dirMode = 1
                self.dirModeCheck.setText('Horizontal')

            if self.main.gradient.coordinateMode() == 1:
                self.fillMode = 0
                self.fillModeCheck.setText('Whole')
            else:
                self.fillMode = 1
                self.fillModeCheck.setText('Per-Bar')

        else:
            self.colorPoints = []
            self.fillMode = 0
            self.dirMode = 0

        self.setGradient()

    def intiUI(self):
        mainBar = self.menuBar()
        mainBar.heightForWidth(20)

        self.dirModeCheck = QAction('Vertical', self)
        self.dirModeCheck.setCheckable(True)
        self.dirModeCheck.triggered.connect(self.setDirMode)

        self.fillModeCheck = QAction('Whole', self)
        self.fillModeCheck.setCheckable(True)
        self.fillModeCheck.triggered.connect(self.setFillMode)

        clear = QAction('Clear', self)
        clear.triggered.connect(self.runClear)

        self.enabled = QAction('Enabled', self)
        self.enabled.setCheckable(True)
        self.enabled.triggered.connect(self.setEnabled)
        self.enabled.setChecked(True)

        mainBar.addAction(self.dirModeCheck)
        mainBar.addAction(self.fillModeCheck)
        mainBar.addAction(clear)
        mainBar.addAction(self.enabled)

    def setDirMode(self, mode):
        if mode == 0:
            self.dirMode = 0
            self.dirModeCheck.setText('Vertical')
        else:
            self.dirMode = 1
            self.dirModeCheck.setText('Horizontal')

        self.setGradient()

    def setFillMode(self, mode):
        if mode == 0:
            self.fillMode = 0
            self.fillModeCheck.setText('Whole')
        else:
            self.fillMode = 1
            self.fillModeCheck.setText('Per-Bar')

        self.setGradient()

    def runClear(self):
        self.colorPoints = []
        self.setGradient()

    def setEnabled(self, on):
        if on:
            self.enabled.setText('Enabled')
            self.disabled = 0
            self.setGradient()
        else:
            self.enabled.setText('Disabled')
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
        self.GH = self.size().height() - 20     # Graphics Height

    def paintEvent(self, event):
        painter = QPainter(self)
        yPos = 20

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
                painter.drawLine(pos, yPos, pos, self.GH+20)

    def mouseDoubleClickEvent(self, event):
        if event.button() == 1:
            if self.dirMode == 0:
                point = 1 - ((event.y() - 20) / self.GH)
            else:
                point = event.x() / self.GW

            color = QColorDialog.getColor(QColor(255,255,255),None,None,QColorDialog.ShowAlphaChannel)

            self.colorPoints.append((point, color))
            self.setGradient()

    def mousePressEvent(self, event):
        if event.button() == 2:
            if self.dirMode == 0:
                posF = 1 - ((event.y() - 20) / self.GH)
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
