#!venv/bin/python
# -*- coding: utf-8 -*-

import os
import pyaudio
import time
import curses
import struct
import queue
import threading as th
import numpy as np
import subprocess as subp
import sounddevice  # This is imported to suppress portaudio debug errors

# Default global variables
width = 64          # fallback width
ceiling = 1000000   # The max value of bars (Default = 5 00000)
frames = 2048       # How accurate/fast bars appear (Default = 1024)
printFPS = 0        # Print video frames per sec
printFrames = 0     # Print number of audio frames
printBarNum = 0     # Print number of bars
printCeilNum = 0    # Print ceiling number
printDelayNum = 0   # Print delay number
interpretBars = 1   # Smooths out the bars, but adds "visual" delay
barThick = 2
gapThick = 1
# Extra variables to avoid error
barValues = []
timeF = 0
timeC = 0
timeDStart = 0

# Displays device ID options
p = pyaudio.PyAudio()
numDevices = p.get_device_count()
for ID in range(numDevices):
    if (p.get_device_info_by_index(ID).get('maxInputChannels')) > 0:
        print(ID, "-", p.get_device_info_by_index(ID).get('name'))
device = int(input('Select Audio Device ID:'))
os.system('tput civis')     # Makes cursor invisible

# Open stream to collect audio data.
stream = p.open(
    input_device_index=device,
    format=pyaudio.paInt16,
    channels=2,
    rate=int(p.get_device_info_by_index(device).get('defaultSampleRate')),
    input=True,
    frames_per_buffer=1)

# Collects the raw audio data and coverts to ints
def audioData(q):
    dataList = []
    for i in range(frames):
        data = stream.read(1)
        dataList.append(sum(struct.unpack("2h", data)))
    q.put(dataList)

# Start the initial thread and queue to collect data
Q1 = queue.Queue()
T1 = th.Thread(target=audioData, args=(Q1,))
T1.start()

# Begin the infinite loop of ReVidia
while stream.is_active():

    # Delay Checker
    if printDelayNum:
        timeDEnd = time.time()
        realTimeD = (timeDEnd - timeDStart) * 1000
        timeDStart = time.time()

    # Gets console X and Y dimensions to set width
    consoleY, consoleX = subp.check_output(['stty', 'size']).decode().split()
    width = int(consoleX) // (gapThick + barThick)
    if width < 2: width = 2

    # Part 2 of separate thread audio data collection
    T1.join()
    dataList = Q1.get()

    # The heart of ReVidia, the fourier transform.
    transform = np.fft.fft(dataList)
    absTransform = np.abs(transform[0:frames//2])     # Each plot is rate/frames = frequency

    # Part 1 of separate thread audio data collection
    T1 = th.Thread(target=audioData, args=(Q1,))
    T1.start()

    # Most of the math to plot ReVidia.
    # It scales linearly for 3/4, then exponentially to 12khz.
    oldBarValues = barValues
    startGrow = int(width // 1.5)
    expoGrow = ((frames//4)/startGrow)**(1/(width - startGrow))
    xBarMaxFloat = startGrow
    xBarMax = startGrow

    barValues = list(map(int, absTransform[0:startGrow]))   # Linearly scale

    for z in range(width - startGrow):                       # Exponentially scale
        xBarMin = xBarMax
        xBarMaxFloat *= expoGrow
        xBarMax = int(-(-xBarMaxFloat // 1))
        if xBarMax - xBarMin <= 0:
            xBarMax += 1

        barValues.append(int(max(absTransform[xBarMin:xBarMax])))

    # Interpolates the data to smooth out the bars
    interpAmnt = 1
    fakeBarValues = []
    if interpretBars:
        interpAmnt = frames // 512
        if len(oldBarValues) == width:
            interpBarValues = list(map(lambda new, old: (new - old) // interpAmnt, barValues, oldBarValues))

            for r in range(interpAmnt):
                oldBarValues = list(map(lambda old, interp: old + interp, oldBarValues, interpBarValues))
                fakeBarValues.append(oldBarValues)

    # Prints out the graph
    # ~85FPS cap as the konsole terminal can't do anymore than that.
    for z in range(interpAmnt):
        if fakeBarValues:
            barValues = fakeBarValues[z]
        if z == 0:
            firstFrameTime = 0.0115 - (time.time() - timeC)
            if firstFrameTime > 0:
                time.sleep(firstFrameTime)
        else:
            time.sleep(0.0115)
        yBarMin = ceiling
        barHeight = int(consoleY)
        yWidth = ceiling // barHeight
        halfYWidth = yWidth // 2
        for y in range(barHeight):
            printBarLine = []
            for x in range(width):
                if barValues[x] > yBarMin:
                    printBarLine.append('\u2588' * barThick)
                elif barValues[x] > (yBarMin - halfYWidth):
                    printBarLine.append('\u2584' * barThick)
                else:
                    printBarLine.append(' ' * barThick)
            yBarMin -= yWidth
            if y < (barHeight - 1):
                print((' ' * gapThick).join(printBarLine))
            else:
                print((' ' * gapThick).join(printBarLine), end='\r')

        # Prints debug stats
        if printFPS or printFrames or printBarNum or printDelayNum or printCeilNum:
            print('')
            printDebugList = []
            if printBarNum:
                printDebugList.append(str(width) + ' Bars')
            if printFrames:
                printDebugList.append(str(frames) + ' Frames')
            if printCeilNum:
                printDebugList.append(str(ceiling//1000) + ' High')
            if printFPS:
                printDebugList.append(str(round(1000 // ((time.time() - timeF) * 1000))) + 'FPS')
                timeF = time.time()
            if printDelayNum:
                printDebugList.append(str(round(realTimeD, 2)) + 'ms')

            print(' | '.join(printDebugList), end='\r')

    timeC = time.time()     # Collects time between graph end to start for frame time consistency.

    # Controls ReVidia with character inputs
    def controls(win):
        win.nodelay(True)
        try:
            key = win.getkey()
            return key
        except Exception:
            pass    # No input
    key = curses.wrapper(controls)

    # Key list
    if key == 'q':
        print('\n', 'Quiting')
        time.sleep(0.5)
        break
    if key == 'p':
        print('\n', 'Paused')
        while True:
            time.sleep(0.25)
            key = curses.wrapper(controls)
            if key == 'p': break
    if key == 'r':
        if frames < 4096:
            frames += 512
    if key == 'f':
        if frames > 512:
            frames -= 512
    if key == 'g':
        if ceiling < 10000000:
            ceiling += 50000
        else:
            print('\n', 'MIN INPUT REACHED')
            time.sleep(0.10)
    if key == 't':
        if ceiling > 50000:
            ceiling -= 50000
        else:
            print('\n', 'MAX INPUT REACHED')
            time.sleep(0.10)
    if key == 'y':
        if barThick > 1:
            barThick -= 1
    if key == 'u':
        if barThick < 25:
            barThick += 1
    if key == 'h':
        if gapThick > 1:
            gapThick -= 1
    if key == 'j':
        if gapThick < 25:
            gapThick += 1
    # Toggles
    if key == 'n':
        if not printFrames:
            printFrames = 1
        elif printFrames:
            printFrames = 0
    if key == 'b':
        if not printBarNum:
            printBarNum = 1
        elif printBarNum:
            printBarNum = 0
    if key == 'v':
        if not printDelayNum:
            printDelayNum = 1
        elif printDelayNum:
            printDelayNum = 0
    if key == 'c':
        if not printCeilNum:
            printCeilNum = 1
        elif printCeilNum:
            printCeilNum = 0
    if key == 'x':
        if not printFPS:
            printFPS = 1
        elif printFPS:
            printFPS = 0
    if key == 'd':
        if not interpretBars:
            interpretBars = 1
        elif interpretBars:
            interpretBars = 0

os.system('clear')
