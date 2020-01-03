import struct
import os 
import subprocess
import re

# Get Python version and bit
pythonBit = struct.calcsize(("P") * 8)

result = subprocess.run("python -V", stdout=subprocess.PIPE)
pythonVersion = result.stdout.decode('utf-8')

# Install the right PyAudio
if re.match(r'Python 3.8', pythonVersion):
    if pythonBit == 32:
        os.system("pip install venv\PyAudio-0.2.11-cp38-cp38-win32.whl")
    elif pythonBit == 64:
        os.system("pip install venv\PyAudio-0.2.11-cp38-cp38-win_amd64.whl")
else:
    print("ERROR: Can't install PyAudio, need Python version 3.8")
    print("Your Python: " + pythonVersion)
    os.system("timeout /t -1")


