#!venv/Scripts/pythonw
# -*- coding: utf-8 -*-

import ReverseFFT
import ReVidia_win
import sys
import time
import threading as th
import multiprocessing as mp
from PyQt5.QtCore import Qt, QPoint, QRect
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
# Windows Icon fix
import ctypes
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('r.r.r.r')


# Create the self object and main window
class ReVidiaMain(QMainWindow):
    def __init__(self):
        super(ReVidiaMain, self).__init__()

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
        self.lumen = 0
        self.gradient = 0
        self.checkRainbow = 0
        self.barWidth = 14
        self.gapWidth = 6
        self.outlineSize = 0
        self.barHeight = 0
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
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setTextPalette()
        if not reload:
            self.getDevice(True)  # Get Device before starting
            self.mainBar = self.menuBar()

        # Setup menu bar
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

        FFTAudDialog = QAction('Reverse FFT', self)
        FFTAudDialog.setToolTip('Listen to the Sound of the Visualizer')
        FFTAudDialog.triggered.connect(self.getFFTAudDialog)

        scaleDialog = QAction('Freq Scale', self)
        scaleDialog.setToolTip('Modify the Frequency Scale')
        scaleDialog.triggered.connect(self.getScaleDialog)

        splitCheck = QAction('Split Audio', self)
        splitCheck.setCheckable(True)
        splitCheck.setToolTip('Toggle to Split Audio Channels')
        splitCheck.toggled.connect(self.setSplit)
        splitCheck.setChecked(self.split)

        curvyMenu = QMenu('Curviness', self)
        curvyMenu.setToolTip('Set How Much the Bars Curve')
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

        gradDialog = QAction('Gradient', self)
        gradDialog.setToolTip('Create a Gradient')
        gradDialog.triggered.connect(self.getGradDialog)

        self.autoLevel = QAction('Auto Level', self)
        self.autoLevel.setCheckable(True)
        self.autoLevel.setToolTip('Auto Scale the Bar Height to Fit Data')
        self.autoLevel.triggered.connect(self.setAutoLevel)
        if not self.barHeight:
            self.autoLevel.setChecked(True)

        sizesCheck = QAction('Dimensions', self)
        sizesCheck.setCheckable(True)
        sizesCheck.setToolTip('Change the Bars Dimensions')
        sizesCheck.toggled.connect(self.showBarSliders)

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
        self.fpsSpinBox.setMaximumSize(100, 100)
        self.fpsSpinBox.valueChanged.connect(self.setFrameRate)
        self.fpsSpinBox.setValue(self.frameRate)
        self.fpsSpinBox.setKeyboardTracking(False)
        self.fpsSpinBox.setFocusPolicy(Qt.ClickFocus)

        mainMenu.addMenu(profilesMenu)
        mainMenu.addAction(deviceDialog)
        mainMenu.addAction(FFTAudDialog)
        mainMenu.addAction(scaleDialog)
        mainMenu.addAction(splitCheck)
        mainMenu.addMenu(curvyMenu)
        mainMenu.addMenu(interpMenu)
        mainMenu.addMenu(bufferMenu)
        designMenu.addMenu(colorMenu)
        designMenu.addMenu(lumenMenu)
        designMenu.addAction(gradDialog)
        designMenu.addAction(self.autoLevel)
        designMenu.addAction(sizesCheck)
        designMenu.addAction(outlineCheck)
        designMenu.addAction(cutoutCheck)
        statsMenu.addAction(deadlineCheck)
        statsMenu.addAction(barNumCheck)
        statsMenu.addAction(latencyCheck)
        statsMenu.addAction(dbBarCheck)
        statsMenu.addAction(self.freqsCheck)
        statsMenu.addAction(self.notesCheck)

        menuWidget = QWidget(self)
        menu = QHBoxLayout(menuWidget)

        menu.addWidget(self.mainBar)
        menu.addWidget(self.fpsSpinBox)
        menu.addStretch(10)

        self.setMenuWidget(menuWidget)
        
        self.setWindowFlags(self.windowFlags() & ~Qt.FramelessWindowHint)   # Fixes Windows window bug
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
        self.reverseFFT = 0

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
        self.T1 = mp.Process(target=ReVidia_win.collectData, args=(
            dataTime, self.dataArray, dataArray2, self.dataQ, self.ID, self.audioBuffer, self.split, self.loopback))

        # Create separate process for audio data processing
        self.P1 = mp.Process(target=ReVidia_win.processData, args=(
            self.syncLock, dataTime, self.proTime, self.dataArray, dataArray2, self.proArray, self.proArray2, self.proQ, self.dataQ,
            self.frameRate, self.audioBuffer, self.plotsList, self.split, self.curvyValue, self.interp))

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

            # Resize Data with user's defined height or the data's height
            if not self.barHeight:
                self.dataCap = max(self.barValues)
            else:
                self.dataCap = self.barHeight
            self.barValues = ReVidia_win.rescaleData(self.barValues, self.dataCap, self.size().height())
            self.splitBarValues = ReVidia_win.rescaleData(self.splitBarValues, self.dataCap, self.size().height())

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
        if self.reverseFFT:
            if not hasattr(self, 'waveLoopTime'):
                self.waveLoopTime = time.time()
            waveTime = time.time() - self.waveLoopTime
            self.waveLoopTime = time.time()

            if not hasattr(self, 'waveFile'):
                self.waveFile = ReverseFFT.createFile(self.sampleRate)
                self.oldVolList = []
                self.oldTimes = []
                freqList = ReVidia_win.assignFreq(self.audioBuffer, self.sampleRate, self.plotsList)
                import random
                # Insert a Tiny bit of random to prevent overlap in freq's
                self.waveFreqList = list(map(lambda freq: freq + random.uniform(-0.1, 0.1), freqList))

            self.oldVolList, self.oldTimes = ReverseFFT.start(self.waveFile, self.sampleRate, self.barValues, waveTime,
                                                              self.size().height(), self.oldVolList, self.oldTimes, self.waveFreqList)
        else:
            if hasattr(self, 'waveFile'):
                self.waveFile.close()
                del self.waveFile
                del self.waveLoopTime

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
        if hasattr(self, 'heightSlider'):
            if self.heightSlider.isSliderDown():
                self.setBarHeight()
            else:
                self.heightSlider.setValue(0)

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

        startScale = ReVidia_win.quadBezier(startPoint, midPoint, startCurve, midPointPos)
        endScale = ReVidia_win.quadBezier(midPoint, endPoint, endCurve, self.barsAmt - midPointPos, True)
        plots = startScale + endScale

        self.plotsList = list(map(int, ReVidia_win.dataPlotter(plots, 1, self.audioBuffer // 2)))
        if hasattr(self, 'proQ'):
            self.proQ.put(['plots', self.plotsList])

    def updateBarsAmt(self):
        if hasattr(self, 'barsAmt'):
            self.barsAmt = self.size().width() // self.wholeWidth

            if self.barsAmt > self.audioBuffer:   # Max of buffer to avoid crash
                self.barsAmt = self.audioBuffer
            if self.barsAmt < 2: self.barsAmt = 2   # Min of 2 point to avoid crash

            if self.curvy:
                self.setCurve(self.curvy)

            self.updatePlots()

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
                ySizeV = self.barValues[y]
                ySize = self.size().height() - ySizeV
                painter.drawRect(xPos - self.gapWidth, yPos, self.gapWidth, self.size().height())   # Gap bar

                if self.split:
                    ySplitV = self.splitBarValues[y]
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
                ySize = self.barValues[y]

                if self.split and len(self.splitBarValues) == self.barsAmt:
                    if ySize > viewHeight // 2:
                        ySize = viewHeight // 2
                    ySplitV = self.splitBarValues[y]
                    if ySplitV > viewHeight // 2:
                        ySplitV = viewHeight // 2
                    yPos = (self.size().height() // 2) + ySplitV
                    ySize = ySplitV + ySize

                if self.lumen:
                    color = QColor(barColor)
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

        freqList = ReVidia_win.assignFreq(self.audioBuffer, self.sampleRate, self.plotsList)

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
            notes = ReVidia_win.assignNotes(freqList)

            xSize = self.barWidth + 1
            yTextPos = yPos - ySize
            for note in notes:
                painter.drawText(xPos, yTextPos, xSize, ySize, Qt.AlignCenter, note)
                xPos += self.wholeWidth

    # Draws a dB bar in right corner
    def paintDB(self, event, painter):
        dbValue = ReVidia_win.getDB(self.dataList)

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
                profileList.append(file.replace('.pkl', ''))
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

    def getDevice(self, firstRun):
        # Run device getter on separate Process because the other PA won't start if not done
        devQ = mp.Queue()
        D1 = mp.Process(target=ReVidia_win.deviceNames, args=(devQ,))
        D1.start(), D1.join()
        deviceList = devQ.get()

        device, ok = QInputDialog.getItem(self, "ReVidia", "Select Audio Input Device:", deviceList[0], 0, False)
        if ok and device:
            self.ID = deviceList[1][deviceList[0].index(device)]
            self.sampleRate = deviceList[2][deviceList[0].index(device)]

            if 'Output:' in device:
                self.loopback = True
            else:
                self.loopback = False

            if firstRun: return
            else:
                self.mainQ.put(1), self.mainThread.join()
                self.proQ.put(['kill'])
                self.dataQ.put(['kill'])
                self.startProcesses()

        elif firstRun: sys.exit()

    def getFFTAudDialog(self):
        self.fftDialog = FFTDialog(self)
        self.fftDialog.setGeometry(self.pos().x(), self.pos().y(), 350, 100)
        self.fftDialog.show()

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
        self.curvy = index  # Assign Dict value
        if index:
            window = int(self.barsAmt * index[0])
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
            self.updateBarsAmt()
            self.dataQ.put(['buffer', self.audioBuffer])
            self.proQ.put(['buffer', self.audioBuffer])

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

    def setLumen(self, index):
        self.lumen = index

        for f in self.lumenDict:
            if int(f) != index:
                self.lumenDict[str(f)].setChecked(False)
            else:
                self.lumenDict[str(f)].setChecked(True)

    def getGradDialog(self):
        self.gradDialog = GradientDialog(self)
        self.gradDialog.setMinimumSize(150, 100)
        posX = self.pos().x() + self.size().width() // 2
        self.gradDialog.setGeometry(posX, self.pos().y(), self.size().width() // 2,
                                     self.size().height() // 2)
        self.gradDialog.show()

    def setAutoLevel(self, on):
        if on:
            self.barHeight = 0
        else:
            self.barHeight = self.dataCap

    def showBarSliders(self, on):
        if on:
            if hasattr(self, 'barSizeDock'):
                self.showBarSliders(False)

            self.barWidthText = QLabel(self)
            self.barWidthText.setText('Bar Width ' + str(self.barWidth))
            barWidthSlider = QSlider(Qt.Horizontal, self)
            barWidthSlider.setMinimum(1)
            barWidthSlider.setValue(self.barWidth)
            barWidthSlider.valueChanged.connect(self.setBarSize)

            self.gapWidthText = QLabel(self)
            self.gapWidthText.setText('Gap Width ' + str(self.gapWidth))
            gapWidthSlider = QSlider(Qt.Horizontal, self)
            gapWidthSlider.setValue(self.gapWidth)
            gapWidthSlider.valueChanged.connect(self.setGapSize)


            self.outlineWidthText = QLabel(self)
            self.outlineWidthText.setText('Out Width ' + str(self.outlineSize))
            self.outlineWidthSlider = QSlider(Qt.Horizontal, self)
            self.outlineWidthSlider.setMaximum(50)
            self.outlineWidthSlider.setValue(self.outlineSize)
            self.outlineWidthSlider.valueChanged.connect(self.setOutlineSize)

            self.heightText = QLabel(self)
            self.heightText.setText('Height \n' + str(int(self.dataCap **(1/2))))
            self.heightText.setGeometry(30, 65, 50, 40)
            self.heightSlider = QSlider(Qt.Vertical, self)
            self.heightSlider.setMinimum(-100)
            self.heightSlider.setMaximum(100)
            self.heightSlider.setMinimumSize(0, 150)
            self.heightSlider.setValue(0)
            self.heightSlider.valueChanged.connect(self.setBarHeight)

            dimenWidget = QWidget(self)

            mainLayout = QGridLayout(dimenWidget)
            mainLayout.setHorizontalSpacing(10)
            mainLayout.setVerticalSpacing(5)

            mainLayout.addWidget(self.heightText, 0, 0, 2, 1, Qt.AlignTop)
            mainLayout.addWidget(self.barWidthText, 0, 1, Qt.AlignCenter)
            mainLayout.addWidget(self.gapWidthText, 0, 2, Qt.AlignCenter)
            mainLayout.addWidget(self.outlineWidthText, 0, 3,Qt.AlignCenter)

            mainLayout.addWidget(self.heightSlider, 2, 0, 4, 0)
            mainLayout.addWidget(barWidthSlider, 1, 1)
            mainLayout.addWidget(gapWidthSlider, 1, 2)
            mainLayout.addWidget(self.outlineWidthSlider, 1, 3)

            self.barSizeDock = QDockWidget(self)
            self.barSizeDock.setFeatures(QDockWidget.NoDockWidgetFeatures)
            self.barSizeDock.setTitleBarWidget(QWidget())
            self.barSizeDock.setWidget(dimenWidget)
            self.barSizeDock.move(0, 35)
            self.barSizeDock.show()

        else:
            # Clean up
            self.barSizeDock.close()
            del self.barSizeDock

    def setBarSize(self, value):
        self.barWidth = value
        self.wholeWidth = self.barWidth + self.gapWidth
        self.updateBarsAmt()
        if self.outlineSize > self.barWidth // 2:
            self.setOutlineSize(self.outlineSize)

        self.barWidthText.setText('Bar Width ' + str(self.barWidth))

    def setGapSize(self, value):
        self.gapWidth = value
        self.wholeWidth = self.barWidth + self.gapWidth
        self.updateBarsAmt()

        self.gapWidthText.setText('Gap Width ' + str(self.gapWidth))

    def setOutlineSize(self, value):
        if value <= self.barWidth // 2:
            self.outlineSize = value
        else:
            self.outlineSize = self.barWidth // 2
            self.outlineWidthSlider.setValue(self.outlineSize)

        self.outlineWidthText.setText('Out Width ' + str(self.outlineSize))

    def setBarHeight(self):
        if not self.barHeight:
            self.barHeight = self.dataCap
            self.autoLevel.setChecked(False)

        value = self.heightSlider.value()
        if value > 0:
            value = 1 + value / (self.frameRate * 10)
            if self.barHeight > 1:
                self.barHeight /= value
            else:
                self.barHeight = 1

        elif value < 0:
            value = 1 + -value / (self.frameRate * 10)
            if self.barHeight < 10**10:
                self.barHeight *= value
            else:
                self.barHeight = 10**10

        self.heightText.setText('Height \n' + str(int(self.barHeight**(1/2))))

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

                self.mainBar.hide()
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
                self.mainBar.show()
                self.fpsSpinBox.show()
                self.show()
                self.move(self.oldX, self.oldY)  # Fixes a weird bug with the window
                return

    def mousePressEvent(self, event):
        if event.button() == 2:  # Right click
            self.mouseGrab = [event.x(), event.y()]

    def mouseMoveEvent(self, event):
        if hasattr(self, 'mouseGrab'):
            xPos = event.globalX() - self.mouseGrab[0]
            yPos = event.globalY() - self.mouseGrab[1]
            self.move(xPos, yPos)

    def mouseReleaseEvent(self, event):
        if hasattr(self, 'mouseGrab'):
            del self.mouseGrab

    # Allows to adjust bars height by scrolling on window
    def wheelEvent(self, event):
        mouseDir = event.angleDelta().y()

        if not self.barHeight:
            self.barHeight = self.dataCap
            self.autoLevel.setChecked(False)

        if mouseDir < 0:
            if self.barHeight < 10**10:
                self.barHeight *= 1.5
            else:
                self.barHeight = 10**10
        elif mouseDir > 0:
            if self.barHeight > 1:
                self.barHeight /= 1.5
            else:
                self.barHeight = 1

        if hasattr(self, 'heightText'):
            self.heightText.setText('Height \n' + str(int(self.barHeight**(1/2))))

    def resizeEvent(self, event):
        self.updateBarsAmt()

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


class FFTDialog(QMainWindow):
    def __init__(self, main):
        super(FFTDialog, self).__init__()
        self.setWindowTitle('Reverse FFT')
        self.main = main

        self.intiUI()

    def intiUI(self):
        buttons = QWidget(self)
        layout = QHBoxLayout(buttons)

        self.record = QPushButton('Record', self)
        self.record.setFixedSize(100, 50)
        self.record.setCheckable(True)
        self.record.clicked.connect(self.setRecord)
        layout.addWidget(self.record)

        self.play = QPushButton('Play', self)
        self.play.setFixedSize(100, 50)
        self.play.setCheckable(True)
        self.play.clicked.connect(self.setPlay)
        layout.addWidget(self.play)

        self.setCentralWidget(buttons)

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
        if self.main.reverseFFT:
            self.record.setText('Stopped')
            self.record.setChecked(False)
            self.main.reverseFFT = 0

        if on:
            self.play.setText('Playing')
            import subprocess
            self.player = subprocess.Popen('powershell -windowstyle hidden -c (New-Object Media.SoundPlayer "reverseFFT.wav").PlaySync();')
        else:
            self.play.setText('Stopped')
            self.player.kill()
            del self.player

    def closeEvent(self, event):
        # Cleanup
        self.main.reverseFFT = 0
        if hasattr(self, 'player'):
            self.player.kill()

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
        self.setPalette(self.main.textPalette)
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

        self.midPointSpinBox = QSpinBox()
        self.midPointSpinBox.setRange(0, int(self.main.sampleRate // 2))
        self.midPointSpinBox.setSuffix(' HZ')
        self.midPointSpinBox.setMaximumWidth(90)
        self.midPointSpinBox.setMaximumHeight(20)
        self.midPointSpinBox.valueChanged.connect(self.setMidPoint)
        self.midPointSpinBox.setValue(self.midPoint)
        self.midPointSpinBox.setKeyboardTracking(False)
        self.midPointSpinBox.setFocusPolicy(Qt.ClickFocus)

        self.endPointSpinBox = QSpinBox()
        self.endPointSpinBox.setRange(0, int(self.main.sampleRate // 2))
        self.endPointSpinBox.setSuffix(' HZ')
        self.endPointSpinBox.setMaximumWidth(90)
        self.endPointSpinBox.setMaximumHeight(20)
        self.endPointSpinBox.valueChanged.connect(self.setEndPoint)
        self.endPointSpinBox.setValue(self.endPoint)
        self.endPointSpinBox.setKeyboardTracking(False)
        self.endPointSpinBox.setFocusPolicy(Qt.ClickFocus)

        menuWidget = QWidget(self)
        menu = QHBoxLayout(menuWidget)

        menu.addWidget(mainBar)
        menu.addWidget(self.startPointSpinBox)
        menu.addWidget(self.midPointSpinBox)
        menu.addWidget(self.endPointSpinBox)
        menu.addStretch(10)

        self.setMenuWidget(menuWidget)

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
            self.freqScale = ReVidia_win.realScale(0, (self.main.sampleRate // 2), steps)
        else:
            self.freqScale = ReVidia_win.quadBezier(0, (self.main.sampleRate // 2), 0, (ySize-1), True)

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

        freqList = (ReVidia_win.assignFreq(self.main.audioBuffer, self.main.sampleRate, self.main.plotsList, True))

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
        buttons = QWidget(self)
        layout = QHBoxLayout(buttons)

        self.dirModeCheck = QPushButton('Vertical', self)
        self.dirModeCheck.setCheckable(True)
        self.dirModeCheck.clicked.connect(self.setDirMode)
        layout.addWidget(self.dirModeCheck)

        self.fillModeCheck = QPushButton('Whole', self)
        self.fillModeCheck.setCheckable(True)
        self.fillModeCheck.clicked.connect(self.setFillMode)
        layout.addWidget(self.fillModeCheck)

        clear = QPushButton('Clear', self)
        clear.clicked.connect(self.runClear)
        layout.addWidget(clear)

        self.enabled = QPushButton('Enabled', self)
        self.enabled.setCheckable(True)
        self.enabled.clicked.connect(self.setEnabled)
        self.enabled.setChecked(True)
        layout.addWidget(self.enabled)

        layout.addStretch(10)

        self.setMenuWidget(buttons)

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
        self.GH = self.size().height()     # Graphics Height

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
