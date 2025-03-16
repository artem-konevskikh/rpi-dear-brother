# Python code for Dear Brother project by Maria Fedorova

## Raspberry Pi Setup

1. **Install Raspbian OS**: Download Raspbian OS from the official website and write it to an SD card.
2. **Enable SPI and I2C interfaces**: Run `sudo raspi-config` and navigate to `Interfacing Options`. Enable SPI and I2C interfaces.
3. **Configure SPI**: Add `spidev.bufsiz=32768` to `/boot/firmware/cmdline.txt`

## Installation

```bash
# Clone the repository
git clone git@github.com:artem-konevskikh/rpi-dear-brother.git

# Navigate to the project directory
cd rpi-dear-brother

# Create and activate a virtual environment with uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package in development mode
uv pip install -e .
```

## Autostart
TODO: add autostart instructions later

## Example Usage

```bash
# Run with default settings
python src.emotion-lighting.main

# Run with custom settings
python src.emotion-lighting.main --led-count 60 --no-touch
```