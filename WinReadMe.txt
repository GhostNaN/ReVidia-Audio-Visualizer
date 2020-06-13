ReVidia [Windows Port]

Installation
============================

ReVidia on Windows REQUIRES Python 3.8(64bit) 
Download from here:
https://www.python.org/downloads/
Just be sure to select a "Windows x86-64" version

During installation MAKE SURE you check the box:
"Add Python to PATH" 
It will not work without it.

With Python installed, run "install.bat" to install.
It might take a couple minutes, so wait until it says "Done" 

Then simply use the desktop shortcut to enjoy!


Optionally install VB-CABLE: 
https://www.vb-audio.com/Cable/index.htm#DownloadCable

In case no device is found or wasapi is not an option.
As this software ONLY accepts inputs and wasapi audio streams on Windows.

Setting up VB-CABLE in 5 steps:
1. After installing VB-CABLE go into the sound control panel or by running "control.exe mmsys.cpl" 
2. Set "CABLE Input" as your default playback device. 
3. Switch to the "Recording" tab and go in "CABLE Output" Properties.
4. Under the tab "Listen" check the box "Listen to this device" 
5. Finally in the "Playback through this device:" select the speakers you normally use. 

Then, if you like to use your speaker's audio that's not wasapi
just select any "CABLE Output" device in ReVidia.


Usage/About
============================

General:

- If you start the program and no device list is shown, it means that 
  no API you have is compatible and you should install VB-CABLE shown above.
  
- If you don't want to use Python 3.8(64bit), install PyAudio Loopback Fork manually:
  https://github.com/intxcc/pyaudio_portaudio

  Then just ignore the error in the install.bat and continue.

- Because how Windows uses transparency:
  If you like to make the background disappear go into Design|Color|Background Color
  and change the alpha channel to 0. Then press SHIFT twice. 
  Press shift once more while on the window to make it reappear.
  
- By default the plot height will auto level to the data. 
  To normalize simply change the plot height manually or by toggling Design|Auto Level to off.
  
- The FPS combo box is the global timer. So if you set it higher, everything will run faster and vice versa.
  And due to windows sub par timings, setting a high FPS is just a mere suggestion.
  Use Stats|Deadline to get an idea if the FPS you set is what you are receiving.

- Two profiles are include for fun. One is the "Monstercat-Lite", which is my best approximation of the Classic Monstercat visualizer.
  And the other is usually a showcase for the latest update or just personal favorite.

- Do note after any new update it's very likely that your old profile will not work for any number of reasons.

- The icon is just my profile pic as a place holder until I come with a better custom icon.


Settings:

For best performance leave as default, shrink the program size and lower the FPS as needed.
Use Stats|Deadline to gauge performance.


On a scale from [0] being negligible/none to [5] being the worst performance cost of settings:

Main|Profiles - Save, Load and Delete profiles that save all your settings [0]
Main|Device - Select a different audio device [0]
Main|Reverse FFT - Record and playback how the visualizer sounds [5]
Main|Split Audio - Splits the audio into left(top half) and right(bottom half) channels [4]
Main|Scale - Popup to adjust scaling curves using dragging and scrolling of points [0] 
Main|Curviness - Curves/Smooths the plots with a Savitzky Golay Filter & Moving Avg. [1] 
Main|Interpolation - By averaging old data with new data it makes the plots appear less noisy [0-1]
Main|Audio Buffer - Audio frames in the buffer. The higher the number the higher the accuracy, but old data lingers [3]

Design|Color|Main Color/Background Color/Outline Color - Allows to pick color and alpha(transparency) [0-2]*
Design|Color|Rainbow - Creates a rainbow effect by rapidly changing the Main Color hue [1]
Design|Illuminate - Scales the alpha cap of the plots(Bars Only) [2]
Design|Stars - Draws stars in the background with popup to customize [1-5] ***
Design|Gradient - Popup for making a gradient using double left click to make a point and right click to delete a point [0-2]*
Design|Dimensions - Brings up sliders to change the dimensions and look of the plots [0-5]**
Design|Auto Level - (On by default) Auto scale the plot height to the data, manually adjusting the plot height will disable [0]*
Design|Outline Only - If Out Width is more than 0 it will only show the outline [0]
Design|Cutout - Instead of drawing the plots normally, it will "cut" the background instead [2]

Stats|Deadline - Tells you the percentage of frames that are meeting the frame time(FPS) deadline [0-1]
Stats|Plots - Tells how many plots are being drawn in the window [0-1]
Stats|Latency - Tells the time in ms(milliseconds) from collecting the data to completing a frame [0-1]
Stats|dB Bar - Using a bar it shows you the loudness of the audio in decibels [1]
Stats|Frequencies - Reveals the frequency (sample rate / audio buffer) of each plot  [4]
Stats|Notes - Places notes to the closest given frequency plot [4]

Bars/Smooth Toggle - Change how the plots are drawn, either in Bars or by directly connecting the plots together called Smooth [0]
FPS Box - Change how fast in general the program runs, lower fps will decrease responsiveness in the visuals [N/A] 

* If you change the alpha to anything less than 255 will cost some performance.

**If you change the widths to allow more plots (use Stats|Plots to check) will decrease performance.
  Having (Out)line Width more than 0/enabled will decrease performance.
  And increasing the height to allow the plots to take up more screen space will decrease performance.

***Drawing more said object will decrease performance.

  
Shortcuts:

Scroll - Change plot height on the fly
Right-Click-Drag - Moves the window around
Shift - Press once to hide toolbar, Once more to hide the borders and then on more time to bring up the borders and the toolbar again.
Esc - Close program 


Tips:

- Due to timings never being perfect, setting a fps slightly above your refresh rate is a good idea.

- Lower the Main|Interpolation and Main|Audio Buffer for more responsiveness, this helps when you have a low FPS set.
