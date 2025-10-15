#! /usr/bin/env python3

import socket
import subprocess
from unittest import mock

import pytest
import requests

from zlsnasdisplay.network_operations import NetworkOperations, TrafficMonitor


class TestNetworkOperations:
    """Tests for NetworkOperations class."""

    def test_check_internet_connection_success(self):
        """Test successful internet connection check."""
        with mock.patch("zlsnasdisplay.network_operations.requests.get") as mock_get:
            mock_response = mock.MagicMock()
            mock_response.raise_for_status = mock.MagicMock()
            mock_get.return_value = mock_response

            result = NetworkOperations.check_internet_connection()

            assert result is True
            mock_get.assert_called_once_with("https://google.com", timeout=5)

    def test_check_internet_connection_request_exception(self):
        """Test internet connection check with request exception."""
        with mock.patch("zlsnasdisplay.network_operations.requests.get") as mock_get:
            mock_get.side_effect = requests.RequestException("Connection error")

            result = NetworkOperations.check_internet_connection()

            assert result is False

    def test_check_internet_connection_timeout(self):
        """Test internet connection check with timeout."""
        with mock.patch("zlsnasdisplay.network_operations.requests.get") as mock_get:
            mock_get.side_effect = requests.Timeout("Timeout error")

            result = NetworkOperations.check_internet_connection()

            assert result is False

    def test_check_internet_connection_generic_exception(self):
        """Test internet connection check with generic exception."""
        with mock.patch("zlsnasdisplay.network_operations.requests.get") as mock_get:
            mock_get.side_effect = Exception("Unexpected error")

            result = NetworkOperations.check_internet_connection()

            assert result is False

    def test_get_signal_strength_success(self):
        """Test successful signal strength retrieval."""
        mock_output = """wlan0     IEEE 802.11  ESSID:"TestNetwork"
                  Mode:Managed  Frequency:5.18 GHz  Access Point: XX:XX:XX:XX:XX:XX
                  Bit Rate=866.7 Mb/s   Tx-Power=22 dBm
                  Retry short limit:7   RTS thr:off   Fragment thr:off
                  Power Management:on
                  Link Quality=70/70  Signal level=-42 dBm
                  Rx invalid nwid:0  Rx invalid crypt:0  Rx invalid frag:0
                  Tx excessive retries:0  Invalid misc:0   Missed beacon:0"""

        with mock.patch(
            "zlsnasdisplay.network_operations.subprocess.check_output"
        ) as mock_subprocess:
            mock_subprocess.return_value = mock_output

            result = NetworkOperations.get_signal_strength("wlan0")

            assert result == -42
            mock_subprocess.assert_called_once()

    def test_get_signal_strength_no_signal(self):
        """Test signal strength retrieval when no signal info present."""
        mock_output = """wlan0     IEEE 802.11  ESSID:off/any
                  Mode:Managed  Access Point: Not-Associated"""

        with mock.patch(
            "zlsnasdisplay.network_operations.subprocess.check_output"
        ) as mock_subprocess:
            mock_subprocess.return_value = mock_output

            result = NetworkOperations.get_signal_strength("wlan0")

            assert result is None

    def test_get_signal_strength_called_process_error(self):
        """Test signal strength retrieval with subprocess error."""
        with mock.patch(
            "zlsnasdisplay.network_operations.subprocess.check_output"
        ) as mock_subprocess:
            mock_subprocess.side_effect = subprocess.CalledProcessError(1, "iwconfig", "Error")

            result = NetworkOperations.get_signal_strength("wlan0")

            assert result is None

    def test_get_signal_strength_timeout(self):
        """Test signal strength retrieval with timeout."""
        with mock.patch(
            "zlsnasdisplay.network_operations.subprocess.check_output"
        ) as mock_subprocess:
            mock_subprocess.side_effect = subprocess.TimeoutExpired("iwconfig", 5)

            result = NetworkOperations.get_signal_strength("wlan0")

            assert result is None

    def test_get_signal_strength_file_not_found(self):
        """Test signal strength retrieval when iwconfig not found."""
        with mock.patch(
            "zlsnasdisplay.network_operations.subprocess.check_output"
        ) as mock_subprocess:
            mock_subprocess.side_effect = FileNotFoundError("iwconfig not found")

            result = NetworkOperations.get_signal_strength("wlan0")

            assert result is None

    def test_get_signal_strength_parse_error(self):
        """Test signal strength retrieval with parsing error."""
        mock_output = """wlan0     Signal level=INVALID dBm"""

        with mock.patch(
            "zlsnasdisplay.network_operations.subprocess.check_output"
        ) as mock_subprocess:
            mock_subprocess.return_value = mock_output

            result = NetworkOperations.get_signal_strength("wlan0")

            assert result is None

    def test_get_ip_address_success(self):
        """Test successful IP address retrieval."""
        with mock.patch("zlsnasdisplay.network_operations.socket.gethostname") as mock_hostname:
            with mock.patch(
                "zlsnasdisplay.network_operations.socket.gethostbyname"
            ) as mock_hostbyname:
                mock_hostname.return_value = "test-pi"
                mock_hostbyname.return_value = "192.168.1.100"

                result = NetworkOperations.get_ip_address()

                assert result == "192.168.1.100"
                mock_hostname.assert_called_once()
                mock_hostbyname.assert_called_once_with("test-pi")

    def test_get_ip_address_gaierror(self):
        """Test IP address retrieval with socket.gaierror."""
        with mock.patch("zlsnasdisplay.network_operations.socket.gethostname") as mock_hostname:
            with mock.patch(
                "zlsnasdisplay.network_operations.socket.gethostbyname"
            ) as mock_hostbyname:
                mock_hostname.return_value = "test-pi"
                mock_hostbyname.side_effect = socket.gaierror("Name resolution error")

                result = NetworkOperations.get_ip_address()

                assert result is None

    def test_get_ip_address_generic_exception(self):
        """Test IP address retrieval with generic exception."""
        with mock.patch("zlsnasdisplay.network_operations.socket.gethostname") as mock_hostname:
            mock_hostname.side_effect = Exception("Unexpected error")

            result = NetworkOperations.get_ip_address()

            assert result is None


class TestTrafficMonitor:
    """Tests for TrafficMonitor class."""

    def test_get_current_traffic_success(self):
        """Test successful traffic monitoring."""
        mock_net_io_start = mock.MagicMock()
        mock_net_io_start.bytes_recv = 1000000
        mock_net_io_start.bytes_sent = 500000

        mock_net_io_end = mock.MagicMock()
        mock_net_io_end.bytes_recv = 1500000  # 500KB downloaded
        mock_net_io_end.bytes_sent = 750000  # 250KB uploaded

        with mock.patch("zlsnasdisplay.network_operations.psutil.net_io_counters") as mock_net_io:
            with mock.patch("zlsnasdisplay.network_operations.time.sleep") as mock_sleep:
                mock_net_io.side_effect = [mock_net_io_start, mock_net_io_end]

                monitor = TrafficMonitor()
                download_speed, download_unit, upload_speed, upload_unit = (
                    monitor.get_current_traffic()
                )

                assert download_speed == pytest.approx(488.28, rel=0.01)  # ~500000/1024
                assert download_unit == "kB"
                assert upload_speed == pytest.approx(244.14, rel=0.01)  # ~250000/1024
                assert upload_unit == "kB"
                mock_sleep.assert_called_once_with(1)

    def test_get_current_traffic_bytes(self):
        """Test traffic monitoring with bytes unit."""
        mock_net_io_start = mock.MagicMock()
        mock_net_io_start.bytes_recv = 1000
        mock_net_io_start.bytes_sent = 500

        mock_net_io_end = mock.MagicMock()
        mock_net_io_end.bytes_recv = 1500  # 500B downloaded
        mock_net_io_end.bytes_sent = 750  # 250B uploaded

        with mock.patch("zlsnasdisplay.network_operations.psutil.net_io_counters") as mock_net_io:
            with mock.patch("zlsnasdisplay.network_operations.time.sleep"):
                mock_net_io.side_effect = [mock_net_io_start, mock_net_io_end]

                monitor = TrafficMonitor()
                download_speed, download_unit, upload_speed, upload_unit = (
                    monitor.get_current_traffic()
                )

                assert download_speed == 500.0
                assert download_unit == "B"
                assert upload_speed == 250.0
                assert upload_unit == "B"

    def test_get_current_traffic_megabytes(self):
        """Test traffic monitoring with megabytes unit."""
        mock_net_io_start = mock.MagicMock()
        mock_net_io_start.bytes_recv = 1000000
        mock_net_io_start.bytes_sent = 500000

        mock_net_io_end = mock.MagicMock()
        # 5MB downloaded, 2.5MB uploaded
        mock_net_io_end.bytes_recv = 1000000 + 5 * 1024 * 1024
        mock_net_io_end.bytes_sent = 500000 + 2.5 * 1024 * 1024

        with mock.patch("zlsnasdisplay.network_operations.psutil.net_io_counters") as mock_net_io:
            with mock.patch("zlsnasdisplay.network_operations.time.sleep"):
                mock_net_io.side_effect = [mock_net_io_start, mock_net_io_end]

                monitor = TrafficMonitor()
                download_speed, download_unit, upload_speed, upload_unit = (
                    monitor.get_current_traffic()
                )

                assert download_speed == pytest.approx(5.0, rel=0.01)
                assert download_unit == "MB"
                assert upload_speed == pytest.approx(2.5, rel=0.01)
                assert upload_unit == "MB"

    def test_get_current_traffic_exception(self):
        """Test traffic monitoring with exception."""
        with mock.patch("zlsnasdisplay.network_operations.psutil.net_io_counters") as mock_net_io:
            mock_net_io.side_effect = AttributeError("Test error")

            monitor = TrafficMonitor()
            download_speed, download_unit, upload_speed, upload_unit = monitor.get_current_traffic()

            assert download_speed == 0.0
            assert download_unit == "B"
            assert upload_speed == 0.0
            assert upload_unit == "B"

    def test_choose_unit_bytes(self):
        """Test unit choice for bytes."""
        speed, unit = TrafficMonitor._choose_unit(512.0)
        assert speed == 512.0
        assert unit == "B"

    def test_choose_unit_kilobytes(self):
        """Test unit choice for kilobytes."""
        speed, unit = TrafficMonitor._choose_unit(1536.0)  # 1.5 KB
        assert speed == pytest.approx(1.5, rel=0.01)
        assert unit == "kB"

    def test_choose_unit_megabytes(self):
        """Test unit choice for megabytes."""
        speed, unit = TrafficMonitor._choose_unit(2 * 1024 * 1024)  # 2 MB
        assert speed == pytest.approx(2.0, rel=0.01)
        assert unit == "MB"

    def test_choose_unit_gigabytes(self):
        """Test unit choice for gigabytes."""
        speed, unit = TrafficMonitor._choose_unit(3 * 1024 * 1024 * 1024)  # 3 GB
        assert speed == pytest.approx(3.0, rel=0.01)
        assert unit == "GB"
