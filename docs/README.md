![Preview](Preview.png)
# ReVidia Audio Visualizer
### A highly customizable real time audio visualizer on Linux/Windows
#### Branches:
- Linux: master branch
- Windows: win-port branch 
## Requirements
#### Linux: Python 3.7+ and Portaudio | Optional: PulseAudio

- Most distros should have Python already installed
- If you don't have PortAudio, download and compile it from:
http://www.portaudio.com/download.html
  - If you can, use your package manager to install PortAudio

#### Windows: Python 3.8(64bit) with PATHS
- Download Python here: https://www.python.org/downloads/
- Just be sure to select a "Windows x86-64" version
- During installation **MAKE SURE** you check the box: "Add Python to PATH"

#### Optionally install VB-CABLE for Windows (See Below in Important Notes)

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
#### This program ONLY accepts input audio streams

If you are on **Linux**, ReVidia will try to use ALSA to retrieve your PulseAudio output

Otherwise if you use JACK normally like below, then just pick the JACK input.
- https://forum.manjaro.org/t/how-to-replace-pulseaudio-with-jack-jack-and-pulseaudio-together-as-friend/2086

&nbsp;

If you are using **Windows** you can optionally install VB-CABLE:
- https://www.vb-audio.com/Cable/index.htm#DownloadCable  

This will allow you to use a non-WASAPI speaker's audio and will have a better chance of using a device:
- To use VB-CABLE follow the "Setting up VB-CABLE in 5 steps:" in the "WindowsReadme.txt"
  
## Future Ideas:
#### In order of likely importance:
- New ReVidia Icon
- General optimizing
- Fix how transparency is done on Windows(Decouple Settings?) 

## Acknowledgments
- Numpy mostly for the FFT
- PyAudio and PortAudio for audio data collection
  - PyAudio WASAPI loopack fork for Windows port
- PyQt5 and QT for the GUI

 ## License
This project is licensed under the GPLv3 License - see the [LICENSE](/LICENSE) file for details

### For more information on the Linux branch please look at the real [ReadMe](/LinuxReadMe) included
