"""Utilities for setting up loguru logging with integration to SIPE logserver"""

import sys
import os
import queue
import atexit
from typing import Optional
from pathlib import Path

import logging
import logging.handlers

import loguru
from loguru import logger


class LogServerHandler(logging.handlers.SocketHandler):
    """This handler attaches metadata to log messages such that logs can be ingested and parsed correctly by the onsite log server.
    These extra fields (rig id, comp id, project name, version) help users and system engineers filter and diagnose problems
    """

    def __init__(
        self,
        project_name,
        version,
        rig_id=os.getenv("aibs_rig_id", "unknown"),
        comp_id=os.getenv("aibs_comp_id", "unknown"),
        *args,
        **kwargs,
    ):
        """Set instance variables and formatter"""
        super().__init__(*args, **kwargs)
        self.project_name = project_name
        self.rig_id = rig_id
        self.comp_id = comp_id
        self.version = version
        self.formatter = logging.Formatter(
            datefmt="%Y-%m-%d %H:%M:%S",
            fmt="%(asctime)s\n%(name)s\n%(levelname)s\n%(funcName)s (%(filename)s:%(lineno)d)\n%(message)s",
        )

    def emit(self, record: logging.LogRecord) -> None:
        """Add instance variables to the log record before sending to log server"""
        # Add extra attributes to the record
        record.project = self.project_name
        record.rig_id = self.rig_id
        record.comp_id = self.comp_id
        record.version = self.version
        # Encode and decode message to skip characters not supported by the log database
        record.msg = record.msg.encode("ascii", errors="replace").decode("ascii")
        record.extra = None  # set extra to None because this sends a pickled record
        super().emit(record)


logging_levels = [
    {"name": "START_STOP", "no": logging.WARNING + 5, "color": "<blue>"},
    # {"name": "ADMIN", "no": logging.WARNING + 6, "color": "<purple>"},
    {"name": "LIMS", "no": logging.WARNING + 7, "color": "<yellow>"},
    {"name": "MTRAIN", "no": logging.WARNING + 8, "color": "<cyan>"},
    {"name": "SLIMS", "no": logging.WARNING + 9, "color": "<magenta>"},
]

logger.configure(
    levels=logging_levels,
)

pre_setup_log_q = queue.Queue()
logger.add(lambda msg: pre_setup_log_q.put(msg.record), serialize=True)  # ensure thread/process safety


def setup_logger(
    project_name: str,
    project_version: str,
    log_file: Optional[Path] = None,
    logserver_url: str | None = None,
    extras: dict | None = None,
):
    """Add handlers to the logger for console, file, and log server."""

    logger.remove()

    if extras:
        logger.configure(extra=extras)

    # Add console handler
    logger.add(
        sys.stderr,
        format=loguru._defaults.LOGURU_FORMAT + " | {extra}",  # include extra context in format
        colorize=True,
    )

    # Add log file
    if log_file:
        logger.add(log_file, format="{time} | {level} | {message} | {extra}")

    # Add log server handler
    if logserver_url is not None:
        logger.add(
            LogServerHandler(
                host=logserver_url.split(":")[0],
                port=int(logserver_url.split(":")[1]),
                project_name=project_name,
                version=project_version,
            ),
            format="{message} | {extra}",
            level="INFO",
        )

    # Send start log, register stop log
    logger.log("START_STOP", "Action, Start")

    while not pre_setup_log_q.empty():
        record = pre_setup_log_q.get()
        logger.log(
            record["level"].name,
            record["message"],
            note="log re-emitted after setup",
            original_record={k: v for k, v in record.items() if k not in ["message"]},
            **record.get("extra", {}),
        )

    atexit.register(lambda: logger.log("START_STOP", "Action, Stop"))
