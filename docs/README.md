![Preview](Preview.png)
# ReVidia Audio Visualizer [Windows Branch]
### A highly customizable real time audio visualizer on Linux/Windows
#### Branches:
- Linux: master branch
- Windows: win-port branch 
## Requirements
#### Windows: Python 3.8(64bit) with PATHS
- Download Python here: https://www.python.org/downloads/
- Just be sure to select a "Windows x86-64" version
- During installation **MAKE SURE** you check the box: "Add Python to PATH"

#### Optionally install VB-CABLE for Windows (See Below in Important Notes)

## Installation
#### On Windows run:
```
install.bat
```
#### Once Started:
- It might take a couple of minutes, wait until it says "Done"
- Then use the desktop shortcut created to enjoy! 🎉
#### Note: Run the installer again if you move the file at all

## Important Notes:
#### This program ONLY accepts input audio streams

If you are using **Windows** you can optionally install VB-CABLE:
- https://www.vb-audio.com/Cable/index.htm#DownloadCable  

This will allow you to use a non-WASAPI speaker's audio and will have a better chance of using a device:
- To use VB-CABLE follow the "Setting up VB-CABLE in 5 steps:" in the "WindowsReadme.txt"
  
## Future Ideas:
#### In order of importance:
- General optimizing
- Fix how transparency is done on Windows
- Overhaul the old Linux terminal version

## Acknowledgments
- Numpy mostly for the FFT
- PyAudio and PortAudio for audio data collection
  - PyAudio WASAPI loopack fork for Windows port
- PyQt5 and QT for the GUI

 ## License
This project is licensed under the GPLv3 License - see the [LICENSE](/LICENSE.txt) file for details

### For more information please look at the real [ReadMe](/WinReadMe.txt) included
