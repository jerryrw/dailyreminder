<|channel|>analysis<|message|>Need outline, steps, code.<|end|><|start|>assistant<|channel|>final<|message|>Below is a **complete, “starter‑kit”** for a small Python project that:

* reads a list of dates/times (and optional messages) from a text/CSV file,
* schedules daily reminder alarms at those times,
* plays a local audio file when the alarm fires,
* logs what happened and can be run as a service or a simple script.

You can copy‑paste everything into a new directory, tweak the configuration to fit your environment, and you’ll have a working reminder system in under 30 minutes.

---

## 1. Project layout

```
daily_reminder/
├── alarms.csv          # input file – one alarm per line
├── alarm_sound.mp3     # local audio file that will be played
├── requirements.txt    # Python dependencies
└── main.py             # the application code
```

### `alarms.csv` example

```csv
time,message
08:30,Morning coffee
12:00,Lunch break
18:45,Evening workout
```

The file format is flexible – see *Parsing* section for alternatives.

---

## 2. Dependencies

Create a virtual environment (recommended) and install the required packages:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .\.venv\Scripts\activate
#pip install --upgrade pip
python -m pip install --upgrade pip
pip install -r requirements.txt
```

`requirements.txt`

```txt
schedule==1.2.2
playsound==1.3.0  # cross‑platform audio playback
pytz==2024.1       # timezone handling (optional)
```

> **Why `schedule`?**  
> It’s a tiny, pure‑Python job scheduler that works well for “once‑daily” tasks and is easier to understand than the built‑in `sched` module.

---

## 3. The code – `main.py`

```python
#!/usr/bin/env python
"""
Daily Reminder Alarm

- Reads alarms from a CSV file.
- Schedules them using schedule library.
- Plays an audio file when triggered.
"""

import csv
import datetime as dt
import logging
import os
import sys
from pathlib import Path
from typing import List, Tuple

import schedule  # pip install schedule
from playsound3 import playsound  # pip install playsound

# ----------------------------------------------------------------------
# Configuration (feel free to change these)
# ----------------------------------------------------------------------
ALARM_FILE = Path("alarms.csv")          # CSV file with time, message
AUDIO_FILE = Path("alarm_sound.mp3")     # Audio file to play on alarm
LOG_LEVEL = logging.INFO                 # DEBUG for more details

# Optional: if you need a specific timezone:
# TIMEZONE = "America/New_York"
TIMEZONE = None  # set to string above or keep None for local system time


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def parse_time(time_str: str) -> dt.time:
    """Parse HH:MM (24‑h) into a datetime.time object."""
    try:
        return dt.datetime.strptime(time_str.strip(), "%H:%M").time()
    except ValueError as exc:
        raise ValueError(f"Invalid time format '{time_str}'. Expected HH:MM") from exc


def read_alarms(csv_path: Path) -> List[Tuple[dt.time, str]]:
    """
    Read CSV and return list of (time_obj, message).
    Skips lines that cannot be parsed.
    """
    alarms = []
    if not csv_path.exists():
        logging.error(f"Alarm file {csv_path} does not exist.")
        sys.exit(1)

    with csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                t = parse_time(row["time"])
                msg = row.get("message", "").strip()
                alarms.append((t, msg))
            except Exception as exc:
                logging.warning(f"Skipping bad line {row}: {exc}")

    return alarms


def play_alarm(message: str):
    """Play the alarm sound and log the message."""
    if not AUDIO_FILE.exists():
        logging.error(f"Audio file {AUDIO_FILE} not found.")
        return

    try:
        logging.info(f"[{dt.datetime.now():%Y-%m-%d %H:%M}] Alarm! {message}")
        playsound(str(AUDIO_FILE))
    except Exception as exc:
        logging.error(f"Failed to play sound: {exc}")


def schedule_alarms(alarms: List[Tuple[dt.time, str]]):
    """Schedule each alarm for daily execution."""
    for t_obj, msg in alarms:
        # `schedule.every().day.at("HH:MM")` schedules a job at that time.
        schedule.every().day.at(t_obj.strftime("%H:%M")).do(play_alarm, message=msg)
        logging.debug(f"Scheduled {t_obj} -> '{msg}'")


def run_scheduler():
    """Run the scheduler loop forever."""
    while True:
        schedule.run_pending()
        # Sleep a short time to avoid busy‑waiting.
        dt.sleep(1)


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------


def main() -> None:
    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Optional timezone handling (requires pytz)
    if TIMEZONE:
        try:
            import pytz
            tz = pytz.timezone(TIMEZONE)
            schedule.tzinfo = tz
            logging.info(f"Using timezone: {TIMEZONE}")
        except Exception as exc:
            logging.warning(f"Could not set timezone '{TIMEZONE}': {exc}")

    alarms = read_alarms(ALARM_FILE)
    if not alarms:
        logging.error("No valid alarms found. Exiting.")
        sys.exit(1)

    schedule_alarms(alarms)
    logging.info("All alarms scheduled. Running scheduler…")
    run_scheduler()


if __name__ == "__main__":
    main()
```

### What the script does

| Step | What happens |
|------|--------------|
| 1 | Reads `alarms.csv`, parses each line into a `(time, message)` tuple. |
| 2 | Uses `schedule.every().day.at("HH:MM")` to schedule a job that calls `play_alarm(message)`. |
| 3 | The main loop keeps the process alive and checks for pending jobs every second. |
| 4 | When an alarm triggers, it logs the event and plays `alarm_sound.mp3`. |

---

## 4. Running the project

```bash
# From the daily_reminder directory
python main.py
```

You should see log output like:

```
2026-04-27 08:30:00 [INFO] Alarm! Morning coffee
```

…and hear the audio.

### Run as a background service (Linux)

Create a systemd unit file `/etc/systemd/system/daily_reminder.service`:

```ini
[Unit]
Description=Daily Reminder Service
After=network.target

[Service]
User=your_user
WorkingDirectory=/home/your_user/daily_reminder
ExecStart=/home/your_user/.venv/bin/python /home/your_user/daily_reminder/main.py
Restart=on-failure
StandardOutput=append:/var/log/daily_reminder.log
StandardError=inherit

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable daily_reminder.service
sudo systemctl start daily_reminder.service
```

---

## 5. Extending the project

| Feature | How to add |
|---------|------------|
| **Different audio per alarm** | Add a third column (`audio`) in CSV and modify `play_alarm` to accept a filename. |
| **Notification pop‑up** | Use `plyer.notification.notify()` or platform‑specific APIs. |
| **Web UI / API** | Wrap the scheduler logic inside a Flask/FastAPI app; expose endpoints to add/remove alarms. |
| **Persist state across restarts** | Store scheduled jobs in a SQLite DB and load them on startup. |
| **Recurring patterns (e.g., weekdays only)** | Extend CSV with a `days` column, parse into a set of weekday numbers, and schedule accordingly. |

---

## 6. Common pitfalls & tips

| Issue | Fix / Tip |
|-------|-----------|
| Audio file not playing on macOS | Install `ffmpeg` or use a `.wav` file; `playsound` relies on system players. |
| Time zone drift after daylight‑saving change | Use `pytz`/`zoneinfo` to set `schedule.tzinfo`. |
| Script stops after first run | Ensure the main loop (`run_scheduler`) never exits. |
| Permissions when running as a service | Make sure the audio device is accessible; may need `sudo` or group membership. |

---

## 7. Quick sanity check

Create a test alarm that fires in 1 minute:

```csv
time,message
```

Add:

```
time,message
00:00,Test message
```

Then edit `main.py`, replace the scheduling line with:

```python
now = dt.datetime.now()
trigger_time = (now + dt.timedelta(minutes=1)).strftime("%H:%M")
schedule.every().day.at(trigger_time).do(play_alarm, message="One‑minute test")
```

Run the script and watch the alarm trigger. Once confirmed, revert to the CSV‑based scheduler.

---

### 🎉 You’re done!

You now have a fully functional, cross‑platform Python reminder system that can be expanded in many ways. Happy coding!