# ZlsNasDisplay

![display (10)](https://github.com/zales/ZlsNasDisplay/assets/832783/6e7828bc-3317-48c0-a1b5-804f8b1b86d2)
![display_sleep](https://github.com/zales/ZlsNasDisplay/assets/832783/63055923-21f6-4852-9ad6-2ac78c4181e7)


The ZlsNasDisplay application renders various system statistics onto the e-ink display, providing users with real-time insights into the Raspberry Pi-based NAS device's performance and connectivity. Here's a breakdown of the displayed information and their respective update frequencies:

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

## Hardware
Raspberry Pi (5 tested)

[Waveshare 2.9" e-ink display](https://www.waveshare.com/product/2.9inch-e-paper-module.htm)

### Wiring

All necessary information about the wiring and operation is available on the [waveshare wiki](https://www.waveshare.com/wiki/2.9inch_e-Paper_Module_Manual#Working_With_Raspberry_Pi)


## Development

### Dependencies

*   `python`: Python version required for the project (>=3.9).
*   `pillow`, `gpiozero`, `schedule`, `psutil`, `requests`: Python dependencies with their respective versions required for the project.
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

To install the ZlsNasDisplay project using Poetry, you can follow these steps:

1.  **Clone the Repository**: First, clone the repository containing the project's code from GitHub:
    
    bashCopy code
    
    `git clone https://github.com/zales/ZlsNasDisplay.git`
    
2.  **Navigate to the Project Directory**: Change your current directory to the root directory of the cloned project:
    
    bashCopy code
    
    `cd ZlsNasDisplay`
    
3.  **Install Dependencies**: Use Poetry to install the project's dependencies defined in the `pyproject.toml` file:
    
    bashCopy code
    
    `poetry install`
    
4.  **(Optional) Create a Virtual Environment**: If you prefer to isolate the project's dependencies, you can create a virtual environment with Poetry:
    
    bashCopy code
    
    `poetry shell`
    
5.  **Run the Project**: After installing the dependencies, you can run the ZlsNasDisplay project using Poetry. For example, if there's a script defined in the `pyproject.toml` file under `[tool.poetry.scripts]`, you can execute it as follows:
    
    bashCopy code
    
    `poetry run python3 zlsnasdisplay`

![Motiv](https://github.com/zales/ZlsNasDisplay/assets/832783/a1a764be-8ecd-4063-a75c-506135400a1f)

