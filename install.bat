:: Create venv required
python -m venv venv
call venv\Scripts\activate

:: Install dependencies
venv\Get_PyAudio.py
pip install -r venv\requirements.txt

:: Create desktop shortcut
set SCRIPT="%TEMP%\%RANDOM%-%RANDOM%-%RANDOM%-%RANDOM%.vbs"

echo Set oWS = WScript.CreateObject("WScript.Shell") >> %SCRIPT%
echo sLinkFile = "%CD%\ReVidia.lnk" >> %SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %SCRIPT%
echo oLink.IconLocation = "%CD%\docs\REV.ico" >> %SCRIPT%
echo oLink.TargetPath = "%CD%\RevidiaGUI_win.pyw" >> %SCRIPT%
echo oLink.Description = "Audio Visualizer" >> %SCRIPT%

echo oLink.Save >> %SCRIPT%
cscript /nologo %SCRIPT%
del %SCRIPT%

echo.
echo Done
timeout /t -1
