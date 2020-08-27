import numpy as np
import wave


def start(file, sampleRate, barValues, time, height, oldVolList, oldTimes, freqList):

    volList = list(map(lambda plot: plot / height, barValues))

    waves, endTimes = createWaves(sampleRate, freqList, volList, oldVolList, time, oldTimes)

    file.writeframes(waves)

    return (volList, endTimes)


def createFile(sampleRate):

    file = wave.open('reverseFFT.wav', 'wb')
    file.setframerate(sampleRate)
    file.setnchannels(1)
    file.setsampwidth(2)

    return file


def createWaves(sampleRate, freqPlot, volList, oldVolList, time, oldTimes):

    sampleList = []
    endTimes = []
    for i in range(len(freqPlot)):

        vol = volList[i]
        freq = freqPlot[i]
        if 0 < freq:
            # Sync up old to new wave to avoid clipping sounds
            if len(oldTimes) == len(freqPlot):
                startTime = oldTimes[i] % (1/freq)
            else:
                startTime = 0
            endTime = startTime + time
            endTimes.append(endTime)

            samples = np.linspace(startTime, endTime, int(sampleRate*time), endpoint=False)
            signal = np.sin(2 * np.pi * freq * samples)

            # Transition from old volume to new nicely
            if len(oldVolList) == len(volList):
                oldVol = oldVolList[i]
                tranSamples = int(sampleRate * time * 0.10)

                tranVol = np.linspace(oldVol, vol, tranSamples)
                tranSignal = np.multiply(signal[:tranSamples], tranVol)
                newSignal = signal[tranSamples:] * vol

                finalSignal = np.concatenate((tranSignal, newSignal)) * 32767
            else:
                finalSignal = signal * (vol * 32767)

            sampleList.append(finalSignal)

        else:
            endTimes.append(0)

    combinedWave = np.sum(sampleList, 0)

    finalWave = (combinedWave / len(sampleList))
    finalWave = finalWave.astype('int16')

    return (finalWave, endTimes)
