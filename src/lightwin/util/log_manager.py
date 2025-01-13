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
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Literal


def _get_package_version(package_name: str) -> str:
    """Get the package version."""
    try:
        return version(package_name)
    except PackageNotFoundError:
        return "Unknown version"


def _get_last_commit_hash() -> str:
    """Get the last Git commit hash."""
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"])
            .decode("utf-8")
            .strip()
        )
    except subprocess.CalledProcessError:
        return "Unknown commit"


def _log_header(package_name: str) -> str:
    """Create a header for the log file."""
    package_version = _get_package_version(package_name)
    commit_hash = _get_last_commit_hash()
    header_message = (
        f"Starting log for {package_name} - Version: {package_version}, "
        f"Commit: {commit_hash}"
    )
    return header_message


def _console_handler(
    output: str, level: str, color: bool, line_template: str
) -> logging.Handler:
    """Set up the console handler."""
    output_stream = sys.stdout if output.lower() == "stdout" else sys.stderr
    console_handler = logging.StreamHandler(output_stream)
    console_handler.setLevel(level.upper())
    console_formatter = LogFormatter(fmt=line_template, color=color)
    console_handler.setFormatter(console_formatter)
    return console_handler


def _file_handler(
    file: Path, level: str, color: bool, line_template: str
) -> logging.Handler | Literal[False]:
    """Set up the file handler."""
    try:
        logfile_handler = logging.FileHandler(file, mode="a")
    except Exception as e:
        print(f"Failed to set up log file: {e}")
        return False

    logfile_handler.setLevel(level.upper())
    logfile_formatter = LogFormatter(fmt=line_template, color=color)
    logfile_handler.setFormatter(logfile_formatter)
    return logfile_handler


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
    package_name: str,
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

    logger.addHandler(
        _console_handler(
            console_log_output,
            console_log_level,
            console_log_color,
            console_log_line_template,
        )
    )

    logfile_handler = _file_handler(
        logfile_file,
        logfile_log_level,
        logfile_log_color,
        logfile_line_template,
    )
    if not logfile_handler:
        return False
    logger.addHandler(logfile_handler)
    logger.info(_log_header(package_name))

    return True


def main():
    """Main function."""
    if not set_up_logging(
        package_name="LightWin",
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
