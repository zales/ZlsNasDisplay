#! /usr/bin/env python3

import logging
import os
import signal
import sys
import time

import schedule

from zlsnasdisplay.display_renderer import DisplayRenderer

# GET ENVIRONMENT VARIABLES
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
SENTRY_DSN = os.getenv("SENTRY_DSN", False)
DISPLAY_IMAGE_PATH = os.getenv("DISPLAY_IMAGE_PATH", False)

# Configure logging level
logging.basicConfig(level=LOG_LEVEL)

if SENTRY_DSN:
    import sentry_sdk

    # Initialize Sentry for error tracking
    sentry_sdk.init(SENTRY_DSN)

# Detect sudo
IS_ROOT = os.getuid() == 0

if not IS_ROOT:
    logging.warning("The script does not run as root. Cannot perform apt update!")

display_renderer = DisplayRenderer(DISPLAY_IMAGE_PATH, IS_ROOT)


# Define signal_handler function to catch SIGINT (Ctrl+C)
def signal_handler(sig, frame):
    """Signal handler function to catch SIGINT (Ctrl+C) and exit the program."""
    logging.info("Exiting the program...")
    # Clear all scheduled jobs
    schedule.clear()
    time.sleep(1)
    # Wait for running jobs to complete
    while schedule.jobs:
        time.sleep(1)

    display_renderer.go_to_sleep()

    sys.exit(0)


def main():
    """Main function to run the program."""

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGHUP, signal_handler)

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

    schedule.run_all()

    while True:
        """ Run the scheduled tasks."""
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
