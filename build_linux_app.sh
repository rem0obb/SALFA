#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

python3 -c 'import tkinter'

if python3 -m venv .venv-build; then
    . .venv-build/bin/activate
    python -m pip install --upgrade pip pyinstaller
    python -m PyInstaller --clean --noconfirm --onefile --windowed \
        --optimize 2 --name SALFAGenerator ctf_generator_gui.py
else
    echo "python3-venv is unavailable; using the user-site PyInstaller."
    python3 -m pip install --user --upgrade pyinstaller --break-system-packages
    python3 -m PyInstaller --clean --noconfirm --onefile --windowed \
        --optimize 2 --name SALFAGenerator ctf_generator_gui.py
fi

./dist/SALFAGenerator --self-test
echo "Built and verified: dist/SALFAGenerator"
