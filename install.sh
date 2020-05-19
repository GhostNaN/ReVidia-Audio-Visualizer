#!/bin/sh

# Create venv and get missing dependencies 
python -m venv venv --system-site-packages
source venv/bin/activate
pip install -r venv/requirements.txt

# Make files executable
chmod +x ReVidiaGUI.py
chmod +x ReVidiaT.py
    
# Create desktop shortcut
touch ReVidia.desktop
chmod +x ReVidia.desktop

echo "[Desktop Entry]
Name=ReVidia
Type=Application
Comment='Audio Visualizer'
Terminal=false
Icon=$(pwd)/docs/REV.png
Exec=bash -c '"$(dirname "$1")"/ReVidiaGUI.py' dummy %k
Path=$(pwd)
" > ReVidia.desktop

echo ""
echo "Done"
