# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview
The project is a Python utility designed to run as a long-running background process. Its core function is to read scheduled alarm definitions from `alarms.csv`, manage these alarms using the `schedule` library, and trigger an audio notification (`alarm_sound.wav`) at specified times. The application runs continuously in a loop checking for pending jobs every second.

## Setup
1. **Virtual Environment**: Create or activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
   ```
2. **Install Dependencies**: Install required packages using the provided `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

## Execution and Development Commands
*   **Run Application**: Start the scheduler loop:
    ```bash
    python main.py
    ```
*   **Test Single Alarm Logic**: To test the alarm playing function manually, you can temporarily modify `main.py` to run a single-shot test (e.g., uncommenting lines 126-129 in `main()`).
*   **Linting/Testing**: Since this is a utility script, there are no explicit linting or testing commands provided in the project structure. Writing unit tests for core components like `parse_time` and `read_alarms` would be beneficial.

## Code Architecture & Data Flow
The application follows a clear separation of concerns:

1.  **Data Source (`alarms.csv`)**: This CSV file is the single source of truth for alarm definitions. It must contain a header with at least two columns: `time` (HH:MM 24-hour format) and `message` (the text displayed when the alarm fires).
    *   **Format:** `time,message`

2.  **Reading Logic (`read_alarms` in main.py)**: This function is responsible for reading and validating the CSV file. It uses `parse_time` to convert string times into Python `datetime.time` objects, skipping any malformed rows with a warning.

3.  **Scheduling Core (`schedule_alarms` in main.py)**:
    *   It iterates through the list of valid alarms.
    *   It uses the external `schedule` library to register a daily job for each alarm time.
    *   The function supports optional timezone configuration via the `TIMEZONE` constant (line 30 of `main.py`).

4.  **Execution Loop (`run_scheduler` in main.py)**:
    *   This infinite loop calls `schedule.run_pending()` every second, checking if any scheduled alarms are due to fire.
    *   When an alarm triggers, it calls `play_alarm()`, which handles logging the event and playing the sound file (`alarm_sound.wav`).

## Key Components
*   **`main.py`**: Contains all core logic, including setup, reading, scheduling, and the infinite execution loop.
*   **`alarms.csv`**: Configuration data for alarm times and messages.
*   **`playsound3`**: The external library used for cross-platform audio playback of `alarm_sound.wav`.