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

- The FPS combo box is the global timer. So if you set it higher, everything will run faster and vice versa.
  And due to windows sub par timings, setting a high FPS is just a mere suggestion.
  Use Stats|Deadline to get an idea if the FPS you set is what you are receiving.

- The icon is just my profile pic as a place holder until I come with a better custom icon.


Settings:

For best performance leave as default, shrink the program size and lower the FPS as needed.
Use Stats|Deadline to gauge performance.


On a scale from [0] being negligible/none to [5] being the worst performance cost of settings:

Main|Profiles - Save, Load and Delete profiles that save all your settings [0]
Main|Split Audio - Splits the audio into left(top half) and right(bottom half) channels [4]
Main|Scale - Popup to adjust scaling curves using dragging and scrolling of points [0] 
Main|Curviness - Curves/Smooths the bars with a Savitzky Golay Filter & Moving Avg. [1] 
Main|Interpolation - By averaging old data with new data it makes the bars appear less noisy [1]
Main|Audio Buffer - Audio frames in the buffer. The higher the number the higher the accuracy, but old data lingers [3]

Design|Color|Bar Color/Background Color/Outline Color - Allows to pick color and alpha(transparency) [0-2]*
Design|Color|Rainbow - Creates a rainbow effect to the colors of Bars/(Outline Only) based on current Bar Color [1]
Design|Gradient - Popup for making a gradient using double left click to make a point and right click to delete a point [0-2]*
Design|Dimensions - Brings up sliders to change the dimensions and look of the bars. [0-5]**
Design|Illuminate - Scales the alpha cap of the bars [2]
Design|Outline Only - If Out Width is more than 0 it will only show the outline. [0]
Design|Cutout - Instead of drawing the bars it will "cut" the background instead [2]

Stats|Deadline - Tells you the percentage of frames that are meeting the frame time(FPS) deadline [0-1]
Stats|Bars - Tells how many bars are being drawn in the window [0-1]
Stats|Latency - Tells the time in ms(milliseconds) from collecting the data to completing a frame [0-1]
Stats|dB Bar - Using a bar it shows you the loudness of the audio in decibels [1]
Stats|Frequencies - Reveals the frequency plots(sample rate / frames) of the bars  [5]
Stats|Notes - Places notes to the closest given frequency plot [4]

* If you change the alpha to anything less than 255 will cost some performance.

**If you change the widths to allow more bars (use Stats|Bars to check) will decrease performance.
  Having (Out)line Width more than 0/enabled will decrease performance.
  And increasing the height to allow the bars to take up more screen space will decrease performance.

  
Shortcuts:

Scroll - Change Bar height on the fly
Shift - Press once to hide toolbar, Once more to hide the borders and then on more time to bring up the borders and the toolbar again.
Esc - Close program 


Tips:

- Due to timings never being perfect, setting a fps slightly above your refresh rate is a good idea.

- Lower the Main|Interpolation and Main|Audio Buffer for more responsiveness, this helps when you have a low FPS set.
