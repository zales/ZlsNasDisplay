"""Tests for web dashboard module."""

from unittest import mock

import pytest
from fastapi.testclient import TestClient

from zlsnasdisplay.web_dashboard import MetricsCollector, create_app

# Use asyncio backend only
pytestmark = pytest.mark.anyio


class TestMetricsCollector:
    """Test MetricsCollector class."""

    @pytest.fixture(scope="class")
    def anyio_backend(self):
        """Use asyncio backend only."""
        return "asyncio"

    @mock.patch("zlsnasdisplay.web_dashboard.TrafficMonitor")
    @mock.patch("zlsnasdisplay.web_dashboard.SystemOperations")
    @mock.patch("zlsnasdisplay.web_dashboard.NetworkOperations")
    async def test_get_all_metrics_success(
        self, mock_network_ops, mock_system_ops, mock_traffic_monitor
    ):
        """Test successful metrics collection."""
        # Mock TrafficMonitor
        mock_traffic_instance = mock_traffic_monitor.return_value
        mock_traffic_instance.get_current_traffic.return_value = (10.5, "MB", 2.3, "MB")

        # Mock SystemOperations
        mock_sys_instance = mock_system_ops.return_value
        mock_sys_instance.get_cpu_load.return_value = 45
        mock_sys_instance.get_cpu_temperature.return_value = 55
        mock_system_ops.get_mem.return_value = 60
        mock_system_ops.get_nvme_usage.return_value = 70
        mock_system_ops.get_nvme_temp.return_value = 40
        mock_system_ops.get_fan_speed.return_value = 3000
        mock_system_ops.get_uptime.return_value = (5, 12, 30)
        mock_system_ops.check_updates.return_value = 3

        # Mock NetworkOperations
        mock_net_instance = mock_network_ops.return_value
        mock_net_instance.get_ip_address.return_value = "192.168.1.100"
        mock_net_instance.get_signal_strength.return_value = -65
        mock_net_instance.check_internet_connection.return_value = True

        collector = MetricsCollector(is_root=True)
        metrics = await collector.get_all_metrics()

        # Verify structure
        assert "timestamp" in metrics
        assert "cpu" in metrics
        assert "memory" in metrics
        assert "nvme" in metrics
        assert "fan" in metrics
        assert "network" in metrics
        assert "system" in metrics

        # Verify values
        assert metrics["cpu"]["load"] == 45
        assert metrics["cpu"]["temperature"] == 55
        assert metrics["memory"]["usage_percent"] == 60
        assert metrics["nvme"]["usage_percent"] == 70
        assert metrics["nvme"]["temperature"] == 40
        assert metrics["fan"]["speed_rpm"] == 3000
        assert metrics["network"]["ip_address"] == "192.168.1.100"
        assert metrics["network"]["signal_strength_dbm"] == -65
        assert metrics["network"]["internet_connected"] is True
        assert metrics["network"]["traffic"]["download_speed"] == 10.5
        assert metrics["network"]["traffic"]["download_unit"] == "MB"
        assert metrics["system"]["uptime"]["days"] == 5
        assert metrics["system"]["uptime"]["hours"] == 12
        assert metrics["system"]["updates_available"] == 3

    @mock.patch("zlsnasdisplay.web_dashboard.TrafficMonitor")
    @mock.patch("zlsnasdisplay.web_dashboard.SystemOperations")
    @mock.patch("zlsnasdisplay.web_dashboard.NetworkOperations")
    async def test_get_all_metrics_with_exception(
        self, mock_network_ops, mock_system_ops, mock_traffic_monitor
    ):
        """Test metrics collection with exception handling."""
        # Mock TrafficMonitor to raise exception
        mock_traffic_instance = mock_traffic_monitor.return_value
        mock_traffic_instance.get_current_traffic.side_effect = Exception("Network error")

        collector = MetricsCollector(is_root=False)
        metrics = await collector.get_all_metrics()

        # Should return error structure
        assert "error" in metrics
        assert "timestamp" in metrics
        assert "Network error" in metrics["error"]


class TestWebDashboardAPI:
    """Test web dashboard API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app(is_root=False)
        return TestClient(app)

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_root_endpoint_returns_html(self, client):
        """Test root endpoint returns HTML."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "ZlsNasDisplay Dashboard" in response.text
        assert "WebSocket" in response.text

    def test_metrics_endpoint(self, client):
        """Test metrics API endpoint."""
        response = client.get("/api/metrics")
        assert response.status_code == 200
        data = response.json()
        # Verify response structure
        assert "timestamp" in data
        assert "cpu" in data
        assert "memory" in data
        assert "nvme" in data
        assert "fan" in data
        assert "network" in data
        assert "system" in data

    def test_websocket_endpoint(self, client):
        """Test WebSocket endpoint."""
        with client.websocket_connect("/ws") as websocket:
            # Receive first message
            data = websocket.receive_json()
            # Verify response structure
            assert "timestamp" in data
            assert "cpu" in data
            assert "memory" in data
            assert "nvme" in data
            assert "fan" in data
            assert "network" in data
            assert "system" in data


class TestWebDashboardHTML:
    """Test web dashboard HTML content."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app(is_root=False)
        return TestClient(app)

    def test_html_contains_metric_elements(self, client):
        """Test HTML contains all metric display elements."""
        response = client.get("/")
        html = response.text

        # Check for metric IDs
        assert 'id="cpu-load"' in html
        assert 'id="cpu-temp"' in html
        assert 'id="memory-usage"' in html
        assert 'id="nvme-usage"' in html
        assert 'id="nvme-temp"' in html
        assert 'id="fan-speed"' in html
        assert 'id="ip-address"' in html
        assert 'id="signal-strength"' in html
        assert 'id="internet-status"' in html
        assert 'id="download-speed"' in html
        assert 'id="upload-speed"' in html
        assert 'id="uptime"' in html
        assert 'id="updates"' in html

    def test_html_contains_websocket_code(self, client):
        """Test HTML contains WebSocket connection code."""
        response = client.get("/")
        html = response.text

        assert "new WebSocket" in html
        assert "ws.onopen" in html
        assert "ws.onmessage" in html
        assert "ws.onerror" in html
        assert "ws.onclose" in html
        assert "connectWebSocket()" in html

    def test_html_contains_styles(self, client):
        """Test HTML contains CSS styles."""
        response = client.get("/")
        html = response.text

        assert "<style>" in html
        assert ".card" in html
        assert ".metric" in html
        assert ".grid" in html
