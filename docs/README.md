![Preview](Preview.png)
# ReVidia Audio Visualizer
### A highly customizable real time audio visualizer on Linux/Windows
#### Branches:
- Linux: master branch
- Windows: win-port branch 
## Requirements
#### Linux: Python 3.7+ and Portaudio

- Most distros should have Python already installed
- If you don't have PortAudio, download and compile it from:
http://www.portaudio.com/download.html
  - If you can, use your package manager to install PortAudio

#### Windows: Python 3.7+ with PATHS
- Download Python here: https://www.python.org/downloads/
- During installation **MAKE SURE** you check the box: "Add Python to PATH"

#### Highly recommend installing VB-CABLE for Windows (See Below in Important Notes)

## Installation
#### On Linux in the project directory run:
```
chmod +x install.sh && ./install.sh
```
#### On Windows run:
```
install.bat
```
#### Once Started:
- It might take a couple of minutes, wait until it says "Done"
- Then use the desktop shortcut created to enjoy! 🎉
#### Note: Run the installer again if you move the file at all

## Important Notes:
#### This program ONLY accepts input(mics) audio streams for now

If you are on **Linux** and want to use your speakers audio I recommend using jack like in this guide:
- https://forum.manjaro.org/t/how-to-replace-pulseaudio-with-jack-jack-and-pulseaudio-together-as-friend/2086
- Or by using some other form of loop back software for now
  
If you are using **Windows** I HIGHLY recommend installing VB-CABLE:
- https://www.vb-audio.com/Cable/index.htm#DownloadCable  
- Not only will it allow you to use your speaker's audio easily
- But depending on your system, it not might even run properly without the APIs it provides
- To use VB-CABLE follow the guide in the "Readme.txt"
  
## Future Ideas:
#### In order of importance:
- Implement a better solution to using speakers on Linux
- Make a profile/config feature
- Add a "Curvy" modifier
- General optimizing
- Fix how transparency is done on Windows
- Overhaul the old Linux terminal version

## Acknowledgments
- Numpy mostly for the FFT
- PyAudio and PortAudio for audio data collection
- PyQt5 and QT for the GUI

 ## License
This project is licensed under the GPLv3 License - see the LICENSE.txt file for details

### For more information please look at the real ReadMe.txt included
