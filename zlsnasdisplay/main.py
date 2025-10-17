#! /usr/bin/env python3

import logging
import signal
import sys
import threading
import time

import schedule

from zlsnasdisplay.config import Config
from zlsnasdisplay.display_renderer import DisplayRenderer

# Configure logging level
logging.basicConfig(level=Config.LOG_LEVEL)

if Config.SENTRY_DSN:
    import sentry_sdk

    # Initialize Sentry for error tracking
    sentry_sdk.init(Config.SENTRY_DSN)

# Check root privileges
if not Config.is_root():
    logging.warning("The script does not run as root. Cannot perform apt update!")

display_renderer = DisplayRenderer(Config.DISPLAY_IMAGE_PATH, Config.is_root())

# Global reference for web server thread
web_server_thread = None


# Define signal_handler function to catch SIGINT (Ctrl+C)
def signal_handler(sig: int, frame: object) -> None:
    """Signal handler function to catch SIGINT (Ctrl+C) and exit the program."""
    logging.info("Exiting the program...")
    # Clear all scheduled jobs
    schedule.clear()

    display_renderer.go_to_sleep()

    sys.exit(0)


def start_web_dashboard() -> None:
    """Start the web dashboard in a separate thread."""
    try:
        from zlsnasdisplay.web_dashboard import run_server

        logging.info(
            f"Starting web dashboard on http://{Config.WEB_DASHBOARD_HOST}:{Config.WEB_DASHBOARD_PORT}"
        )
        run_server(
            host=Config.WEB_DASHBOARD_HOST,
            port=Config.WEB_DASHBOARD_PORT,
            is_root=Config.is_root(),
        )
    except Exception as e:
        logging.error(f"Failed to start web dashboard: {e}", exc_info=True)


def main() -> int:
    """Main function to run the program."""
    global web_server_thread

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGHUP, signal_handler)

    # Start web dashboard if enabled
    if Config.ENABLE_WEB_DASHBOARD:
        # Import FastAPI in main thread to avoid Pydantic initialization issues
        try:
            from zlsnasdisplay.web_dashboard import run_server  # noqa: F401
        except ImportError as e:
            logging.error(f"Failed to import web dashboard: {e}")
            logging.info("Continuing without web dashboard")
        else:
            logging.info("Web dashboard enabled - starting in background thread")
            web_server_thread = threading.Thread(target=start_web_dashboard, daemon=True)
            web_server_thread.start()
    else:
        logging.info(
            "Web dashboard disabled. Set ENABLE_WEB_DASHBOARD=true to enable it."
        )

    display_renderer.startup()

    # Render current traffic every 10 seconds
    schedule.every(10).seconds.do(display_renderer.render_current_traffic)
    # Render fan speed every 10 seconds
    schedule.every(10).seconds.do(display_renderer.render_fan_speed)
    # Render CPU load every 30 seconds
    schedule.every(30).seconds.do(display_renderer.render_cpu_load)
    # Render current traffic every 30 seconds
    schedule.every(30).seconds.do(display_renderer.check_net)
    # Render signal strength every minute
    schedule.every(1).minutes.do(display_renderer.render_signal_strength)
    # Render memory usage every minute
    schedule.every(1).minutes.do(display_renderer.render_mem)
    # Render NVMe stats every minute
    schedule.every(1).minutes.do(display_renderer.render_nvme_stats)
    # Render uptime every minute
    schedule.every(1).minutes.do(display_renderer.render_uptime)
    # Render IP address every hour
    schedule.every(1).hours.do(display_renderer.render_ip_address)
    # Get updates every 3 hours
    schedule.every(3).hours.do(display_renderer.get_updates)
    # Update display
    schedule.every(2).seconds.do(display_renderer.update_display_and_save_image)

    display_renderer.render_grid()
    schedule.run_all()

    while True:
        """Run the scheduled tasks."""
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    sys.exit(main())
