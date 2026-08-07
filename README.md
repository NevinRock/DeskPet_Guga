# Guga Desktop Pet

Guga is a standalone Windows desktop pet created by [@Nevin](https://github.com/NevinRock) in 2026.

It is a transparent, always-on-top PySide6 application that runs locally without a browser or an internet connection.

## Features

- Transparent frameless desktop window
- Config-driven sprite animations
- Idle animation and hover-to-wave interaction
- Action menu with wave, shake, walk, think, jump, and random actions
- Real window movement during jumps
- Alpha-aware mouse hit testing
- Drag-to-move interaction
- Live pet-size adjustment from 120 to 320 px
- Multi-monitor-aware default placement

## Run from source

```powershell
py -3 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python main.py
```

## Build

Run `build.bat` to create a windowed standalone executable at `dist\Guga.exe`.

## License

Copyright (c) 2026 Nevin. Released under the [MIT License](LICENSE).
