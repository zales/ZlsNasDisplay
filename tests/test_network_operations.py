#! /usr/bin/env python3

import socket
from unittest import mock

import pytest

from zlsnasdisplay.network_operations import NetworkOperations, TrafficMonitor


class TestNetworkOperations:
    """Tests for NetworkOperations class."""

    def test_check_internet_connection_success(self):
        """Test successful internet connection check via DNS."""
        with mock.patch("zlsnasdisplay.network_operations.socket.socket") as mock_socket_class:
            mock_socket_instance = mock.MagicMock()
            # Context manager support
            mock_socket_instance.__enter__ = mock.MagicMock(return_value=mock_socket_instance)
            mock_socket_instance.__exit__ = mock.MagicMock(return_value=False)
            mock_socket_class.return_value = mock_socket_instance

            result = NetworkOperations.check_internet_connection()

            assert result is True
            mock_socket_class.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)
            mock_socket_instance.settimeout.assert_called_once_with(3)
            mock_socket_instance.connect.assert_called_once_with(("8.8.8.8", 53))

    def test_check_internet_connection_os_error(self):
        """Test internet connection check with OS error."""
        with mock.patch("zlsnasdisplay.network_operations.socket.socket") as mock_socket_class:
            mock_socket_instance = mock.MagicMock()
            mock_socket_instance.__enter__ = mock.MagicMock(return_value=mock_socket_instance)
            mock_socket_instance.__exit__ = mock.MagicMock(return_value=False)
            mock_socket_instance.connect.side_effect = OSError("Connection refused")
            mock_socket_class.return_value = mock_socket_instance

            result = NetworkOperations.check_internet_connection()

            assert result is False

    def test_check_internet_connection_timeout(self):
        """Test internet connection check with timeout."""
        with mock.patch("zlsnasdisplay.network_operations.socket.socket") as mock_socket_class:
            mock_socket_instance = mock.MagicMock()
            mock_socket_instance.__enter__ = mock.MagicMock(return_value=mock_socket_instance)
            mock_socket_instance.__exit__ = mock.MagicMock(return_value=False)
            mock_socket_instance.connect.side_effect = socket.timeout("Timeout")
            mock_socket_class.return_value = mock_socket_instance

            result = NetworkOperations.check_internet_connection()

            assert result is False

    def test_get_signal_strength_success(self):
        """Test successful signal strength retrieval from /proc/net/wireless."""
        mock_file_content = """Inter-| sta-|   Quality        |   Discarded packets               | Missed | WE
 face | tus | link level noise |  nwid  crypt   frag  retry   misc | beacon | 22
wlan0: 0000   70.  -42.  -256        0      0      0      0      0        0
"""
        with mock.patch("builtins.open", mock.mock_open(read_data=mock_file_content)):
            result = NetworkOperations.get_signal_strength("wlan0")
            assert result == -42

    def test_get_signal_strength_interface_not_found(self):
        """Test signal strength retrieval when interface not in /proc/net/wireless."""
        mock_file_content = """Inter-| sta-|   Quality        |   Discarded packets               | Missed | WE
 face | tus | link level noise |  nwid  crypt   frag  retry   misc | beacon | 22
eth0: 0000   70.  -42.  -256        0      0      0      0      0        0
"""
        with mock.patch("builtins.open", mock.mock_open(read_data=mock_file_content)):
            result = NetworkOperations.get_signal_strength("wlan0")
            assert result is None

    def test_get_signal_strength_file_not_found(self):
        """Test signal strength retrieval when /proc/net/wireless doesn't exist."""
        with mock.patch("builtins.open", side_effect=FileNotFoundError()):
            result = NetworkOperations.get_signal_strength("wlan0")
            assert result is None

    def test_get_signal_strength_parse_error(self):
        """Test signal strength retrieval with parsing error."""
        mock_file_content = """Inter-| sta-|   Quality        |   Discarded packets
wlan0: invalid data
"""
        with mock.patch("builtins.open", mock.mock_open(read_data=mock_file_content)):
            result = NetworkOperations.get_signal_strength("wlan0")
            assert result is None

    def test_get_signal_strength_generic_exception(self):
        """Test signal strength retrieval with generic exception."""
        with mock.patch("builtins.open", side_effect=Exception("Unexpected error")):
            result = NetworkOperations.get_signal_strength("wlan0")
            assert result is None

    def test_get_ip_address_success(self):
        """Test successful IP address retrieval from interface."""
        mock_addr = mock.MagicMock()
        mock_addr.family = socket.AF_INET
        mock_addr.address = "192.168.1.100"

        mock_addrs = {"wlan0": [mock_addr]}

        with mock.patch("zlsnasdisplay.network_operations.psutil.net_if_addrs") as mock_net_if:
            mock_net_if.return_value = mock_addrs

            result = NetworkOperations.get_ip_address("wlan0")

            assert result == "192.168.1.100"

    def test_get_ip_address_interface_not_found(self):
        """Test IP address retrieval when interface doesn't exist."""
        mock_addrs = {"eth0": []}

        with mock.patch("zlsnasdisplay.network_operations.psutil.net_if_addrs") as mock_net_if:
            mock_net_if.return_value = mock_addrs

            result = NetworkOperations.get_ip_address("wlan0")

            assert result is None

    def test_get_ip_address_skip_loopback(self):
        """Test IP address retrieval skips loopback addresses."""
        mock_addr_loopback = mock.MagicMock()
        mock_addr_loopback.family = socket.AF_INET
        mock_addr_loopback.address = "127.0.0.1"

        mock_addr_valid = mock.MagicMock()
        mock_addr_valid.family = socket.AF_INET
        mock_addr_valid.address = "192.168.1.100"

        mock_addrs = {"wlan0": [mock_addr_loopback, mock_addr_valid]}

        with mock.patch("zlsnasdisplay.network_operations.psutil.net_if_addrs") as mock_net_if:
            mock_net_if.return_value = mock_addrs

            result = NetworkOperations.get_ip_address("wlan0")

            assert result == "192.168.1.100"

    def test_get_ip_address_fallback_to_eth0(self):
        """Test IP address retrieval falls back to eth0 when wlan0 not available."""
        mock_addr_eth = mock.MagicMock()
        mock_addr_eth.family = socket.AF_INET
        mock_addr_eth.address = "192.168.1.200"

        mock_addrs = {"eth0": [mock_addr_eth], "lo": []}

        with mock.patch("zlsnasdisplay.network_operations.psutil.net_if_addrs") as mock_net_if:
            mock_net_if.return_value = mock_addrs

            # Should fallback to eth0 when wlan0 not found
            result = NetworkOperations.get_ip_address("wlan0")

            assert result == "192.168.1.200"

    def test_get_ip_address_skip_docker(self):
        """Test IP address retrieval returns first available private IP when no public IP exists."""
        mock_addr_docker = mock.MagicMock()
        mock_addr_docker.family = socket.AF_INET
        mock_addr_docker.address = "172.17.0.1"

        mock_addr_valid = mock.MagicMock()
        mock_addr_valid.family = socket.AF_INET
        mock_addr_valid.address = "192.168.1.100"

        mock_addrs = {"docker0": [mock_addr_docker], "eth0": [mock_addr_valid], "lo": []}

        with mock.patch("zlsnasdisplay.network_operations.psutil.net_if_addrs") as mock_net_if:
            mock_net_if.return_value = mock_addrs

            result = NetworkOperations.get_ip_address("wlan0")

            # Both IPs are private, so either is acceptable (dictionary iteration order not guaranteed)
            assert result in ("192.168.1.100", "172.17.0.1")

    def test_get_ip_address_no_ipv4(self):
        """Test IP address retrieval when no IPv4 address available."""
        mock_addr_ipv6 = mock.MagicMock()
        mock_addr_ipv6.family = socket.AF_INET6
        mock_addr_ipv6.address = "fe80::1"

        mock_addrs = {"wlan0": [mock_addr_ipv6]}

        with mock.patch("zlsnasdisplay.network_operations.psutil.net_if_addrs") as mock_net_if:
            mock_net_if.return_value = mock_addrs

            result = NetworkOperations.get_ip_address("wlan0")

            assert result is None

    def test_get_ip_address_generic_exception(self):
        """Test IP address retrieval with generic exception."""
        with mock.patch("zlsnasdisplay.network_operations.psutil.net_if_addrs") as mock_net_if:
            mock_net_if.side_effect = Exception("Unexpected error")

            result = NetworkOperations.get_ip_address()

            assert result is None


class TestTrafficMonitor:
    """Tests for TrafficMonitor class."""

    def test_get_current_traffic_first_call(self):
        """Test traffic monitoring on first call (returns zeros)."""
        mock_net_io = mock.MagicMock()
        mock_net_io.bytes_recv = 1000000
        mock_net_io.bytes_sent = 500000

        with mock.patch("zlsnasdisplay.network_operations.psutil.net_io_counters") as mock_net:
            with mock.patch("zlsnasdisplay.network_operations.time.time") as mock_time:
                mock_net.return_value = mock_net_io
                mock_time.return_value = 100.0

                monitor = TrafficMonitor()
                download_speed, download_unit, upload_speed, upload_unit = (
                    monitor.get_current_traffic()
                )

                # First call should return zeros
                assert download_speed == 0.0
                assert download_unit == "B"
                assert upload_speed == 0.0
                assert upload_unit == "B"

    def test_get_current_traffic_success(self):
        """Test successful traffic monitoring with cached measurements."""
        mock_net_io_start = mock.MagicMock()
        mock_net_io_start.bytes_recv = 1000000
        mock_net_io_start.bytes_sent = 500000

        mock_net_io_end = mock.MagicMock()
        mock_net_io_end.bytes_recv = 1500000  # 500KB downloaded
        mock_net_io_end.bytes_sent = 750000  # 250KB uploaded

        with mock.patch("zlsnasdisplay.network_operations.psutil.net_io_counters") as mock_net_io:
            with mock.patch("zlsnasdisplay.network_operations.time.time") as mock_time:
                mock_net_io.side_effect = [mock_net_io_start, mock_net_io_end]
                mock_time.side_effect = [100.0, 101.0]  # 1 second interval

                monitor = TrafficMonitor()
                # First call - initialize
                monitor.get_current_traffic()
                # Second call - measure
                download_speed, download_unit, upload_speed, upload_unit = (
                    monitor.get_current_traffic()
                )

                assert download_speed == pytest.approx(488.28, rel=0.01)  # ~500000/1024
                assert download_unit == "kB"
                assert upload_speed == pytest.approx(244.14, rel=0.01)  # ~250000/1024
                assert upload_unit == "kB"

    def test_get_current_traffic_bytes(self):
        """Test traffic monitoring with bytes unit."""
        mock_net_io_start = mock.MagicMock()
        mock_net_io_start.bytes_recv = 1000
        mock_net_io_start.bytes_sent = 500

        mock_net_io_end = mock.MagicMock()
        mock_net_io_end.bytes_recv = 1500  # 500B downloaded
        mock_net_io_end.bytes_sent = 750  # 250B uploaded

        with mock.patch("zlsnasdisplay.network_operations.psutil.net_io_counters") as mock_net_io:
            with mock.patch("zlsnasdisplay.network_operations.time.time") as mock_time:
                mock_net_io.side_effect = [mock_net_io_start, mock_net_io_end]
                mock_time.side_effect = [100.0, 101.0]  # 1 second interval

                monitor = TrafficMonitor()
                monitor.get_current_traffic()  # First call
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
            with mock.patch("zlsnasdisplay.network_operations.time.time") as mock_time:
                mock_net_io.side_effect = [mock_net_io_start, mock_net_io_end]
                mock_time.side_effect = [100.0, 101.0]  # 1 second interval

                monitor = TrafficMonitor()
                monitor.get_current_traffic()  # First call
                download_speed, download_unit, upload_speed, upload_unit = (
                    monitor.get_current_traffic()
                )

                assert download_speed == pytest.approx(5.0, rel=0.01)
                assert download_unit == "MB"
                assert upload_speed == pytest.approx(2.5, rel=0.01)
                assert upload_unit == "MB"

    def test_get_current_traffic_too_soon(self):
        """Test traffic monitoring when called too soon (< 0.1s)."""
        mock_net_io = mock.MagicMock()
        mock_net_io.bytes_recv = 1000000
        mock_net_io.bytes_sent = 500000

        with mock.patch("zlsnasdisplay.network_operations.psutil.net_io_counters") as mock_net:
            with mock.patch("zlsnasdisplay.network_operations.time.time") as mock_time:
                mock_net.return_value = mock_net_io
                mock_time.side_effect = [100.0, 100.05]  # Only 0.05s interval

                monitor = TrafficMonitor()
                monitor.get_current_traffic()  # First call
                download_speed, download_unit, upload_speed, upload_unit = (
                    monitor.get_current_traffic()
                )

                # Should return zeros when called too soon
                assert download_speed == 0.0
                assert download_unit == "B"
                assert upload_speed == 0.0
                assert upload_unit == "B"

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
