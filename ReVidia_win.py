# -*- coding: utf-8 -*-

import pyaudio
import struct
import numpy as np
import time
import sys


# Displays device ID options
def deviceNames(q):
    p = pyaudio.PyAudio()
    wasapiList, intputList, wasapiIdList, intputIdList, wasapiSampleList, inputSampleList = [], [], [], [], [], []
    numDevices = p.get_device_count()
    for ID in range(numDevices):
        name = p.get_device_info_by_index(ID).get('name')
        API = p.get_host_api_info_by_index(p.get_device_info_by_index(ID).get('hostApi')).get('name')
        
        if (p.get_device_info_by_index(ID).get('maxInputChannels')) > 0:
            if not API in ['Windows WDM-KS', 'Windows DirectSound']:  # Removes crap windows APIs
                intputList.append('Intput: ' + name + ' - ' + str(API))
                intputIdList.append(ID)
                inputSampleList.append(p.get_device_info_by_index(ID).get('defaultSampleRate'))
        elif API == 'Windows WASAPI' and ((p.get_device_info_by_index(ID).get('maxOutputChannels')) > 0):
            wasapiList.append('Output: ' + name + ' - ' + str(API))
            wasapiIdList.append(ID)
            wasapiSampleList.append(p.get_device_info_by_index(ID).get('defaultSampleRate'))

    deviceList = [wasapiList + intputList, wasapiIdList + intputIdList, wasapiSampleList + inputSampleList]
    p.terminate()
    q.put(deviceList)


# Collects the raw audio data and coverts to ints
def collectData(dataTime, dataArr, dataArr2, dataQ, device, buffer, split, loopback):
    p = pyaudio.PyAudio()
    stream = p.open(
        input_device_index=device,
        format=pyaudio.paInt16,
        channels=2,
        rate=int(p.get_device_info_by_index(device).get('defaultSampleRate')),
        input=True,
        frames_per_buffer=1,
        as_loopback=loopback)

    i = 0
    while True:
        while stream.get_read_available():
            data = stream.read(1, exception_on_overflow=False)
            if not split:
                dataArr[i] = (sum(struct.unpack("2h", data)) // 2)
            else:
                dataArr[i] = (sum(struct.unpack("2h", data)[:1]))   # Left
                dataArr2[i] = (sum(struct.unpack("2h", data)[1:]))  # Right

            if i < buffer - 1:
                i += 1
            else:
                i = 0
        else:
            time.sleep(0.00001)  # Sleep just a little to reduce CPU usage

        dataTime.value = time.time()

        # Request a setting change
        while dataQ.qsize() > 0:
            change = dataQ.get()

            if 'kill' in change:
                p.terminate()
                sys.exit()
            elif 'buffer' in change:  # Change a setting
                buffer = change[1]
            elif 'split' in change:
                split = change[1]


# Processes data into Y values of bars
def processData(syncLock, dataTime, proTime, dataArr, dataArr2, proArr, proArr2, proQ, dataQ,
                frameRate, buffer, plotsList, split, curvy, interp):

    killTimeout = 3  # How many seconds to wait for main thread
    frameTime = 1 / frameRate
    width = len(plotsList) - 1
    barValues = []
    splitBarValues = []
    oldList = []
    oldSplitList = []
    while True:
        frameTimer = time.time()

        # Get audio data
        delayTime = dataTime.value  # Get current time of data
        dataList = dataArr[:buffer]
        if split:
            rightDataList = dataArr2[:buffer]

        # Transforms audio data
        oldBarValues = barValues
        barValues = transformData(dataList, plotsList, curvy)
        if split:
            oldSplitValues = splitBarValues
            splitBarValues = transformData(rightDataList, plotsList, curvy)

        # Smooth audio data using past averages
        if interp:
            if len(oldList) <= interp:
                oldList.append(list(oldBarValues))
                if split:
                    oldSplitList.append(list(oldSplitValues))
            while len(oldList) > interp:
                del (oldList[0])
            if split:
                while len(oldSplitList) > interp:
                    del (oldSplitList[0])

            barValues = interpData(barValues, oldList)
            if split:
                splitBarValues = interpData(splitBarValues, oldSplitList)

        # Send out data
        proTime.value = delayTime
        proArr[:width] = barValues
        if split:
            proArr2[:width] = splitBarValues

        workTime = time.time() - frameTimer

        # Request a setting change
        while proQ.qsize() > 0:
            request = proQ.get()

            if 'kill' in request:
                sys.exit()
            elif 'frameRate' in request:
                frameRate = request[1]
                frameTime = 1 / frameRate
            elif 'buffer' in request:
                buffer = request[1]
            elif 'split' in request:
                split = request[1]
            elif 'curvy' in request:
                curvy = request[1]
            elif 'interp' in request:
                interp = request[1]
            elif 'plots' in request:
                plotsList = request[1]
                width = len(plotsList) - 1

        killTime = time.time()
        syncLock.acquire(timeout=killTimeout)
        if (time.time() - killTime) > killTimeout:
            dataQ.put(['kill'])
            sys.exit()

        # Based on previous processing time, delay for lower latency
        delay = frameTime - workTime
        if delay < 0:
            delay = 0
        # Scale margin for error based on work load
        margin = 1 - ((workTime / frameTime) / 2)
        if margin > 0.95: margin = 0.95
        if (margin > 0) and (delay > 0):
            time.sleep(delay * margin)


# Assigns frequencies locations based on plots
def assignFreq(buffer, samples, plotsList, maxMode=False):
    freq = samples / buffer

    freqs = list(map(lambda plot: plot * freq, plotsList))

    if not maxMode:
        freqList = freqs[:-1]
    else:
        freqList = freqs

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
    if amp != 0:
        dB = round(20 * np.log10(amp), 1)
    else:
        dB = -float('Inf')

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


# Savitzky Golay Filter straight from the SciPy Cookbook
def savitzkyGolay(y, window_size, order, deriv=0, rate=1):
    from math import factorial
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


def realScale(start, stop, step):
    floats = list(np.arange(start, stop+step, step))
    ints = list(map(lambda float: int(round(float)), floats))

    return ints


def quadBezier(p0, p2, c, n, extra=False):
    x = []
    samples = n
    if extra: samples = n + 1
    for i in range(samples):
        t = i / n
        x.append((1 - t) * ((1-t) * p0 + t * c) + t * ((1-t) * c + t * p2))

    return x


def dataPlotter(values, step, limit):
    maxNum = int(values[0])
    plottedList = [maxNum]
    for i in range(1, len(values)):
        minNum = maxNum
        maxNum = step * round(values[i]/step)

        if values[i - 1] <= values[i]:
            if maxNum - minNum <= 0:
                maxNum = minNum + step
        else:
            if minNum - maxNum <= 0:
                maxNum = minNum - step

        if maxNum > max(values):
            maxNum = round(max(values) - step)
        if maxNum < 0:
            maxNum = step
        if maxNum > limit:
            maxNum = limit - step
        if minNum == maxNum:
            maxNum += step

        plottedList.append(maxNum)

    return plottedList


def rescaleData(data, dataCap, ceiling, log=False):
    if not dataCap:
        dataCap = 1
    if not log:
        scaledData = np.interp(data, (0, dataCap), (0, ceiling))
    else:   # WIP may be used later
        dataLog = np.log10(data)
        rangeLog = (0, np.log10(dataCap))
        scaleLog = (0, np.log10(ceiling))
        logScaled = np.power(10, np.interp(dataLog, rangeLog, scaleLog))

        scaledData = np.nan_to_num(logScaled)

    rescaled = list(map(int, scaledData))

    return rescaled


# Processes the audio data into proper
def transformData(dataList, plotsList, curvy=False):
    buffer = len(dataList)

    # The heart of ReVidia, the fourier transform.
    transform = np.fft.rfft(dataList, buffer, norm="ortho")
    absTransform = np.abs(transform)     # Each plot is rate/buffer = frequency

    barValues = []
    for z in range(len(plotsList)-1):
        minNum = plotsList[z]
        maxNum = plotsList[z+1]

        if maxNum > minNum:
            barValues.append(int(max(absTransform[minNum:maxNum])))
        else:
            barValues.append(int(max(absTransform[maxNum:minNum])))

    if curvy:
        curveArray = np.array(barValues)
        w = curvy[0]
        p = curvy[1]
        if w > len(plotsList): w = len(plotsList)  # Fail Safes
        if (w % 2) == 0: w += 1

        filtered = savitzkyGolay(curveArray, w, p)  # data, window size, polynomial order

        # Apply a basic moving avg on top to blend data
        movingAvg = []
        movingAvg.append((filtered[0] + filtered[1]) // 2)
        movingAvg.extend(map(lambda back, mid, front: (back + mid + front) // 3, filtered[0:], filtered[1:], filtered[2:]))
        movingAvg.append((filtered[-2] + filtered[-1]) // 2)

        barValues = list(map(int, movingAvg))

    return barValues
