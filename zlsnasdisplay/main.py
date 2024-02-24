#! /usr/bin/env python3

import logging
import signal
import sys
import time

import schedule
import sentry_sdk

from zlsnasdisplay.display_renderer import DisplayRenderer

# Configure logging level
logging.basicConfig(level=logging.DEBUG)

# Initialize Sentry for error tracking
sentry_sdk.init("https://c23614af051048d6866787f8338d15c0@glitchtip.zales.dev/1")

display_renderer = DisplayRenderer()


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

    # Render CPU load every 30 seconds
    schedule.every(30).seconds.do(display_renderer.render_cpu_load)
    # Get updates every 3 hours
    schedule.every(3).hours.do(display_renderer.get_updates)
    # Render signal strength every minute
    schedule.every(1).minutes.do(display_renderer.render_signal_strength)
    # Render memory usage every minute
    schedule.every(1).minutes.do(display_renderer.render_mem)
    # Render NVMe stats every minute
    schedule.every(1).minutes.do(display_renderer.render_nvme_stats)
    # Render fan speed every 10 seconds
    schedule.every(10).seconds.do(display_renderer.render_fan_speed)
    # Render IP address every hour
    schedule.every(1).hours.do(display_renderer.render_ip_address)
    # Render uptime every minute
    schedule.every(1).minutes.do(display_renderer.render_uptime)
    # Render current traffic every 10 seconds
    schedule.every(10).seconds.do(display_renderer.render_current_traffic)

    schedule.run_all()

    while True:
        """ Run the scheduled tasks."""
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
