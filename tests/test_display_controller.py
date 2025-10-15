from unittest.mock import MagicMock, patch

import pytest

from zlsnasdisplay.display_controller import DisplayController


@pytest.fixture
def mock_epd():
    """Fixture to mock the EPD display driver"""
    with patch("zlsnasdisplay.display_controller.epd2in9_V2.EPD") as mock:
        epd_instance = MagicMock()
        epd_instance.height = 128
        epd_instance.width = 296
        mock.return_value = epd_instance
        yield epd_instance


def test_display_controller_init(mock_epd):
    """Test DisplayController initialization"""
    controller = DisplayController()

    assert controller.epd is not None
    mock_epd.init.assert_called_once()


def test_update_display(mock_epd):
    """Test updating the display with an image"""
    controller = DisplayController()
    mock_image = MagicMock()
    mock_buffer = b"fake_buffer_data"
    mock_epd.get_buffer.return_value = mock_buffer

    controller.update_display(mock_image)

    mock_epd.get_buffer.assert_called_once_with(mock_image)
    mock_epd.display_partial.assert_called_once_with(mock_buffer)


def test_clear_display(mock_epd):
    """Test clearing the display"""
    controller = DisplayController()

    controller.clear_display()

    mock_epd.clear.assert_called_once_with(0xFF)


def test_sleep_display(mock_epd):
    """Test putting the display to sleep"""
    controller = DisplayController()

    controller.sleep_display()

    mock_epd.sleep.assert_called_once()


def test_display_controller_multiple_operations(mock_epd):
    """Test multiple display operations in sequence"""
    controller = DisplayController()
    mock_image = MagicMock()
    mock_buffer = b"fake_buffer"
    mock_epd.get_buffer.return_value = mock_buffer

    # Perform multiple operations
    controller.update_display(mock_image)
    controller.clear_display()
    controller.update_display(mock_image)
    controller.sleep_display()

    # Verify all operations were called correctly
    assert mock_epd.display_partial.call_count == 2
    assert mock_epd.clear.call_count == 1
    assert mock_epd.sleep.call_count == 1
