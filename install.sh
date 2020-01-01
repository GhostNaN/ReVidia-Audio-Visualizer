#!/bin/sh

# Create venv required
python -m venv venv
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
Exec=ReVidiaGUI.py
Path=$(pwd)
" > ReVidia.desktop

echo ""
echo "Done"
