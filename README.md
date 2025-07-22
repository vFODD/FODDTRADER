# FODDTRADER

An open-source desktop application that automatically processes signals and integrates with Binance.

## Installation

1. Required libraries:

   - python-binance
   - telethon

Installation:
```bash
pip install python-binance telethon
```
> Note: `tkinter` is included in most Python distributions. If missing, on Windows you can use `pip install tk`.

2. To start the application:
   ```bash
   python trader.py
   ```

## Building as .exe (PyInstaller)

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```
2. To create the .exe:
   ```bash
   pyinstaller --onefile --windowed --icon=v2.ico --add-data "v2.ico;." trader.py
   ```
   - The output file will be located in `dist/trader.exe`.

## Open Source Usage

- The entire code is open source.
- Anyone can review, improve, and run the code on their own computer.

## Notes

- Your Binance API keys and Telegram API information are stored only locally on your own computer; they are never sent to any server or third party.
- Please make sure to keep your keys safe.
- The application also works on non-Windows systems, but the .exe is only for Windows.
