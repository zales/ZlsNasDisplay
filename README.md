# ZlsNasDisplay

![display (10)](https://github.com/zales/ZlsNasDisplay/assets/832783/6e7828bc-3317-48c0-a1b5-804f8b1b86d2)
![display_sleep](https://github.com/zales/ZlsNasDisplay/assets/832783/63055923-21f6-4852-9ad6-2ac78c4181e7)

The ZlsNasDisplay application renders various system statistics onto the e-ink display, providing users with real-time insights into the Raspberry Pi-based NAS device's performance and connectivity. The display uses partial updates for smooth, flicker-free transitions and highlights critical values (CPU load, temperature, memory, disk usage) with inverted colors when thresholds are exceeded.

Here's a breakdown of the displayed information and their respective update frequencies:

* **CPU Load and Temperature**  
Displayed Information: The current CPU load percentage and temperature.  
Update Frequency: Updated every 30 seconds.
* **Available System Updates**  
Displayed Information: The number of available system updates.  
Update Frequency: Checked every 3 hours.
* **Network Status**
Displayed Information: Indicator of internet connectivity status.  
Update Frequency: Checked every 30 seconds.
* **Signal Strength**  
Displayed Information: The signal strength of the Wi-Fi connection in dBm.  
Update Frequency: Updated every minute.
* **Memory Usage**  
Displayed Information: The current memory usage percentage.  
Update Frequency: Updated every minute.
* **NVMe Disk Usage and Temperature**  
Displayed Information: The NVMe disk usage percentage and temperature.  
Update Frequency: Updated every minute.
* **Fan Speed**  
Displayed Information: The current fan speed in RPM (Revolutions Per Minute).  
Update Frequency: Updated every 10 seconds.
* **IP Address**  
Displayed Information: The current IP address of the Raspberry Pi.  
Update Frequency: Updated every hour.
* **System Uptime**  
Displayed Information: The system uptime in days, hours, and minutes.  
Update Frequency: Updated every minute.
* **Current Network Traffic**  
Displayed Information: The current download and upload speeds in MB/s.  
Update Frequency: Updated every 10 seconds.


## Installation

`sudo pip3 install zlsnasdisplay`

## Features

### E-ink Display
The application renders real-time system statistics on a Waveshare 2.9" e-ink display, providing at-a-glance monitoring directly on your NAS device.

**Smart Display Updates:**
- Uses partial updates for smooth, flicker-free transitions
- Minimal refresh artifacts for better viewing experience

**Critical Value Highlighting:**
- CPU load, temperature, memory, and disk usage are monitored against configurable thresholds
- Values exceeding critical thresholds are highlighted with inverted colors (white text on black background)
- Provides instant visual feedback when system resources need attention

### Web Dashboard (NEW!)
Access your NAS metrics remotely via a modern, responsive web interface with real-time updates.

- **Real-time monitoring** via WebSocket (2-second updates)
- **REST API endpoints** for integration with other tools
- **Responsive design** works on desktop and mobile
- **Auto-reconnect** handles network interruptions gracefully
- **Color-coded metrics** for quick status assessment

Enable the web dashboard:
```bash
# Set environment variable before running
export ENABLE_WEB_DASHBOARD=true

# Run the application
sudo python3 -m zlsnasdisplay

# Access at http://<raspberry-pi-ip>:8000
```

## Hardware
Raspberry Pi (5 tested)

[Waveshare 2.9" e-ink display](https://www.waveshare.com/product/2.9inch-e-paper-module.htm)

### Wiring

All necessary information about the wiring and operation is available on the [waveshare wiki](https://www.waveshare.com/wiki/2.9inch_e-Paper_Module_Manual#Working_With_Raspberry_Pi)


## Development

### Dependencies

*   `python`: Python version required for the project (>=3.9).
*   `pillow`, `gpiozero`, `schedule`, `psutil`, `requests`, `spidev`, `lgpio`: Python dependencies for display and system monitoring.
*   `fastapi`, `uvicorn`: Optional dependencies for the web dashboard feature.
*   `mypy`, `pre-commit`, `pytest`, `pytest-cov`, `ruff`, `tomli`: Development dependencies for linting, testing, and formatting.

#### Build System

*   `requires`: Poetry core version required for the build system.
*   `build-backend`: Specifies the backend used for building the project.

#### Mypy Configuration

*   `check_untyped_defs`: Checks untyped function definitions.
*   `disallow_untyped_defs`: Disallows untyped function definitions.
*   `overrides`: Overrides configuration for specific modules.

#### Pytest Configuration

*   `minversion`: Minimum required version of pytest.
*   `addopts`: Additional options passed to pytest for coverage reporting.

#### Coverage Reporting

*   `exclude_lines`: Lines excluded from coverage reporting.

#### Ruff Configuration

*   `line-length`: Maximum line length.
*   `target-version`: Target Python version for compatibility.
*   `fix`: Automatically fix linting issues.
*   `lint`: Configuration for linting rules, select options, and ignored rules.

### Development Setup

To install the ZlsNasDisplay project using Poetry:

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/zales/ZlsNasDisplay.git
    ```

2.  **Navigate to the Project Directory**:
    ```bash
    cd ZlsNasDisplay
    ```

3.  **Install Dependencies**:
    ```bash
    poetry install
    ```

4.  **(Optional) Activate Virtual Environment**:
    ```bash
    poetry shell
    ```

5.  **Run the Project**:
    ```bash
    # Display only
    poetry run python3 -m zlsnasdisplay

    # With web dashboard
    ENABLE_WEB_DASHBOARD=true poetry run python3 -m zlsnasdisplay
    ```

### Configuration

You can configure thresholds and other settings via environment variables:

```bash
# Display update timeout (seconds)
export DISPLAY_UPDATE_TIMEOUT=10

# Cache TTL values (seconds)
export DISPLAY_CACHE_TTL_INTERNET=30
export DISPLAY_CACHE_TTL_SIGNAL=60
export DISPLAY_CACHE_TTL_IP=3600

# Threshold values for critical highlighting
export THRESHOLD_CPU_HIGH=70        # CPU load warning threshold (%)
export THRESHOLD_CPU_CRITICAL=90    # CPU load critical threshold (%)
export THRESHOLD_TEMP_HIGH=70       # Temperature warning threshold (°C)
export THRESHOLD_TEMP_CRITICAL=85   # Temperature critical threshold (°C)
export THRESHOLD_MEM_HIGH=80        # Memory warning threshold (%)
export THRESHOLD_MEM_CRITICAL=95    # Memory critical threshold (%)
export THRESHOLD_DISK_HIGH=85       # Disk usage warning threshold (%)
export THRESHOLD_DISK_CRITICAL=95   # Disk usage critical threshold (%)

# Web dashboard (optional)
export ENABLE_WEB_DASHBOARD=true
export WEB_DASHBOARD_HOST=0.0.0.0
export WEB_DASHBOARD_PORT=8000

# Logging
export LOG_LEVEL=INFO

# Error tracking (optional)
export SENTRY_DSN=your-sentry-dsn
```

### Running as a Service

To run ZlsNasDisplay automatically on boot, create a systemd service:

1. Create service file at `/etc/systemd/system/zlsnasdisplay.service`:
    ```ini
    [Unit]
    Description=ZlsNasDisplay E-ink Monitor
    After=network.target

    [Service]
    Type=simple
    User=root
    WorkingDirectory=/path/to/ZlsNasDisplay
    Environment="ENABLE_WEB_DASHBOARD=true"
    Environment="LOG_LEVEL=INFO"
    ExecStart=/usr/bin/python3 -m zlsnasdisplay
    Restart=always
    RestartSec=10

    [Install]
    WantedBy=multi-user.target
    ```

2. Enable and start the service:
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable zlsnasdisplay
    sudo systemctl start zlsnasdisplay
    ```

3. Check service status:
    ```bash
    sudo systemctl status zlsnasdisplay
    sudo journalctl -u zlsnasdisplay -f
    ```

![Motiv](https://github.com/zales/ZlsNasDisplay/assets/832783/a1a764be-8ecd-4063-a75c-506135400a1f)

