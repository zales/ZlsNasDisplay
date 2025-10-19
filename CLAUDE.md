# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ZlsNasDisplay is a Python application that renders system statistics on a Waveshare 2.9" e-ink display for a Raspberry Pi-based NAS device. The application uses scheduled tasks to periodically collect and display various metrics like CPU load, temperature, memory usage, network status, and more.

## Development Commands

### Setup
```bash
# Install dependencies using Poetry
poetry install

# Activate virtual environment
poetry shell
```

### Running the Application
```bash
# Run the application (display only)
poetry run python3 zlsnasdisplay

# Run with web dashboard enabled
ENABLE_WEB_DASHBOARD=true poetry run python3 zlsnasdisplay

# Run web dashboard on custom host/port
ENABLE_WEB_DASHBOARD=true WEB_DASHBOARD_HOST=0.0.0.0 WEB_DASHBOARD_PORT=8080 poetry run python3 zlsnasdisplay

# Or if in Poetry shell
python3 -m zlsnasdisplay
```

### Web Dashboard

The web dashboard provides a browser-based interface for monitoring NAS metrics in real-time:

```bash
# Enable via environment variable
export ENABLE_WEB_DASHBOARD=true

# Optional: Configure host and port (defaults: 0.0.0.0:8000)
export WEB_DASHBOARD_HOST=0.0.0.0
export WEB_DASHBOARD_PORT=8000

# Run the application
poetry run python3 zlsnasdisplay

# Access dashboard at http://<raspberry-pi-ip>:8000
```

**Features:**
- Real-time metrics via WebSocket (updates every 2s)
- REST API endpoints: `/api/metrics`, `/api/health`
- Responsive HTML dashboard with auto-reconnect
- Color-coded values (green/yellow/red based on thresholds)

### Matter Integration

The application can expose system metrics as Matter-compatible sensors using CircuitMatter:

```bash
# Enable Matter integration
export ENABLE_MATTER=true

# Optional: Configure Matter device settings
export MATTER_DEVICE_NAME="ZlsNAS"          # Default: "ZlsNAS"
export MATTER_VENDOR_ID="0xFFF1"            # Default: 0xFFF1 (test vendor)
export MATTER_PRODUCT_ID="0x8001"           # Default: 0x8001
export MATTER_UPDATE_INTERVAL="30"          # Seconds between updates (default: 30)

# Run the application
poetry run python3 zlsnasdisplay
```

**Commissioning:**
1. Start the application with `ENABLE_MATTER=true`
2. A QR code will be displayed in the console
3. Scan the QR code with a Matter controller (Apple Home, Google Home, Home Assistant, etc.)
4. Follow the controller's commissioning process

**Exposed Sensors:**
- CPU Temperature (TemperatureMeasurement cluster)
- NVMe Temperature (TemperatureMeasurement cluster)

**Requirements:**
- Python 3.11+ (required by CircuitMatter)
- `avahi-utils` package for mDNS functionality: `sudo apt install avahi-utils`
- Matter controller (Apple HomePod, Google Nest Hub, Home Assistant, etc.)

### Building Standalone Binary

Build a standalone binary with PyInstaller (must be run on Raspberry Pi for ARM64 compatibility):

```bash
# Build binary using the build script
./build-binary.sh

# Or manually:
poetry run pyinstaller zlsnasdisplay.spec

# Binary will be created at:
# - dist/zlsnasdisplay (single executable, ~53MB)
# - release-binary/zlsnasdisplay-VERSION-linux-aarch64.tar.gz (distribution package)
```

**Upload to GitHub Release:**
```bash
# After building on Raspberry Pi, upload to existing release
gh release upload v3.0.0 release-binary/zlsnasdisplay-3.0.0-linux-aarch64.tar.gz
```

**Important:** Binary must be built on ARM64 architecture (Raspberry Pi) for proper compatibility. Building on x86_64 will create an incompatible binary.

### Testing
```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/test_main.py

# Run tests without coverage
pytest --no-cov
```

### Code Quality
```bash
# Run type checking with mypy
mypy zlsnasdisplay

# Run linting and formatting with ruff
ruff check zlsnasdisplay
ruff format zlsnasdisplay

# Run pre-commit hooks manually
pre-commit run --all-files
```

## Architecture

### Core Components

1. **main.py** - Entry point that orchestrates the application
   - Sets up signal handlers for graceful shutdown
   - Configures scheduled tasks using the `schedule` library
   - Different metrics update at different intervals (10s, 30s, 1m, 1h, 3h)
   - Environment variables: `LOG_LEVEL`, `SENTRY_DSN`, `DISPLAY_IMAGE_PATH`, `ENABLE_WEB_DASHBOARD`, `WEB_DASHBOARD_HOST`, `WEB_DASHBOARD_PORT`, `ENABLE_MATTER`, `MATTER_DEVICE_NAME`, `MATTER_VENDOR_ID`, `MATTER_PRODUCT_ID`, `MATTER_UPDATE_INTERVAL`
   - Optionally runs web dashboard in background thread
   - Optionally runs Matter device integration for smart home compatibility

2. **display_controller.py** - Hardware abstraction layer
   - Wraps the Waveshare e-ink display driver (`epd2in9_V2`)
   - Handles display initialization, updates, clearing, and sleep mode
   - Uses partial display updates to reduce flickering

3. **display_renderer.py** - UI rendering logic
   - Manages the PIL Image object that represents the display
   - Renders grid layout and individual stat components
   - Handles font loading (Ubuntu fonts + Material Symbols icons)
   - Each render method clears its specific rectangle before drawing

4. **system_operations.py** - System metrics collection
   - Uses `psutil` for CPU load, memory, disk, and fan speed
   - Uses `gpiozero.CPUTemperature` for CPU temperature
   - Uses `apt` library to check for available system updates
   - Requires root privileges for apt update operations

5. **network_operations.py** - Network metrics collection
   - `NetworkOperations`: IP address, signal strength, internet connectivity
   - `TrafficMonitor`: Current upload/download speeds with unit auto-scaling
   - Uses `iwconfig` subprocess for Wi-Fi signal strength

6. **web_dashboard.py** - Web dashboard for remote monitoring (optional)
   - FastAPI-based REST API for metrics
   - WebSocket endpoint for real-time updates
   - Built-in HTML/CSS/JS frontend
   - Runs in background thread when `ENABLE_WEB_DASHBOARD=true`

7. **matter_device.py** - Matter/CHIP protocol integration (optional)
   - Uses CircuitMatter library for pure Python Matter implementation
   - Exposes NAS metrics as Matter-compatible sensors
   - Supports commissioning via QR code
   - CPU and NVMe temperature sensors using TemperatureMeasurement cluster
   - Integrates with main event loop for packet processing

8. **waveshare_epd/** - Third-party e-ink display drivers
   - Contains Waveshare's display driver code
   - Should generally not be modified unless updating driver versions

### Update Frequencies

The application uses `schedule` to run different tasks at different intervals:
- **10 seconds**: Current traffic, fan speed
- **30 seconds**: CPU load, network connectivity check
- **1 minute**: Signal strength, memory, NVMe stats, uptime
- **1 hour**: IP address
- **3 hours**: System updates check
- **2 seconds**: Display update cycle (renders accumulated changes)

### Data Flow

1. Scheduled tasks call specific render methods in `DisplayRenderer`
2. Render methods query `SystemOperations` or `NetworkOperations` for data
3. Data is drawn onto the PIL Image object using `ImageDraw`
4. Every 2 seconds, `update_display_and_save_image()` pushes the image to hardware
5. Display controller sends the image buffer to the e-ink display via SPI

## Type Checking

The project enforces strict type checking with mypy:
- All functions must have type annotations
- Test files are exempt from this requirement (see `tool.mypy.overrides`)

## Code Style

Ruff configuration (100 char line length):
- Enforces Python 3.8+ syntax
- Auto-fixes issues when possible
- Ignores formatter-recommended rules to avoid conflicts

## Configuration

### Display Layout Configuration

Display coordinates and constants are centralized in `display_config.py`:
- All pixel coordinates for the 296x128 display
- Unicode icon definitions
- Section boundaries and positioning
- Makes layout changes easier and code more maintainable

Import in rendering code:
```python
from zlsnasdisplay import display_config as cfg
self.draw.text((cfg.CPU_VALUE_X, cfg.CPU_VALUE_Y), "...")
```

## Error Handling

The codebase implements defensive error handling:
- All hardware sensor access is wrapped in try-except blocks
- Graceful fallback values (0, empty strings) when sensors unavailable
- Specific exception types caught (KeyError, AttributeError, OSError)
- Comprehensive logging for debugging
- Network operations have 5-second timeouts

Example pattern:
```python
def get_sensor_data() -> int:
    try:
        sensors = psutil.sensors_xyz()
        if sensors and "sensor_name" in sensors:
            return int(sensors["sensor_name"][0].value)
        return 0  # Fallback
    except (KeyError, IndexError, AttributeError) as e:
        logging.warning(f"Sensor access failed: {e}")
        return 0
```

## Important Implementation Notes

1. **TrafficMonitor Instance**: A single TrafficMonitor instance is created in DisplayRenderer.__init__() and reused. Do not create new instances in render methods.

2. **Font Loading**: Fonts are loaded with validation and fallback to PIL default font if files are missing.

3. **Sensor Validation**: Always validate sensor existence before accessing psutil dictionaries (e.g., `sensors_fans()["pwmfan"]`, `sensors_temperatures()["nvme"]`).

4. **Network Timeouts**: All network operations (requests, subprocess) should have explicit timeouts (default: 5 seconds).

## Testing

Comprehensive test suite with 60+ unit tests:
- `tests/test_system_operations.py` - SystemOperations class tests
- `tests/test_network_operations.py` - NetworkOperations and TrafficMonitor tests
- `tests/test_web_dashboard.py` - Web dashboard API and WebSocket tests
- `tests/test_matter_device.py` - Matter device integration tests
- All tests use mocks for hardware dependencies
- Tests cover both success and failure scenarios

To run specific test suites:
```bash
# Install test dependencies
poetry install --with dev

# Run all tests
poetry run pytest

# Run only web dashboard tests
poetry run pytest tests/test_web_dashboard.py -v

# Run only Matter integration tests
poetry run pytest tests/test_matter_device.py -v
```
