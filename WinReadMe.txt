ReVidia [Windows Port]

Installation
============================

ReVidia on Windows REQUIRES Python 3.8 
Download from here:
https://www.python.org/downloads/

During installation MAKE SURE you check the box:
"Add Python to PATH" 
It will not work without it.

With Python installed, run "install.bat" to install.
It might take a couple minutes, so wait until it says "Done" 

Then simply use the desktop shortcut to enjoy!


I also HIGHLY recommend installing VB-CABLE: 
https://www.vb-audio.com/Cable/index.htm#DownloadCable

As this software ONLY accepts input(mics) audio streams for now.

Without it you might not be able to select speaker's audio 
or even start the program at ALL because it also uses
Windows audio APIs that meld better with PortAudio.

Using VB-CABLE:
After installing VB-CABLE go into the sound control panel 
and set "CABLE Input" as your default playback device. 
Then in "CABLE Output" Properties check the box
"Listen to this device" to your speakers you normally use. 

Then, if you like to use your speaker's audio
just select any "CABLE Output" device in ReVidia.


Usage/About
============================

General:

- If you start the program and no device list is shown, it means that 
  no API you have is compatible and you should install VB-CABLE shown above.

- If you really don't like VB-CABLE and you want to use your speaker audio try this guide:
  https://www.howtogeek.com/howto/39532/how-to-enable-stereo-mix-in-windows-7-to-record-audio/
  
- If you don't want to use Python 3.8, install PyAudio manually using the venv pip.
  Then just ignore the error in the install.bat and continue.

- Because how Windows uses transparency:
  If you like to make the background disappear go into Design|Color|Background Color
  and change the alpha channel to 0. Then press SHIFT twice. 
  Press shift once more while on the window to make it reappear.

- The icon is just my profile pic as a place holder until I come with a better custom icon.


Settings:

For best performance leave as default, shrink the program size and lower the FPS as needed.
Use Stats's Late Frames and Latency to gauge performance.

On a scale from [0] being negligible/none to [5] being the worst performance cost of settings:

Main|Split Audio - Splits the audio into left(top half) and right(bottom half) channels [5]
Main|Curviness - Curves/Smooths the bars with a Savitzky Golay Filter [1] 
Main|Interpolation - By averaging old data with new data it makes the bars appear smoother [1]
Main|Frames - Audio frames in the buffer, the higher the number the higher the accuracy [5]

Design|Color|Bar Color/Background Color/Outline Color - Allows to pick color and alpha(transparency) [0-2]*
Design|Color|Rainbow - Creates a rainbow effect to the colors of Bars/(Outline Only) based on current Bar Color [1]
Design|Dimensions - Brings up a scroll bars the change dimensions and look of the bars. [0-5]**
Design|Illuminate - Scales the alpha cap of the bars [2]
Design|Outline Only - If Out Width is more than 0 it will only show the outline. [0]
Design|Cutout - Instead of drawing the bars it will "cut" the background instead [2]

Stats|Frequencies - Reveals the frequency plots(sample rate / frames) of the bars  [5]
Stats|Notes - Places notes to the closest given frequency plot [4]
Stats|Late Frames - Tells you how many video frames aren't meeting the frame time(FPS) deadline [0-1]
Stats|Bars - Tells how many bars are being drawn in the window [0-1]
Stats|Latency - Tells the time in ms(milliseconds) to complete drawing a frame [0-1]
Stats|dB Bar - Using a bar it shows you the loudness of the audio in decibels [1]

* If you change the alpha to anything less than 255 will cost some performance.

**If you change the width or gap to allow more bars (use Stats|Bars to check) will decrease performance.
  Having (Out)line more than 0/enabled will decrease performance.
  And increasing the height to allow the bars to take up more screen space will decrease performance.

Shortcuts:

Scroll - Change Bar height on the fly
Shift - Press once to hide toolbar, Once more to hide the borders and then on more time to bring up the borders and the toolbar again.
Esc - Close program 


Tips:

- Lower the Main|Interpolation for more responsiveness, this helps when you have a low FPS set.

- For a Monstercat lite-edition style, set Main|Curviness to Sharp, Main|Frames to 8192, scale window to have 64 bars(Stats|Bars)
  and keep the rest at default. This WILL NOT look the exact same, that was never my goal to begin with.
