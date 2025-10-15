import os
from unittest.mock import MagicMock, Mock, patch

import pytest
from PIL import Image, ImageDraw, ImageFont

from zlsnasdisplay.display_renderer import DisplayRenderer


@pytest.fixture
def mock_display_controller():
    """Fixture to mock DisplayController"""
    with patch("zlsnasdisplay.display_renderer.DisplayController") as mock:
        controller_instance = MagicMock()
        controller_instance.epd.height = 128
        controller_instance.epd.width = 296
        mock.return_value = controller_instance
        yield controller_instance


@pytest.fixture
def mock_system_operations():
    """Fixture to mock SystemOperations"""
    with patch("zlsnasdisplay.display_renderer.SystemOperations") as mock:
        instance = MagicMock()
        instance.get_cpu_load.return_value = 42
        instance.get_cpu_temperature.return_value = 55
        instance.check_updates.return_value = 5
        instance.get_mem.return_value = 67
        instance.get_nvme_usage.return_value = 80
        instance.get_nvme_temp.return_value = 45
        instance.get_fan_speed.return_value = 3500
        instance.get_uptime.return_value = (1, 12, 34)
        mock.return_value = instance
        yield mock


@pytest.fixture
def mock_network_operations():
    """Fixture to mock NetworkOperations"""
    with patch("zlsnasdisplay.display_renderer.NetworkOperations") as mock:
        mock.get_ip_address.return_value = "192.168.1.100"
        mock.get_signal_strength.return_value = -50
        mock.check_internet_connection.return_value = True
        yield mock


@pytest.fixture
def mock_traffic_monitor():
    """Fixture to mock TrafficMonitor"""
    with patch("zlsnasdisplay.display_renderer.TrafficMonitor") as mock:
        instance = MagicMock()
        instance.get_current_traffic.return_value = (10.5, "MB", 2.3, "MB")
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_font():
    """Fixture to create a proper mock font"""
    font_mock = MagicMock()
    font_mock.getmask2.return_value = (b"", (0, 0, 10, 10))
    font_mock.getsize.return_value = (10, 10)
    return font_mock


@pytest.fixture
def mock_image_draw():
    """Fixture to mock ImageDraw"""
    with patch("zlsnasdisplay.display_renderer.ImageDraw.Draw") as mock:
        draw_instance = MagicMock()
        mock.return_value = draw_instance
        yield draw_instance


@pytest.fixture
def renderer(mock_display_controller, mock_traffic_monitor, mock_font, mock_image_draw):
    """Fixture to create a DisplayRenderer instance with mocked dependencies"""
    with patch("os.path.exists", return_value=True), patch(
        "zlsnasdisplay.display_renderer.ImageFont.truetype"
    ) as mock_truetype:
        mock_truetype.return_value = mock_font
        renderer = DisplayRenderer(display_image_path=None, is_root=False)
        yield renderer


def test_display_renderer_init(mock_display_controller, mock_traffic_monitor, mock_font, mock_image_draw):
    """Test DisplayRenderer initialization"""
    with patch("os.path.exists", return_value=True), patch(
        "zlsnasdisplay.display_renderer.ImageFont.truetype"
    ) as mock_truetype:
        mock_truetype.return_value = mock_font

        renderer = DisplayRenderer(display_image_path="/tmp/display.bmp", is_root=True)

        assert renderer.display_image_path == "/tmp/display.bmp"
        assert renderer.is_root is True
        assert renderer.traffic_monitor is not None
        assert renderer.image is not None
        assert renderer.draw is not None
        mock_display_controller.clear_display.assert_called_once()


def test_load_font_success(mock_display_controller, mock_traffic_monitor, mock_font, mock_image_draw):
    """Test successful font loading"""
    with patch("os.path.exists", return_value=True), patch(
        "zlsnasdisplay.display_renderer.ImageFont.truetype"
    ) as mock_truetype:
        mock_font_instance = MagicMock()
        mock_font_instance.getmask2.return_value = (b"", (0, 0, 10, 10))
        mock_truetype.return_value = mock_font_instance

        renderer = DisplayRenderer(display_image_path=None, is_root=False)
        fontdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fonts")

        font = renderer._load_font(fontdir, "Ubuntu-Regular.ttf", 24)

        assert font == mock_font_instance


def test_load_font_fallback_on_missing_file(mock_display_controller, mock_traffic_monitor, mock_font, mock_image_draw):
    """Test font loading falls back to default when file is missing"""
    with patch("os.path.exists") as mock_exists, patch(
        "zlsnasdisplay.display_renderer.ImageFont.truetype"
    ) as mock_truetype, patch(
        "zlsnasdisplay.display_renderer.ImageFont.load_default"
    ) as mock_default:
        # Fonts during init exist, but the test font doesn't
        mock_exists.side_effect = lambda path: "NonExistent" not in path
        mock_truetype.return_value = mock_font
        mock_default.return_value = mock_font

        renderer = DisplayRenderer(display_image_path=None, is_root=False)
        fontdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fonts")

        font = renderer._load_font(fontdir, "NonExistent.ttf", 24)

        # Should return default font
        assert font is not None
        mock_default.assert_called()


def test_load_font_fallback_on_oserror(mock_display_controller, mock_traffic_monitor, mock_font, mock_image_draw):
    """Test font loading falls back to default on OSError"""
    with patch("os.path.exists", return_value=True), patch(
        "zlsnasdisplay.display_renderer.ImageFont.truetype"
    ) as mock_truetype, patch(
        "zlsnasdisplay.display_renderer.ImageFont.load_default"
    ) as mock_default:
        # First calls during init should succeed
        mock_truetype.side_effect = [mock_font] * 7 + [OSError("Font error")]
        mock_default.return_value = mock_font

        renderer = DisplayRenderer(display_image_path=None, is_root=False)
        fontdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fonts")

        font = renderer._load_font(fontdir, "Ubuntu-Regular.ttf", 24)

        # Should return default font
        assert font is not None
        mock_default.assert_called_once()


def test_render_grid(renderer, mock_image_draw):
    """Test rendering the display grid"""
    renderer.render_grid()

    # Verify that drawing operations were performed
    assert renderer.image is not None
    assert renderer.draw is not None
    # Verify draw methods were called
    assert mock_image_draw.rectangle.called
    assert mock_image_draw.line.called
    assert mock_image_draw.text.called


def test_render_cpu_load(renderer, mock_system_operations):
    """Test rendering CPU load"""
    renderer.render_cpu_load()

    # Verify SystemOperations was called
    mock_system_operations.return_value.get_cpu_load.assert_called()
    mock_system_operations.return_value.get_cpu_temperature.assert_called()


def test_get_updates_with_updates(renderer, mock_system_operations):
    """Test rendering system updates when updates are available"""
    mock_system_operations.return_value.check_updates.return_value = 5

    renderer.get_updates()

    mock_system_operations.return_value.check_updates.assert_called_with(False)


def test_get_updates_no_updates(renderer, mock_system_operations):
    """Test rendering system updates when no updates available"""
    mock_system_operations.return_value.check_updates.return_value = 0

    renderer.get_updates()

    mock_system_operations.return_value.check_updates.assert_called_with(False)


def test_check_net_connected(renderer, mock_network_operations):
    """Test checking network when internet is connected"""
    mock_network_operations.check_internet_connection.return_value = True

    renderer.check_net()

    mock_network_operations.check_internet_connection.assert_called()


def test_check_net_disconnected(renderer, mock_network_operations):
    """Test checking network when internet is disconnected"""
    mock_network_operations.check_internet_connection.return_value = False

    renderer.check_net()

    mock_network_operations.check_internet_connection.assert_called()


def test_render_signal_strength_with_signal(renderer, mock_network_operations):
    """Test rendering signal strength when signal is present"""
    mock_network_operations.get_signal_strength.return_value = -50

    renderer.render_signal_strength()

    mock_network_operations.get_signal_strength.assert_called()


def test_render_signal_strength_no_signal(renderer, mock_network_operations):
    """Test rendering signal strength when no signal"""
    mock_network_operations.get_signal_strength.return_value = None

    renderer.render_signal_strength()

    mock_network_operations.get_signal_strength.assert_called()


def test_render_mem(renderer, mock_system_operations):
    """Test rendering memory stats"""
    mock_system_operations.get_mem.return_value = 67

    renderer.render_mem()

    mock_system_operations.get_mem.assert_called()


def test_render_nvme_stats(renderer, mock_system_operations):
    """Test rendering NVMe stats"""
    mock_system_operations.get_nvme_usage.return_value = 80
    mock_system_operations.get_nvme_temp.return_value = 45

    renderer.render_nvme_stats()

    mock_system_operations.get_nvme_usage.assert_called()
    mock_system_operations.get_nvme_temp.assert_called()


def test_render_fan_speed(renderer, mock_system_operations):
    """Test rendering fan speed"""
    mock_system_operations.get_fan_speed.return_value = 3500

    renderer.render_fan_speed()

    mock_system_operations.get_fan_speed.assert_called()


def test_render_ip_address_with_ip(renderer, mock_network_operations):
    """Test rendering IP address when available"""
    mock_network_operations.get_ip_address.return_value = "192.168.1.100"

    renderer.render_ip_address()

    mock_network_operations.get_ip_address.assert_called()


def test_render_ip_address_no_ip(renderer, mock_network_operations):
    """Test rendering IP address when not available"""
    mock_network_operations.get_ip_address.return_value = None

    renderer.render_ip_address()

    mock_network_operations.get_ip_address.assert_called()


def test_render_uptime(renderer, mock_system_operations):
    """Test rendering system uptime"""
    mock_system_operations.get_uptime.return_value = (1, 12, 34)

    renderer.render_uptime()

    mock_system_operations.get_uptime.assert_called()


def test_render_current_traffic(renderer):
    """Test rendering current network traffic"""
    renderer.traffic_monitor.get_current_traffic.return_value = (10.5, "MB", 2.3, "MB")

    renderer.render_current_traffic()

    renderer.traffic_monitor.get_current_traffic.assert_called()


def test_update_display_and_save_image_no_path(renderer, mock_display_controller):
    """Test updating display without saving image"""
    renderer.display_image_path = None

    renderer.update_display_and_save_image()

    mock_display_controller.update_display.assert_called_once()


def test_update_display_and_save_image_with_path(renderer, mock_display_controller):
    """Test updating display and saving image to file"""
    renderer.display_image_path = "/tmp/test_display.bmp"

    with patch.object(renderer.image, "save") as mock_save:
        renderer.update_display_and_save_image()

        mock_display_controller.update_display.assert_called_once()
        mock_save.assert_called_once_with("/tmp/test_display.bmp", "BMP")


def test_go_to_sleep(renderer, mock_display_controller):
    """Test sleep display rendering"""
    renderer.go_to_sleep()

    # Verify sleep was called on display controller
    mock_display_controller.sleep_display.assert_called_once()
    mock_display_controller.update_display.assert_called()


def test_startup(renderer, mock_display_controller):
    """Test startup display rendering"""
    renderer.startup()

    # Verify display was updated
    mock_display_controller.update_display.assert_called()


def test_traffic_monitor_instance_reused(renderer):
    """Test that TrafficMonitor instance is reused across calls"""
    traffic_monitor_instance = renderer.traffic_monitor

    renderer.render_current_traffic()
    renderer.render_current_traffic()

    # Verify same instance is used
    assert renderer.traffic_monitor is traffic_monitor_instance
    assert renderer.traffic_monitor.get_current_traffic.call_count == 2
