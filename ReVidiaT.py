#!venv/bin/python
# -*- coding: utf-8 -*-
import ReVidia
import os
import time
import signal
import curses
import subprocess
import multiprocessing as mp


class ReVidiaTerm():
    def __init__(self):
        super(ReVidiaTerm, self).__init__()
        signal.signal(signal.SIGINT, self.killEvent)

        self.slices = 8     # Slices of chars
        self.pointsList = [0, 1, 1000, 0.66, 1, 12000]
        self.split = 0
        self.curvy = 0
        self.interp = 4
        self.audioBuffer = 4096
        self.lumen = 0
        self.stars = {}
        self.gradient = 0
        self.checkRainbow = 0
        self.plotWidth = 2
        self.gapWidth = 1
        self.dataCap = 0
        self.wholeWidth = self.plotWidth + self.gapWidth
        self.checkStats = 0
        self.checkFreq = 0
        self.checkNotes = 0
        self.frameRate = 100

        self.curveList = [0, (0.05, 3), (0.15, 3), (0.30, 3), (1, 3)]  # [0, (5,3), (11,3), (23,3), (43,3)]
        self.interpList = [0, 4, 8, 16, 32]
        self.audioBufferList = [1024, 2048, 4096, 8096]
        
        self.getDevice()
        self.starterVars()
        self.updateSize()
        self.updateStack()
        self.startProcesses()

    def starterVars(self):
        # Define placeholder stater variables
        self.width = 1
        self.height = 1
        self.plotValues = [0]
        self.plotSplitValues = [0]
        self.dataList = [0]
        self.delay = 0
        self.frames = 0
        self.paintBusy = 0
        self.paintTime = 0
        self.paintDelay = (1 / self.frameRate)
        self.loopTime = 0
        self.latency = 0
        self.latePercent = 0

    def startProcesses(self):
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
            self.frameRate, self.audioBuffer, self.plotsList, self.split, self.curvy, self.interp))

        self.T1.daemon = True
        self.P1.daemon = True
        self.T1.start()
        self.P1.start()

        self.mainLoop()
        
    def mainLoop(self):
        os.system('tput civis') # Makes cursor invisible
        timer = time.time()
        while True:
            # Gets the real frametime for time sensitive objects
            self.loopTime = time.time() - timer
            timer = time.time()

            # Gets final results from processing
            self.delay = self.proTime.value
            plotsData = self.proArray[:self.plotsAmt]
            splitPlotData = self.proArray2[:self.plotsAmt]
            if self.checkStats:
                self.dataList = self.dataArray[:self.audioBuffer]

            # Resize Data with user's defined height or the data's height Half slices
            self.plotValues = ReVidia.rescaleData(plotsData, self.dataCap, self.height * self.slices)
            self.plotSplitValues = ReVidia.rescaleData(splitPlotData, self.dataCap, self.height * self.slices)

            if not self.P1.is_alive():
                print('RIP Audio Processor, shutting down.')
                break
            if not self.T1.is_alive():
                print('RIP Audio Data Collector, shutting down.')
                break

            try:  # Avoid Crash
                self.syncLock.release()  # Start processing next frame
            except: pass

            self.printBars()
            if self.checkStats:
                self.printStats()

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

            self.checkInput()
            self.updateSize()

            if self.mainQ.qsize() > 0:
                break
    
    def updateSize(self):
        oldWidth = self.width
        oldHeight = self.height
        consoleY, consoleX = subprocess.check_output(['stty', 'size']).decode().split()
        self.width = int(consoleX)
        self.height = int(consoleY)
        
        if (oldWidth != self.width) or (oldHeight != self.height):
            self.updateStack()
        
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
        self.plotsAmt = self.width // self.wholeWidth

        if self.plotsAmt > self.audioBuffer:  # Max of buffer to avoid crash
            self.plotsAmt = self.audioBuffer
        if self.plotsAmt < 2: self.plotsAmt = 2  # Min of 2 point to avoid crash

        if self.curvy:
            window = int(self.plotsAmt * self.curvy[0])
            if (window % 2) == 0: window += 1
            if window < 5: window = 5
            self.curvyValue = (window, self.curvy[1])  # Only used to init process

            if hasattr(self, 'proQ'):
                self.proQ.put(['curvy', self.curvyValue])

    def updateFreqList(self):
        # Assigns frequencies locations based on plots
        freq = self.sampleRate / self.audioBuffer
        self.freqList = list(map(lambda plot: plot * freq, self.plotsList))

    def printBars(self):
        blockList = ['\u2581', '\u2582', '\u2583', '\u2584', '\u2585', '\u2586', '\u2587']

        ceiling = self.height * self.slices
        for y in range(self.height):
            limit = ceiling - (y * self.slices)
            printBarLine = []
            for barValue in self.plotValues:
                if limit <= barValue:   # Full
                    printBarLine.append('\u2588' * self.plotWidth)
                elif (limit-self.slices) < barValue:   # Part
                    block = barValue % self.slices
                    char = blockList[block-1]
                    printBarLine.append(char * self.plotWidth)
                else:   # Empty
                    printBarLine.append(' ' * self.plotWidth)
            if (y * self.slices) < (ceiling - self.slices):
                print((' ' * self.gapWidth).join(printBarLine))
            else:
               print((' ' * self.gapWidth).join(printBarLine), end='\r')

    def printStats(self):
        # Frame Counter to scale timings
        if self.frames < 10000:
            self.frames += 1
        else:
            self.frames = 0

        block = self.frameRate // 10
        if block < 1: block = 1
        if self.frames % block == 0:
            self.latency = str(round(((time.time() - self.delay) * 1000))) + 'ms'
            self.latePercent = str(round(((1 / self.frameRate) / self.loopTime) * 100)) + '%'
            
        barsNum = str(self.plotsAmt)
        if self.dataCap:
            dataCap = str(int(self.dataCap**(1/2)))
        else:
            dataCap = 'Auto'
        rawdbValue = ReVidia.getDB(self.audioPeak.value)
        if rawdbValue == -float('Inf'): 
            dbValue = '-Inf' + 'db'
        else:
            dbValue = str(round(rawdbValue, 1)) + 'db'
        
        print('')
        print('Latency', 'Bars', 'Height', 'Volume', 'Deadline', sep='\t')
        print(self.latency, barsNum, dataCap, dbValue, self.latePercent, sep='\t')

    def getDevice(self, pulseAudio=False):
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

        deviceNames = defaultList + deviceList[0]
        if 'Input: revidia_capture - ALSA' in deviceNames:  # Hide custom ALSA device
            deviceNames.remove('Input: revidia_capture - ALSA')

        if not pulseAudio:
            import os
            os.system('clear')
            for i in range(len(deviceNames)):
                print(str([i]) + ' ' + deviceNames[i])
            select = int(input('Select Audio Device ID:'))
            device = deviceNames[select]
        else:   # Auto select PulseAudio
            device = 'Input: revidia_capture - ALSA'
            ok = 1

        if device:
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
                self.getDevice(True)
    
    def checkInput(self):
        # Controls ReVidia with character inputs
        def getInput(win):
            win.nodelay(True)
            try:
                key = win.getkey()
                return key
            except Exception:
                pass  # No input

        key = curses.wrapper(getInput)
        # Matching keys, I wish Python had Switch Cases
        if key:
            if key == 't':  # Decrease Data Cap
                if not self.dataCap:
                    self.dataCap = max(self.proArray[:self.plotsAmt])

                if self.dataCap > 1:
                    self.dataCap /= 1.5
                else:
                    self.dataCap = 10
            elif key == 'g':  # Increase Data Cap
                if not self.dataCap:
                    self.dataCap = max(self.proArray[:self.plotsAmt])

                if self.dataCap < 10 ** 10:
                    self.dataCap *= 1.5
                else:
                    self.dataCap = 10 ** 10

            elif key == 'i':  # Check Stats
                if self.checkStats:
                    self.checkStats = 0
                else:
                    self.checkStats = 1

            elif key == 'e':  # Decrease Plot Thickness
                if self.plotWidth > 1:
                    self.plotWidth -= 1

                self.wholeWidth = self.plotWidth + self.gapWidth
                self.updateStack()
            elif key == 'r':  # Increase Plot Thickness
                if self.plotWidth < 25:
                    self.plotWidth += 1

                self.wholeWidth = self.plotWidth + self.gapWidth
                self.updateStack()

            elif key == 'd':  # Decrease Gap Thickness
                if self.gapWidth > 0:
                    self.gapWidth -= 1

                self.wholeWidth = self.plotWidth + self.gapWidth
                self.updateStack()
            elif key == 'f':  # Increase Gap Thickness
                if self.gapWidth < 25:
                    self.gapWidth += 1

                self.wholeWidth = self.plotWidth + self.gapWidth
                self.updateStack()

            elif key == 'q':  # Decrease Curviness
                index = self.curveList.index(self.curvy)
                if index > 0:
                    index -= 1

                    self.curvy = self.curveList[index]

                    if self.curvy:
                        window = int(self.plotsAmt * self.curvy[0])
                        if (window % 2) == 0: window += 1
                        if window < 5: window = 5
                        self.curvyValue = (window, self.curvy[1])  # Only used to init process
                    else:
                        self.curvyValue = 0

                    if hasattr(self, 'proQ'):
                        self.proQ.put(['curvy', self.curvyValue])
            elif key == 'w':  # Increase Curviness
                index = self.curveList.index(self.curvy)
                if index < len(self.curveList) - 1:
                    index += 1

                    self.curvy = self.curveList[index]

                if self.curvy:
                    window = int(self.plotsAmt * self.curvy[0])
                    if (window % 2) == 0: window += 1
                    if window < 5: window = 5
                    self.curvyValue = (window, self.curvy[1])  # Only used to init process
                else:
                    self.curvyValue = 0

                if hasattr(self, 'proQ'):
                    self.proQ.put(['curvy', self.curvyValue])
                
            elif key == 'a':  # Decrease Interpolation
                index = self.interpList.index(self.interp)
                if index > 0:
                    index -= 1

                    self.interp = self.interpList[index]
                    if hasattr(self, 'proQ'):
                        self.proQ.put(['interp', self.interp])
            elif key == 's':  # Increase Interpolation
                index = self.interpList.index(self.interp)
                if index < len(self.interpList) - 1:
                    index += 1

                    self.interp = self.interpList[index]
                    if hasattr(self, 'proQ'):
                        self.proQ.put(['interp', self.interp])
                
            elif key == 'z':  # Decrease Buffer
                index = self.audioBufferList.index(self.audioBuffer)
                if index > 0:
                    index -= 1
                    
                    self.audioBuffer = self.audioBufferList[index]

                    if hasattr(self, 'dataQ'):
                        # Update before buffer
                        self.updateStack()
                        self.dataQ.put(['buffer', self.audioBuffer])
                        self.proQ.put(['buffer', self.audioBuffer])
            elif key == 'x':  # Increase Buffer
                index = self.audioBufferList.index(self.audioBuffer)
                if index < len(self.audioBufferList) - 1:
                    index += 1

                    self.audioBuffer = self.audioBufferList[index]

                    if hasattr(self, 'dataQ'):
                        # Update before buffer
                        self.updateStack()
                        self.dataQ.put(['buffer', self.audioBuffer])
                        self.proQ.put(['buffer', self.audioBuffer])

    def killEvent(self, sig, frame):
        print("Quitting")
        try:
            self.mainQ.put(1)  # End main thread
            self.P1.terminate()  # Kill Processes
            self.T1.terminate()
            if hasattr(self, 'cleanLines'):  # Clean up ~/.asoundrc
    
                alsaFolder = os.getenv("HOME") + '/.asoundrc'
                with open(alsaFolder, 'w') as alsaConf:
                    alsaConf.writelines(self.cleanLines)
        except RuntimeError:
            print('Some processes won\'t close properly, closing anyway.')


# Starts program
if __name__ == '__main__':
    ReVidiaTerm()


