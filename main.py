#!/usr/bin/env python
"""
Daily Reminder Alarm

- Reads alarms from a CSV file.
- Schedules them using schedule library.
- Plays an audio file when triggered.
"""

import csv
import datetime as dt
import time
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import schedule  # pip install schedule
from playsound3 import playsound  # pip install playsound3

# ----------------------------------------------------------------------
# Configuration (feel free to change these)
# ----------------------------------------------------------------------
ALARM_FILE = Path("alarms.csv")          # CSV file with time, message
AUDIO_FILE = Path("alarm_sound.wav")     # Audio file to play on alarm
LOG_LEVEL = logging.INFO                 # DEBUG for more details

# Optional: if you need a specific timezone:
# TIMEZONE = "America/New_York"
TIMEZONE = "America/New_York"  # set to string above or keep None for local system time


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def parse_time(time_str: str) -> dt.time:
    """Parse HH:MM (24‑h) into a datetime.time object."""
    try:
        return dt.datetime.strptime(time_str.strip(), "%H:%M").time()
    except ValueError as exc:
        raise ValueError(f"Invalid time format '{time_str}'. Expected HH:MM") from exc


def read_alarms(csv_path: Path) -> List[Tuple[dt.time, str, Optional[Path]]]:
    """
    Read CSV and return list of (time_obj, message, audio_path).
    Skips lines that cannot be parsed or are missing required fields.
    """
    alarms = []
    if not csv_path.exists():
        logging.error(f"Alarm file {csv_path} does not exist.")
        sys.exit(1)

    with csv_path.open(newline="") as f:
        # Assuming the CSV now has at least time, message, and audio_file headers
        reader = csv.DictReader(f)
        for row in reader:
            try:
                t = parse_time(row["time"])
                msg = row.get("message", "").strip()
                # The third column is for the custom audio file path/name
                audio_file_str = row.get("alarm_sound_file", "").strip()
                custom_audio_path = Path(audio_file_str) if audio_file_str else None

                alarms.append((t, msg, custom_audio_path))
            except Exception as exc:
                logging.warning(f"Skipping bad line {row}: {exc}")

    return alarms


def play_alarm(message: str, custom_audio_path: Optional[Path] = None):
    """Play the alarm sound and log the message."""
    # Use custom path if provided, otherwise fall back to global audio file
    audio_to_play = custom_audio_path if custom_audio_path else AUDIO_FILE

    if not audio_to_play.exists():
        logging.error(f"Audio file {audio_to_play} not found.")
        return

    try:
        logging.info(f"[{dt.datetime.now():%Y-%m-%d %H:%M}] Alarm! {message}")
        playsound(str(audio_to_play))
    except Exception as exc:
        logging.error(f"Failed to play sound: {exc}")


def schedule_alarms(alarms: List[Tuple[dt.time, str, Optional[Path]]], timezone: Optional[str] = None):
    """Schedule each alarm for daily execution."""
    for t_obj, msg, audio_path in alarms:
        # `schedule.every().day.at("HH:MM")` schedules a job at that time.
        if timezone:
            schedule.every().day.at(t_obj.strftime("%H:%M"), timezone).do(play_alarm, message=msg, custom_audio_path=audio_path)
        else:
            schedule.every().day.at(t_obj.strftime("%H:%M")).do(play_alarm, message=msg, custom_audio_path=None)
        logging.debug(f"Scheduled {t_obj} -> '{msg}' (Audio: {audio_path})")


def run_scheduler():
    """Run the scheduler loop forever."""
    while True:
        schedule.run_pending()
        # Sleep a short time to avoid busy‑waiting.
        time.sleep(1)


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------


def main() -> None:
    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Optional timezone handling is configured per job via .at(..., timezone)
    if TIMEZONE:
        logging.info(f"Using timezone: {TIMEZONE}")

    alarms = read_alarms(ALARM_FILE)
    if not alarms:
        logging.error("No valid alarms found. Exiting.")
        sys.exit(1)

    schedule_alarms(alarms, TIMEZONE)
    #logging.info("All alarms scheduled. Running scheduler…")
    #run_scheduler()
    #now = dt.datetime.now()
    #trigger_time = (now + dt.timedelta(minutes=1)).strftime("%H:%M")
    #schedule.every().day.at(trigger_time).do(play_alarm, message="One‑minute test")
    logging.info("All alarms scheduled. Running scheduler…")
    run_scheduler()
    
if __name__ == "__main__":
    main()
