# SALFA CTF Code Generator

Graphical JLR Gen21 code generator recovered from the CTF firmware. The
160-byte `UPDATE.INF` profile is embedded in the application.

## Command line

```bash
python3 flare_generator.py SALFA2AEXEH401960 --region EU
```

Multiple VINs can be processed in one run:

```bash
python3 flare_generator.py \
  SALFA2AEXEH401960 \
  SALFA2AE8DH343605 \
  --region EU
```

## Graphical interface

```bash
python3 ctf_generator_gui.py
```

The interface accepts multiple VINs separated by newlines, spaces, commas, or
semicolons.

## Windows build

On Windows, run:

```powershell
.\build_windows_exe.ps1
```

Alternatively, open `build_windows_exe.bat`. The script:

1. Locates Python 3.10 or newer.
2. Installs Python with `winget` when necessary.
3. Installs or updates PyInstaller.
4. Creates one standalone `dist\SALFAGenerator.exe`.
5. Runs the EXE self-test to validate its embedded PKG archive.

The build is staged on the local system drive, so the script also works when
the project is opened from a mapped drive such as `Z:` or a network share.

Python and PyInstaller are required only on the build machine. The computer
running `SALFAGenerator.exe` does not need Python installed.

## Linux build

```bash
./build_linux_app.sh
```

The executable is created at `dist/SALFAGenerator` and verified automatically.

## Tests

```bash
python3 -m unittest -v
```

See [`FLARE_ANALYSIS.md`](FLARE_ANALYSIS.md) for the recovered algorithm and
the relevant firmware addresses.
