#!/usr/bin/env python3
"""Python dual-logging setup (console and log file).

It supports different log levels and colorized output.

Created by Fonic <https://github.com/fonic>
Date: 04/05/20 - 02/07/23

Based on:
https://stackoverflow.com/a/13733863/1976617
https://uran198.github.io/en/python/2016/07/12/colorful-python-logging.html
https://en.wikipedia.org/wiki/ANSI_escape_code#Colors

"""
import logging
import sys
from pathlib import Path


class LogFormatter(logging.Formatter):
    """Logging formatter supporting colorized output."""

    COLOR_CODES = {
        # bright/bold magenta
        logging.CRITICAL: "\033[1;35m",
        # bright/bold red
        logging.ERROR: "\033[1;31m",
        # bright/bold yellow
        logging.WARNING: "\033[1;33m",
        # white / light gray
        logging.INFO: "\033[0;37m",
        # bright/bold black / dark gray
        logging.DEBUG: "\033[1;30m",
    }

    RESET_CODE = "\033[0m"

    def __init__(self, color: bool, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.color = color

    def format(self, record: logging.LogRecord, *args, **kwargs) -> str:
        if self.color and record.levelno in self.COLOR_CODES:
            record.color_on = self.COLOR_CODES[record.levelno]
            record.color_off = self.RESET_CODE
        else:
            record.color_on = ""
            record.color_off = ""
        return super().format(record, *args, **kwargs)


def set_up_logging(
    console_log_output: str = "stdout",
    console_log_level: str = "INFO",
    console_log_color: bool = True,
    console_log_line_template: str = "%(color_on)s[%(levelname)-8s] [%(filename)-20s]%(color_off)s %(message)s",
    logfile_file: Path = Path("lightwin.log"),
    logfile_log_level: str = "INFO",
    logfile_log_color: bool = False,
    logfile_line_template: str = "%(color_on)s[%(asctime)s] [%(levelname)-8s] [%(filename)-20s]%(color_off)s %(message)s",
) -> bool:
    """Set up logging with both console and file handlers."""
    # Remove previous logger
    for handler in logging.root.handlers[:]:
        handler.close()
        logging.root.removeHandler(handler)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Set up console handler
    output_stream = (
        sys.stdout if console_log_output.lower() == "stdout" else sys.stderr
    )
    console_handler = logging.StreamHandler(output_stream)
    console_handler.setLevel(console_log_level.upper())
    console_formatter = LogFormatter(
        fmt=console_log_line_template, color=console_log_color
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Set up file handler
    try:
        logfile_handler = logging.FileHandler(logfile_file, mode="a")
    except Exception as e:
        print(f"Failed to set up log file: {e}")
        return False

    logfile_handler.setLevel(logfile_log_level.upper())
    logfile_formatter = LogFormatter(
        fmt=logfile_line_template, color=logfile_log_color
    )
    logfile_handler.setFormatter(logfile_formatter)
    logger.addHandler(logfile_handler)

    return True


def main():
    """Main function."""
    if not set_up_logging(
        console_log_output="stdout",
        console_log_level="warning",
        console_log_color=True,
        logfile_file=Path("lightwin.log"),
        logfile_log_level="INFO",
        logfile_log_color=False,
    ):
        print("Failed to set up logging, aborting.")
        return 1

    # Sample log messages
    logging.debug("Debug message")
    logging.info("Info message")
    logging.warning("Warning message")
    logging.error("Error message")
    logging.critical("Critical message")
    return 0


if __name__ == "__main__":
    sys.exit(main())
