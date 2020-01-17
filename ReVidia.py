# -*- coding: utf-8 -*-

import pyaudio
import struct
import numpy as np
from math import factorial


def getPA():    # PortAudio
    return pyaudio.PyAudio()


# Displays device ID options
def deviceName(p):
    deviceList, idList = [], []
    numDevices = p.get_device_count()
    for ID in range(numDevices):
        if (p.get_device_info_by_index(ID).get('maxInputChannels')) > 0:
            deviceList.append(p.get_device_info_by_index(ID).get('name'))
            idList.append(ID)
    deviceList = [deviceList, idList]
    return deviceList


# Returns sample rate
def sampleRate(p, device):
    return int(p.get_device_info_by_index(device).get('defaultSampleRate'))


# Open stream to collect audio data.
def startStream(p, device, samples):
    stream = p.open(
        input_device_index=device,
        format=pyaudio.paInt16,
        channels=2,
        rate=samples,
        input=True,
        frames_per_buffer=1)
    return stream


# Collects the raw audio data and coverts to ints
def audioData(q1, q2, stream, frames, split):
    monoList, leftList, rightList = [], [], []
    while True:
        data = stream.read(1, exception_on_overflow=False)
        if not split:
            monoList.append(sum(struct.unpack("2h", data)) // 2)
            while len(monoList) > frames:
                del (monoList[0])

                if q1.empty():
                    q1.put(monoList)
        else:
            leftList.append(sum(struct.unpack("2h", data)[:1]))   # Left
            rightList.append(sum(struct.unpack("2h", data)[1:]))  # Right
            while len(leftList) > frames:
                del (leftList[0])
                del (rightList[0])

                if q1.empty() or q2.empty():
                    q1.put(leftList)
                    q2.put(rightList)

        if q1.qsize() > 1:
            break


# Assigns frequencies locations based on plots
def assignFreq(frames, samples, width):
    plot = samples / frames

    freqList = [0]
    noteNum = plot
    numFloat = plot
    point1 = 1000 / plot
    point1Pos = 0.66
    endPoint = samples // 4

    startGrow = int(width * point1Pos)
    if startGrow > 1:
        expoGrow = point1 ** (1 / (startGrow - 1))

        for f in range(width - 1):

            oldFloat = noteNum
            numFloat *= expoGrow
            noteNum = numFloat

            if numFloat - oldFloat <= plot:
                noteNum = oldFloat + plot

            if f == startGrow - 2:
                expoGrow = (endPoint / noteNum) ** (1 / (width - startGrow))  # RATE=(END/START)**(1/STEPS)

            freqList.append(oldFloat)

    return freqList


# Assigns notes locations based on the frequency plot
def assignNotes(freqList):

    notesList = ['C', 'C♯', 'D', 'D♯', 'E', 'F', 'F♯', 'G', 'G♯', 'A', 'A♯', 'B'] * 9
    notesFreq = []
    for i in range(-8, 100):  # C-(-1) - B-8
        notesFreq.append((2 ** (1 / 12)) ** (i - 49) * 440)

    notesFreqList = []
    low = 0
    for freq in freqList:
        for n in range(low, 108):
            if freq - notesFreq[n] < 0:
                index = notesFreq.index(min(notesFreq[n], notesFreq[n-1], key=lambda x: abs(x - freq)))
                notesFreqList.append(notesList[index])
                low = n
                break

    return notesFreqList


# Calculates decibel
def getDB(data):
    amp = max(data) / 32767
    if amp < 0:
        amp *= -1
    dB = round(20 * np.log10(amp), 1)

    return dB


# Interpolates the data to smooth out the bars
def interpData(barValues, oldList):
    interpBarValues = barValues

    if len(oldList[0]) == len(barValues):
        for oldValues in oldList:
            barValues = list(map(lambda new, old: new + old, barValues, oldValues))
        divide = len(oldList) + 1
        interpBarValues = list(map(lambda bars: bars // divide, barValues))

    return interpBarValues


# Savitzky Golay Filter stolen/borrowed from "elviuz" on Stackoverflow and is much faster than SciPy
def savitzky_golay(y, window_size, order, deriv=0, rate=1):
    try:
        window_size = np.abs(np.int(window_size))
        order = np.abs(np.int(order))
    except:
        raise ValueError("window_size and order have to be of type int")
    if window_size % 2 != 1 or window_size < 1:
        raise TypeError("window_size size must be a positive odd number")
    if window_size < order + 2:
        raise TypeError("window_size is too small for the polynomials order")
    order_range = range(order+1)
    half_window = (window_size -1) // 2
    # precompute coefficients
    b = np.mat([[k**i for i in order_range] for k in range(-half_window, half_window+1)])
    m = np.linalg.pinv(b).A[deriv] * rate**deriv * factorial(deriv)
    # pad the signal at the extremes with
    # values taken from the signal itself
    firstvals = y[0] - np.abs( y[1:half_window+1][::-1] - y[0] )
    lastvals = y[-1] + np.abs(y[-half_window-1:-1][::-1] - y[-1])
    y = np.concatenate((firstvals, y, lastvals))
    return np.convolve( m[::-1], y, mode='valid')


# Processes the audio data into proper
def processData(dataList, width, samples, curvy=False):

    frames = len(dataList)
    plot = samples / frames
    if width < 2: width = 2  # Prevents crash when window gets too small
    if width > (frames//4): width = (frames//4)     # Prevents crash when width is too high

    # The heart of ReVidia, the fourier transform.
    transform = np.fft.fft(dataList, frames)
    absTransform = np.abs(transform[0:frames//2])     # Each plot is rate/frames = frequency

    point1 = 1000 / plot    # Points in the graph scales to
    point1Pos = 0.66
    endPoint = frames // 4

    startGrow = int(width * point1Pos)
    expoGrow = point1**(1 / startGrow)     # RATE=(END/1)**(1/STEPS)
    xBarMaxFloat = 1
    xBarMax = 0

    barValues = []
    for z in range(width):                       # Exponentially scale
        xBarMin = xBarMax
        xBarMaxFloat *= expoGrow
        xBarMax = int(xBarMaxFloat)
        if xBarMax - xBarMin <= 0:
            xBarMax = xBarMin + 1
        if z == startGrow-1:
            xBarMaxFloat = xBarMax
            expoGrow = (endPoint / xBarMaxFloat) ** (1 / (width - startGrow))  # RATE=(END/START)**(1/STEPS)

        barValues.append(int(max(absTransform[xBarMin:xBarMax])))

    if curvy:
        curveArray = np.array(barValues)
        barValues = savitzky_golay(curveArray, curvy, 3)  # data, window size, polynomial order

    return barValues
