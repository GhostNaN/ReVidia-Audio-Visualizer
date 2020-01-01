# -*- coding: utf-8 -*-

import pyaudio
import struct
import numpy as np


def getPA():    # PortAudio
    return pyaudio.PyAudio()


# Displays device ID options
def deviceName(p):
    deviceList = []
    numDevices = p.get_device_count()
    for ID in range(numDevices):
        if (p.get_device_info_by_index(ID).get('maxInputChannels')) > 0:
            API = p.get_device_info_by_index(ID).get('hostApi')     # Removes crap windows duplicate APIs
            if not p.get_host_api_info_by_index(API).get('name') in ['Windows WDM-KS', 'Windows DirectSound']:
                deviceList.append(p.get_device_info_by_index(ID).get('name') + " - " + str(ID))
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


# Assigns notes locations based on plots
def plotNotes(frames, samples, width):
    plot = samples / frames
    startGrow = int(width // 1.5)
    expoGrow = ((samples // 4) / (startGrow * plot)) ** (1 / (width - startGrow))
    noteList = ['C', 'C♯', 'D', 'D♯', 'E', 'F', 'F♯', 'G', 'G♯', 'A', 'A♯', 'B'] * 9
    notesFreq = []
    for i in range(-8, 100):    # C-(-1) - B-8
        notesFreq.append((2 ** (1 / 12)) ** (i - 49) * 440)

    notePlot = []
    noteNum = 0
    low = 0
    for f in range(width):
        for n in range(low, 108):
            if noteNum - notesFreq[n] < 0:
                index = notesFreq.index(min(notesFreq[n], notesFreq[n-1], key=lambda x: abs(x - noteNum)))
                notePlot.append(noteList[index])
                low = n
                break

        if f < startGrow - 1:
            noteNum += plot
        else:
            noteNum *= expoGrow

    return notePlot


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


# Processes the audio data into proper
def revidiaLoop(dataList, width, frames):

    if width < 2: width = 2  # Prevents crash when window gets too small
    if width > (frames//4): width = (frames//4)     # Prevents crash when width is too high

    # The heart of ReVidia, the fourier transform.
    transform = np.fft.fft(dataList, frames)
    absTransform = np.abs(transform[0:frames//2])     # Each plot is rate/frames = frequency

    # Most of the math to plot ReVidia.
    # It scales linearly for 2/3, then exponentially to ~12khz.
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
            xBarMax = xBarMin + 1

        barValues.append(int(max(absTransform[xBarMin:xBarMax])))

    # Curvy
    # if True:
    #     xList = [x + 1 for x in range(len(barValues))]
    #     barValues = np.polyfit(xList, barValues, width // 4)
    #     barValues = np.poly1d(barValues)(xList)

    return barValues
