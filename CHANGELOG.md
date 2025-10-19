# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Placeholder for upcoming features

### Changed
- Placeholder for changes

### Fixed
- Placeholder for bug fixes

## [3.0.0] - 2025-01-XX

### Added
- Matter/CHIP protocol integration for smart home compatibility
- QR code commissioning for easy Matter device setup
- CPU and NVMe temperature sensors exposed via Matter
- Web dashboard with real-time metrics via WebSocket
- FastAPI-based REST API for metrics
- Comprehensive test coverage (84+ tests)
- Hardware dependency mocking for CI/CD
- Automated release workflow with PyInstaller

### Changed
- Refactored Waveshare driver to use Pythonic exceptions instead of C-style return codes
- Improved event loop with smart sleep timing based on Matter status
- Optimized display rendering with better layout (QR code left, text right)
- CircuitMatter dependency now installed from GitHub
- Made lgpio optional for non-Raspberry Pi environments

### Fixed
- Critical bug in digital_read() returning constants instead of GPIO values
- QR code layout overlap issue on Matter commissioning screen
- CI test failures with proper hardware mocking
- Code formatting issues with ruff

### Dependencies
- Added CircuitMatter from GitHub
- Added httpx for FastAPI testing
- Made lgpio optional (hardware-specific)

[Unreleased]: https://github.com/zales/ZlsNasDisplay/compare/v3.0.0...HEAD
[3.0.0]: https://github.com/zales/ZlsNasDisplay/releases/tag/v3.0.0
