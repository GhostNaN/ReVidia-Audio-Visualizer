#!venv/bin/python
# -*- coding: utf-8 -*-

import sys
import time
import queue
import threading as th
from ReVidiaQT import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


# Create the self object and main window
class ReVidiaMain(QMainWindow):
    def __init__(self, parent=None):
        super(ReVidiaMain, self).__init__(parent)

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
        self.frameRate = 125
        self.split = 0
        self.curvy = 0
        self.interp = 2
        self.audioFrames = 4096
        self.backgroundColor = QColor(50, 50, 50, 255)
        self.barColor = QColor(255, 255, 255, 255)      # R, G, B, Alpha 0-255
        self.outlineColor = QColor(0, 0, 0)
        self.lumen = 0
        self.checkRainbow = 0
        self.textPalette = QPalette()
        self.barWidth = 14
        self.gapWidth = 6
        self.outlineThick = 0
        self.barHeight = 0.001
        self.wholeWidth = self.barWidth + self.gapWidth
        self.outline = 0
        self.cutout = 0
        self.checkFreq = 0
        self.checkNotes = 0
        self.checkLateNum = 0
        self.checkBarNum = 0
        self.checkLatency = 0
        self.checkDB = 0

        self.initUI()

    # Setup main window
    def initUI(self):
        self.setWindowIcon(QIcon('docs/REV.png'))
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.setAttribute(Qt.WA_TranslucentBackground, True)    # Initial background is transparent
        self.setTextPalette()
        self.PA = getPA()       # Initialize PortAudio
        self.getDevice(True)    # Get Device before starting

        # Setup menu bar
        mainBar = self.menuBar()
        mainMenu = mainBar.addMenu('Main')
        mainMenu.setToolTipsVisible(True)
        designMenu = mainBar.addMenu('Design')
        designMenu.setToolTipsVisible(True)
        statsMenu = mainBar.addMenu('Stats')
        statsMenu.setToolTipsVisible(True)

        viewDevices = QAction('Device', self)
        viewDevices.setToolTip('Select Audio Device')
        viewDevices.triggered.connect(self.getDevice)

        split = QAction('Split Audio', self)
        split.setCheckable(True)
        split.setChecked(self.split)
        split.setToolTip('Toggle to Split Audio Channels')
        split.toggled.connect(self.setSplit)

        curvyMenu = QMenu('Curviness', self)
        curvyMenu.setToolTip('Set How Much the Bars Curve')
        curvySettings = ['No Curves', 'Sharp', 'Mid', 'Loose']
        curveList = [0, 5, 9, 17]
        self.curvyDict = {}
        for f in range(4):
            curve = curveList[f]
            self.curvyDict[str(curve)] = QAction(curvySettings[f], self)
            self.curvyDict[str(curve)].setCheckable(True)
            self.curvyDict[str(curve)].triggered.connect(lambda checked, index=curve: self.setCurve(index))
            curvyMenu.addAction(self.curvyDict[str(curve)])
        self.curvyDict[str(self.curvy)].setChecked(True)

        interpMenu = QMenu('Interpolation', self)
        interpMenu.setToolTip('Set Interp Amount (Smoothing)')
        interpSettings = ['No Interpolation', 'Low', 'Mid', 'High']
        interp = 0
        self.interpDict = {}
        for f in range(4):
            self.interpDict[str(interp)] = QAction(interpSettings[f], self)
            self.interpDict[str(interp)].setCheckable(True)
            self.interpDict[str(interp)].triggered.connect(lambda checked, index=interp: self.setInterp(index))
            interpMenu.addAction(self.interpDict[str(interp)])
            interp += 1
        self.interpDict[str(self.interp)].setChecked(True)

        frames = QMenu('Frames', self)
        frames.setToolTip('Set the Audio Frame Rate')
        audioRate = 1024
        self.audioFramesDict = {}
        for f in range(4):
            self.audioFramesDict[str(audioRate)] = QAction(str(audioRate), self)
            self.audioFramesDict[str(audioRate)].setCheckable(True)
            self.audioFramesDict[str(audioRate)].triggered.connect(lambda checked, index=audioRate: self.setFrames(index))
            frames.addAction(self.audioFramesDict[str(audioRate)])
            audioRate *= 2
        self.audioFramesDict[str(self.audioFrames)].setChecked(True)

        color = QMenu('Color', self)
        color.setToolTip('Select Colors and Transparency')
        barColor = QAction('Bar Color', self)
        barColor.triggered.connect(self.setBarColor)
        backColor = QAction('Background Color', self)
        backColor.triggered.connect(self.setBackgroundColor)
        outColor = QAction('Outline Color', self)
        outColor.triggered.connect(self.setOutlineColor)
        rainbowColor = QAction('Rainbow', self)
        rainbowColor.setCheckable(True)
        rainbowColor.triggered.connect(self.setRainbow)

        color.addAction(barColor)
        color.addAction(backColor)
        color.addAction(outColor)
        color.addAction(rainbowColor)

        barSize = QAction('Dimensions', self)
        barSize.setCheckable(True)
        barSize.setToolTip('Change the Bars Dimensions')
        barSize.toggled.connect(self.showBarSize)

        lumen = QAction('Illuminate', self)
        lumen.setCheckable(True)
        lumen.setToolTip('Change the Bars Alpha Scale')
        lumen.triggered.connect(self.showLumen)

        outline = QAction('Outline Only', self)
        outline.setCheckable(True)
        outline.setChecked(self.outline)
        outline.setToolTip('Toggle Outline/Turn Off Fill')
        outline.toggled.connect(self.setOutline)

        cutout = QAction('Cutout', self)
        cutout.setCheckable(True)
        cutout.setChecked(self.cutout)
        cutout.setToolTip('Toggle to Cutout Background with Bars')
        cutout.toggled.connect(self.setCutout)

        freq = QAction('Frequencies', self)
        freq.setCheckable(True)
        freq.setChecked(self.checkFreq)
        freq.setToolTip('Show Each Bar\'s Frequency')
        freq.toggled.connect(self.showFreq)

        notes = QAction('Notes', self)
        notes.setCheckable(True)
        notes.setChecked(self.checkNotes)
        notes.setToolTip('Guesses the Notes')
        notes.toggled.connect(self.showNotes)

        lateNum = QAction('Late Frames', self)
        lateNum.setCheckable(True)
        lateNum.setChecked(self.checkLateNum)
        lateNum.setToolTip('Display Amount of Late Video Frames')
        lateNum.toggled.connect(self.showLateFrames)

        barNum = QAction('Bars', self)
        barNum.setCheckable(True)
        barNum.setChecked(self.checkBarNum)
        barNum.setToolTip('Display Amount of Bars')
        barNum.toggled.connect(self.showBarNum)

        latNum = QAction('Latency', self)
        latNum.setCheckable(True)
        latNum.setChecked(self.checkLatency)
        latNum.setToolTip('Display Latency Between Display and Audio')
        latNum.toggled.connect(self.showLatency)

        dbBar = QAction('dB Bar', self)
        dbBar.setCheckable(True)
        dbBar.setChecked(self.checkDB)
        dbBar.setToolTip('Display dB Bar Indicating Volume')
        dbBar.toggled.connect(self.showDB)

        self.fpsSpinBox = QSpinBox()
        self.fpsSpinBox.setRange(1, 999)
        self.fpsSpinBox.setSuffix(' FPS')
        self.fpsSpinBox.setMaximumWidth(70)
        self.fpsSpinBox.setMaximumHeight(20)
        self.fpsSpinBox.valueChanged[int].connect(self.setFPS)
        self.fpsSpinBox.setValue(self.frameRate)
        self.fpsSpinBox.setKeyboardTracking(False)
        self.fpsSpinBox.setFocusPolicy(Qt.ClickFocus)
        fpsDock = QDockWidget(self)
        fpsDock.move(150, -20)
        fpsDock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        fpsDock.setWidget(self.fpsSpinBox)
        fpsDock.show()

        mainMenu.addAction(viewDevices)
        mainMenu.addAction(split)
        mainMenu.addMenu(curvyMenu)
        mainMenu.addMenu(interpMenu)
        mainMenu.addMenu(frames)
        designMenu.addMenu(color)
        designMenu.addAction(barSize)
        designMenu.addAction(lumen)
        designMenu.addAction(outline)
        designMenu.addAction(cutout)
        statsMenu.addAction(freq)
        statsMenu.addAction(notes)
        statsMenu.addAction(lateNum)
        statsMenu.addAction(barNum)
        statsMenu.addAction(latNum)
        statsMenu.addAction(dbBar)

        self.show()
        self.startStream()

    # Audio Data Collection
    def startStream(self):
        self.sampleRate = sampleRate(self.PA, self.ID)
        self.stream = startStream(self.PA, self.ID, self.sampleRate)
        self.startVidia()

    # Main loop of ReVidia
    def startVidia(self):
        # Create separate thread for audio data collection
        self.Q1 = queue.SimpleQueue()
        self.Q2 = queue.SimpleQueue()
        self.T1 = th.Thread(target=audioData, args=(self.Q1, self.Q2, self.stream, self.audioFrames, self.split))
        self.T1.daemon = True
        self.T1.start()

        self.dataList = []
        self.barValues = [0]
        self.splitBarValues = [0]

        while True:
            timeD = time.time()
            self.widthSize = self.size().width() // self.wholeWidth

            self.updateObjects()
            QApplication.processEvents()  # This is NEEDED to stop gui freezing
            self.prePaint()
            self.repaint()

            self.latency = round((time.time() - timeD) * 1000)

            # Frame Time Delay Scalar
            delay = (1 / self.frameRate)
            frameTime = delay - (time.time() - timeD)
            if frameTime < 0:
                frameTime = 0
                if self.checkLateNum:
                    self.lateFrames += 1
            time.sleep(frameTime)

    # Gets audio devices
    def getDevice(self, firstRun):
        deviceList = (deviceName(self.PA))
        device, ok = QInputDialog.getItem(self, "ReVidia", "Select Audio Input Device:", deviceList[0], 0, False)
        if ok and device:
            self.ID = deviceList[1][deviceList[0].index(device)]
            if firstRun: return
            else:
                self.Q1.put(1), self.Q1.put(1)  # Trip breaker to stop data collection
                self.T1.join()
                self.PA.terminate()     # Sacrifice PortAudio for a new device
                self.PA = getPA()       # Initialize PortAudio
                self.startStream()

    # Updates objects during loop
    def updateObjects(self):
        if self.checkLateNum:
            self.showLateFrames(1)
        if self.checkBarNum:
            self.showBarNum(1)
        if self.checkLatency:
            self.showLatency(1)
        if self.checkRainbow:
            self.setRainbow(1)

    # Sets the text color to better see it
    def setTextPalette(self):
        if self.backgroundColor.value() <= 128:
            self.textPalette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        else:
            self.textPalette.setColor(QPalette.WindowText, QColor(0, 0, 0))

        self.setPalette(self.textPalette)

    # Creates the bars for painter to draw
    def prePaint(self):
        # Get audio data
        while len(self.dataList) < self.audioFrames:
            self.dataList = self.Q1.get()
            if self.split:
                self.rightDataList = self.Q2.get()

        # Process audio data
        oldBarValues = self.barValues
        self.barValues = processData(self.dataList, self.widthSize, self.sampleRate, self.curvy)
        oldSplitValues = self.splitBarValues
        if self.split:
            self.splitBarValues = processData(self.rightDataList, self.widthSize, self.sampleRate, self.curvy)

        # Smooth audio data using past averages
        if self.interp:
            if not hasattr(self, 'oldList'):
                self.oldList = []
                self.oldSplitList = []
            if len(self.oldList) <= self.interp:
                self.oldList.append(list(oldBarValues))
                if self.split:
                    self.oldSplitList.append(list(oldSplitValues))
            while len(self.oldList) > self.interp:
                del (self.oldList[0])
            if self.split:
                while len(self.oldSplitList) > self.interp:
                    del (self.oldSplitList[0])

            self.barValues = interpData(self.barValues, self.oldList)
            if self.split:
                self.splitBarValues = interpData(self.splitBarValues, self.oldSplitList)

    # Setup painter object
    def paintEvent(self, event):
        if not hasattr(self, 'barValues'):
            return
        if self.split:
            if not hasattr(self, 'splitBarValues'):
                return
        painter = QPainter(self)
        painter.setPen(QPen(Qt.NoPen))  # Removes pen
        self.paintBackground(event, painter)
        if not self.cutout:
            self.paintBars(event, painter)
        if self.checkFreq or self.checkNotes:
            self.paintFreq(event, painter)
        if self.checkDB:
            self.paintDB(event, painter)
        painter.end()

    # Draw background
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

    # Draw bars
    def paintBars(self, event, painter):
        ySizeList = []
        yPosList = []
        xSize = self.barWidth
        xPos = (self.gapWidth // 2)
        yPos = self.size().height()
        viewHeight = self.size().height()
        if self.lumen:
            lumReigen = 255 / (viewHeight * (self.lumen / 100))

        painter.setBrush(self.barColor)

        for y in range(len(self.barValues)):
            ySize = int(self.barValues[y] * self.barHeight)

            if self.lumen:
                color = QColor(self.barColor)
                lumBright = int(ySize * lumReigen)
                if lumBright > 255: lumBright = 255
                color.setAlpha(lumBright)
                painter.setBrush(color)  # Fill of bar color

            if self.split:
                if ySize > viewHeight // 2:
                    ySize = viewHeight // 2
                ySplitV = int(self.splitBarValues[y] * self.barHeight)
                if ySplitV > viewHeight // 2:
                    ySplitV = viewHeight // 2
                yPos = (self.size().height() // 2) + ySplitV
                ySize = ySplitV + ySize

            if ySize > viewHeight:
                ySize = viewHeight
            if not self.outline:
                painter.drawRect(xPos, yPos, xSize, -ySize)

            xPos += self.wholeWidth
            if self.outlineThick:
                ySizeList.append(ySize)
                yPosList.append(yPos)

        if self.outlineThick:
            xPos = (self.gapWidth // 2)

            painter.setBrush(self.outlineColor)  # Fill of outline color
            for y in range(len(self.barValues)):
                ySize = ySizeList[y]
                yPos = yPosList[y]
                if ySize > 0:    # Hack way of making outline without the (Slow QPen)
                    painter.drawRect(xPos, yPos, self.outlineThick, -ySize)  # Left
                    painter.drawRect(xPos, yPos-ySize, self.barWidth,  self.outlineThick)  # Top
                    painter.drawRect(xPos + self.barWidth, yPos-ySize, -self.outlineThick, ySize)  # Right
                    painter.drawRect(xPos, yPos, self.barWidth, -self.outlineThick)  # Bottom

                xPos += self.wholeWidth

    # Draw frequency plot
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
        fontSize = self.barWidth - (self.outlineThick * 2) - 1
        if fontSize < 1: fontSize = 1
        font.setPixelSize(fontSize)
        painter.setFont(font)

        freqList = assignFreq(self.audioFrames, self.sampleRate, self.widthSize)

        # Paint frequency plot
        if self.checkFreq:
            xSize = fontSize
            ySize = int(fontSize * 1.5)
            xPos = self.gapWidth // 2
            yPos = self.size().height()
            for freq in freqList:
                freq = round(freq)

                digits = 0
                number = freq
                if number == 0:
                    digits = 1
                while number > 0:
                    number //= 10
                    digits += 1
                yTextSize = ySize * digits
                yTextPos = yPos - ((digits * ySize) - digits)
                painter.drawText(xPos, yTextPos, xSize, yTextSize, Qt.AlignHCenter | Qt.TextWrapAnywhere, str(freq))
                xPos += self.wholeWidth

        # Instead of painting freq, give a approximation of notes
        elif self.checkNotes:
            notes = assignNotes(freqList)
            xSize = self.barWidth + 1
            ySize = xSize + 5
            xPos = self.gapWidth // 2
            yPos = self.size().height() - self.barWidth - 5
            for note in notes:
                painter.drawText(xPos, yPos, xSize, ySize, Qt.AlignHCenter, note)
                xPos += self.wholeWidth

    # Draws a dB bar in right corner
    def paintDB(self, event, painter):
        if len(self.dataList) >= self.audioFrames:
            dbValue = getDB(self.dataList)

            painter.setPen(self.textPalette.color(QPalette.WindowText))
            painter.setFont(QApplication.font())
            if dbValue > -1.0:
                painter.setPen(QColor(255, 30, 30))
            xPos = self.size().width() - 35
            yPos = 145

            painter.drawText(xPos, yPos, str(dbValue))

            if dbValue == -float('Inf'):
                return
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

    # Toggle for audio split setting
    def setSplit(self, on):
        if on:
            self.split = 1
        else:
            self.split = 0

        self.Q1.put(1), self.Q1.put(1)  # Trip breaker to stop data collection
        self.T1.join()
        self.startVidia()

    # Sets how wide the curves selected
    def setCurve(self, index):
        self.curvy = index

        for f in self.curvyDict:
            if int(f) != index:
                self.curvyDict[str(f)].setChecked(False)

    # Sets amount of Frames Per Sec selected
    def setFPS(self, value):
        self.frameRate = value

    # Sets amount of interpolation selected
    def setInterp(self, index):
        self.interp = index

        for f in self.interpDict:
            if int(f) != index:
                self.interpDict[str(f)].setChecked(False)

    # Sets amount of audio frames selected
    def setFrames(self, index):
        self.audioFrames = index

        for f in self.audioFramesDict:
            if int(f) != index:
                self.audioFramesDict[str(f)].setChecked(False)
        self.Q1.put(1), self.Q1.put(1)  # Trip breaker to stop data collection
        self.T1.join()
        self.startVidia()

    # Bar color selection
    def setBarColor(self):
        self.barColor = QColorDialog.getColor(self.barColor,None,None,QColorDialog.ShowAlphaChannel)

    # Background color selection
    def setBackgroundColor(self):
        self.backgroundColor = QColorDialog.getColor(self.backgroundColor,None,None,QColorDialog.ShowAlphaChannel)
        self.setTextPalette()

    # Outline color selection
    def setOutlineColor(self):
        self.outlineColor = QColorDialog.getColor(self.outlineColor, None, None, QColorDialog.ShowAlphaChannel)

    # Creates a rainbow effect with the bars color
    def setRainbow(self, on):
        if not self.checkRainbow:
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

    # Shows sliders for all of bars dimensions
    def showBarSize(self, on):
        if on:
            self.showBarText = QLabel(self)
            self.showBarText.setText('Bar Width')
            self.showBarText.setGeometry(5, 25, 75, 20)
            self.showBarText.show()
            self.showBarWidth = QSlider(Qt.Horizontal, self)
            self.showBarWidth.setMinimum(1)
            self.showBarWidth.setValue(self.barWidth)
            self.showBarWidth.setGeometry(0, 40, 100, 30)
            self.showBarWidth.valueChanged[int].connect(self.setBarSize)
            self.showBarWidth.show()
            self.showBarInt()

            self.showGapText = QLabel(self)
            self.showGapText.setText('Gap Width')
            self.showGapText.setGeometry(105, 25, 75, 20)
            self.showGapText.show()
            self.showGapWidth = QSlider(Qt.Horizontal, self)
            self.showGapWidth.setValue(self.gapWidth)
            self.showGapWidth.setGeometry(100, 40, 100, 30)
            self.showGapWidth.valueChanged[int].connect(self.setGapSize)
            self.showGapWidth.show()
            self.showGapInt()

            self.showOutlineText = QLabel(self)
            self.showOutlineText.setText('Out Width')
            self.showOutlineText.setGeometry(205, 25, 75, 20)
            self.showOutlineText.show()
            self.showOutlineThick = QSlider(Qt.Horizontal, self)
            self.showOutlineThick.setMaximum(50)
            self.showOutlineThick.setValue(self.outlineThick)
            self.showOutlineThick.setGeometry(200, 40, 100, 30)
            self.showOutlineThick.valueChanged[int].connect(self.setOutlineSize)
            self.showOutlineThick.show()
            self.showOutlineInt()

            self.showHeightText = QLabel(self)
            self.showHeightText.setText('Height')
            self.showHeightText.setGeometry(30, 65, 50, 20)
            self.showHeightText.show()
            self.showHeightScroll = QSlider(Qt.Vertical, self)
            self.showHeightScroll.setMinimum(-100)
            self.showHeightScroll.setMaximum(100)
            self.showHeightScroll.setValue(0)
            self.showHeightScroll.setGeometry(0, 70, 30, 150)
            self.showHeightScroll.valueChanged.connect(self.setBarHeight)
            self.showHeightScroll.show()
            self.showHeightInt()
        else:
            self.showBarWidth.close()
            self.showGapWidth.close()
            self.showOutlineThick.close()
            self.showHeightScroll.close()
            self.showBarText.close()
            self.showGapText.close()
            self.showOutlineText.close()
            self.showHeightText.close()

            self.showBarTextInt.close()
            self.showGapTextInt.close()
            self.showOutlineTextInt.close()
            self.showHeightTextInt.close()

    # Sets bar width selected
    def setBarSize(self, value):
        self.barWidth = value
        self.wholeWidth = self.barWidth + self.gapWidth
        if self.outlineThick > self.barWidth // 2:
            self.setOutlineSize(self.outlineThick)
        self.showBarInt()

    # Show bar current int
    def showBarInt(self):
        if hasattr(self, 'showBarTextInt'):
            self.showBarTextInt.close()

        self.showBarTextInt = QLabel(self)
        self.showBarTextInt.setText(str(self.barWidth))
        self.showBarTextInt.setGeometry(75, 25, 100, 20)
        self.showBarTextInt.show()

    # Sets gap between bars selected
    def setGapSize(self, value):
        self.gapWidth = value
        self.wholeWidth = self.barWidth + self.gapWidth
        self.showGapInt()

    # Show gap current int
    def showGapInt(self):
        if hasattr(self, 'showGapTextInt'):
            self.showGapTextInt.close()

        self.showGapTextInt = QLabel(self)
        self.showGapTextInt.setText(str(self.gapWidth))
        self.showGapTextInt.setGeometry(175, 25, 100, 20)
        self.showGapTextInt.show()

    # Sets outline size selected
    def setOutlineSize(self, value):
        if value <= self.barWidth // 2:
            self.outlineThick = value
        else:
            self.outlineThick = self.barWidth // 2
            self.showOutlineThick.setValue(self.outlineThick)
        self.showOutlineInt()

    # Show outline current int
    def showOutlineInt(self):
        if hasattr(self, 'showOutlineTextInt'):
            self.showOutlineTextInt.close()

        self.showOutlineTextInt = QLabel(self)
        self.showOutlineTextInt.setText(str(self.outlineThick))
        self.showOutlineTextInt.setGeometry(275, 25, 100, 20)
        self.showOutlineTextInt.show()

    # Sets bar height selected
    def setBarHeight(self):
        while self.showHeightScroll.isSliderDown():
            QApplication.processEvents()  # This is NEEDED to stop gui freezing
            self.repaint()

            value = self.showHeightScroll.value()
            if value > 0:
                value = 1 + value / 10000
                if self.barHeight < 10:
                    self.barHeight *= value
            elif value < 0:
                value = 1 + -value / 10000
                if self.barHeight > 0.000001:
                    self.barHeight /= value

            self.showHeightInt()
        self.showHeightScroll.setValue(0)

    # Show height current int
    def showHeightInt(self):
        if hasattr(self, 'showHeightTextInt'):
            self.showHeightTextInt.close()

        self.showHeightTextInt = QLabel(self)
        self.showHeightTextInt.setText(str(round(self.barHeight * 1000, 2)))
        self.showHeightTextInt.setGeometry(30, 85, 45, 20)
        self.showHeightTextInt.show()

    # Shows the Light Limit scroll bar
    def showLumen(self, on):
        if on:
            self.showLumenText = QLabel(self)
            self.showLumenText.setText('Light Limit')
            self.showLumenText.setGeometry(30, 235, 75, 20)
            self.showLumenText.show()
            self.lumenScroll = QSlider(Qt.Vertical, self)
            self.lumenScroll.setMaximum(100)
            self.lumenScroll.setValue(self.lumen)
            self.lumenScroll.setGeometry(0, 240, 30, 100)
            self.lumenScroll.valueChanged[int].connect(self.setLumen)
            self.lumenScroll.show()
            self.showLumenInt()
        else:
            self.showLumenText.close()
            self.lumenScroll.close()

            self.showLumenTextInt.close()

    # Sets Light Limit selected
    def setLumen(self, value):
        self.lumen = value
        self.showLumenInt()

    # Shows current lumen int
    def showLumenInt(self):
        if hasattr(self, 'showLumenTextInt'):
            self.showLumenTextInt.close()

        self.showLumenTextInt = QLabel(self)
        self.showLumenTextInt.setText(str(self.lumen) + '%')
        self.showLumenTextInt.setGeometry(30, 255, 50, 20)
        self.showLumenTextInt.show()

    # Sets bars outline only
    def setOutline(self, on):
        if on:
            self.outline = 1
        else:
            self.outline = 0

    # Sets bars to cut out background instead of drawn
    def setCutout(self, on):
        if on:
            self.cutout = 1
        else:
            self.cutout = 0

    # Sets if to show the bars frequency plot
    def showFreq(self, on):
        if on:
            self.checkFreq = 1
            self.checkNotes = 0
        else:
            self.checkFreq = 0

    # Show estimation of where notes are
    def showNotes(self, on):
        if on:
            self.checkNotes = 1
            self.checkFreq = 0
        else:
            self.checkNotes = 0
    
    # Show how many frames fail to meet frame time set
    def showLateFrames(self, on):
        if hasattr(self, 'showLateNumText'):
            self.showLateNumText.close()
        else:
            self.showLateNumText = QLabel(self)
            self.lateFrames = 0
        if on:
            self.checkLateNum = 1

            self.showLateNumText.setText(str(self.lateFrames) + ' Late')
            digits = 0
            number = self.lateFrames
            if number == 0:
                digits = 1
            while number > 0:
                number //= 10
                digits += 1
            lateNumPos = (self.size().width()//2) - 80 - (digits * 8)
            self.showLateNumText.setGeometry(lateNumPos, 15, 100, 30)
            self.showLateNumText.show()
        else:
            self.checkLateNum = 0
            self.showLateNumText.close()

    # Shows the amount of bars on screen
    def showBarNum(self, on):
        if hasattr(self, 'showBarNumText'):
            self.showBarNumText.close()
        else:
            self.showBarNumText = QLabel(self)
        if on:
            self.checkBarNum = 1

            if self.widthSize > (self.audioFrames // 4):
                self.widthSize = self.audioFrames // 4
            self.showBarNumText.setText(str(self.widthSize) + ' Bars')
            barNumPos = (self.size().width()//2) - 50
            self.showBarNumText.setGeometry(barNumPos, 15, 75, 30)
            self.showBarNumText.setAlignment(Qt.AlignCenter)
            self.showBarNumText.show()
        else:
            self.checkBarNum = 0
            self.showBarNumText.close()

    # Shows latency in milliseconds between the audio and bars being drawn
    def showLatency(self, on):
        if hasattr(self, 'showLatencyNum'):
            self.showLatencyNum.close()
        else:
            self.showLatencyNum = QLabel(self)
            self.latency = 0
        if on:
            self.checkLatency = 1

            self.showLatencyNum.setText(str(self.latency) + ' ms')
            latPos = (self.size().width()//2) + 30
            self.showLatencyNum.setGeometry(latPos, 15, 100, 30)
            self.showLatencyNum.show()
        else:
            self.checkLatency = 0
            self.showLatencyNum.close()

    # Toggle for showing dB bar
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
                oldY = self.y()
                self.setWindowFlags(Qt.FramelessWindowHint)
                self.show()
                self.move(self.x(), oldY + 1)  # Fixes a weird bug with the window
                self.move(self.x(), oldY)
                return
            if self.menuToggle == 2:
                self.menuToggle = 0
                oldY = self.y()
                self.setWindowFlags(self.windowFlags() & ~Qt.FramelessWindowHint)
                self.menuBar().show()
                self.fpsSpinBox.show()
                self.show()
                self.move(self.x() + 1, oldY + 1)  # Fixes a weird bug with the window
                self.move(self.x(), oldY)
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

    # Makes sure the window isn't running in the background after closing
    def closeEvent(self, event):
        sys.exit()


# Starts program
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ReVidiaMain()
