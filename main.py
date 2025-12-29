#!/usr/bin/env python3
"""
CalendarConvert - CSV to iCalendar Converter

Converts CSV calendar/appointment data to iCalendar (.ics) format.
"""

import argparse
import csv
import hashlib
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Constants for date and time formats and iCalendar templates
DATE_FORMAT = "%d.%m.%y"
TIME_FORMAT = "%H:%M"
ICAL_FORMAT = "%Y%m%dT%H%M%S"
DEFAULT_TIMEZONE = "Europe/Berlin"

ICAL_TEMPLATE = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//CalendarConvert//github.com//
{events}END:VCALENDAR"""

EVENT_TEMPLATE = """BEGIN:VEVENT
UID:{uid}
DTSTART;TZID={timezone}:{start}
DTEND;TZID={timezone}:{end}
SUMMARY:{summary}
DESCRIPTION:{description}
END:VEVENT
"""

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def is_valid_date(date_str: str) -> bool:
    """
    Check if the given date string is in the format "%d.%m.%y".

    Args:
        date_str: The date string to check.

    Returns:
        True if the date string is valid, False otherwise.
    """
    try:
        datetime.strptime(date_str, DATE_FORMAT)
        return True
    except ValueError:
        return False


def is_valid_time(time_str: str) -> bool:
    """
    Check if the given time string is in the format "HH:MM - HH:MM".

    Args:
        time_str: The time string to check.

    Returns:
        True if the time string is valid, False otherwise.
    """
    if not time_str or " - " not in time_str:
        return False

    parts = time_str.split(" - ")
    if len(parts) != 2:
        return False

    try:
        datetime.strptime(parts[0].strip(), TIME_FORMAT)
        datetime.strptime(parts[1].strip(), TIME_FORMAT)
        return True
    except ValueError:
        return False


def convert_to_ical_format(date_str: str, time_str: str) -> tuple[str, str]:
    """
    Convert the given date and time strings to the iCalendar format.

    Args:
        date_str: The date string to convert (format: DD.MM.YY).
        time_str: The time string to convert (format: HH:MM - HH:MM).

    Returns:
        A tuple of (start_datetime, end_datetime) in iCalendar format.

    Raises:
        ValueError: If the date or time format is invalid.
    """
    date_obj = datetime.strptime(date_str, DATE_FORMAT)
    time_start_str, time_end_str = time_str.split(" - ")
    time_start_obj = datetime.strptime(time_start_str.strip(), TIME_FORMAT)
    time_end_obj = datetime.strptime(time_end_str.strip(), TIME_FORMAT)
    start_datetime = datetime.combine(date_obj, time_start_obj.time())
    end_datetime = datetime.combine(date_obj, time_end_obj.time())
    return start_datetime.strftime(ICAL_FORMAT), end_datetime.strftime(ICAL_FORMAT)


def generate_uid(termin: dict[str, str]) -> str:
    """
    Generate a unique identifier for a calendar event.

    Args:
        termin: The appointment dictionary.

    Returns:
        A unique identifier string.
    """
    content = f"{termin.get('datum', '')}{termin.get('zeit', '')}{termin.get('beschreibung', '')}"
    hash_value = hashlib.md5(content.encode()).hexdigest()[:16]
    return f"{hash_value}@calendarconvert"


def sanitize_text(text: str) -> str:
    """
    Sanitize text for iCalendar format by escaping special characters.

    Args:
        text: The text to sanitize.

    Returns:
        The sanitized text.
    """
    if not text:
        return ""
    # Escape backslashes, semicolons, commas, and newlines per RFC 5545
    text = text.replace("\\", "\\\\")
    text = text.replace(";", "\\;")
    text = text.replace(",", "\\,")
    text = text.replace("\n", "\\n")
    return text


def create_event(termin: dict[str, str], timezone: str = DEFAULT_TIMEZONE) -> str:
    """
    Create an iCalendar event from the given appointment.

    Args:
        termin: The appointment dictionary with keys: datum, zeit, beschreibung, typ.
        timezone: The timezone for the event.

    Returns:
        The iCalendar event as a string.
    """
    start_str, end_str = convert_to_ical_format(termin['datum'], termin['zeit'])
    uid = generate_uid(termin)
    summary = sanitize_text(termin.get('beschreibung', ''))
    description = sanitize_text(termin.get('typ', ''))

    return EVENT_TEMPLATE.format(
        uid=uid,
        timezone=timezone,
        start=start_str,
        end=end_str,
        summary=summary,
        description=description
    )


def read_csv(filepath: Path) -> list[dict[str, str]]:
    """
    Read appointments from a CSV file.

    Args:
        filepath: Path to the CSV file.

    Returns:
        List of valid appointment dictionaries.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        PermissionError: If the file can't be read.
        csv.Error: If the CSV format is invalid.
    """
    termine = []

    with open(filepath, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file, delimiter=';')

        # Validate required columns
        required_columns = {'datum', 'zeit', 'beschreibung'}
        if reader.fieldnames is None:
            raise csv.Error("CSV file is empty or has no header")

        missing_columns = required_columns - set(reader.fieldnames)
        if missing_columns:
            raise csv.Error(f"Missing required columns: {', '.join(missing_columns)}")

        for row_num, row in enumerate(reader, start=2):
            if is_valid_date(row['datum']) and is_valid_time(row['zeit']):
                termine.append(row)
            else:
                logger.warning(f"Row {row_num}: Invalid format - {row}")

    return termine


def write_ics(filepath: Path, content: str) -> None:
    """
    Write iCalendar content to a file.

    Args:
        filepath: Path to the output file.
        content: The iCalendar content to write.

    Raises:
        PermissionError: If the file can't be written.
        OSError: If there's an I/O error.
    """
    with open(filepath, mode='w', encoding='utf-8') as file:
        file.write(content)


def convert_csv_to_ics(
    input_path: Path,
    output_path: Optional[Path] = None,
    timezone: str = DEFAULT_TIMEZONE
) -> Path:
    """
    Convert a CSV file to iCalendar format.

    Args:
        input_path: Path to the input CSV file.
        output_path: Path to the output ICS file. If None, uses input filename with .ics extension.
        timezone: Timezone for the events.

    Returns:
        Path to the created ICS file.

    Raises:
        FileNotFoundError: If the input file doesn't exist.
        ValueError: If no valid appointments are found.
    """
    if output_path is None:
        output_path = input_path.with_suffix('.ics')

    termine = read_csv(input_path)

    if not termine:
        raise ValueError("No valid appointments found in the CSV file")

    logger.info(f"Found {len(termine)} valid appointments")

    events = [create_event(termin, timezone) for termin in termine]
    ical_content = ICAL_TEMPLATE.format(events="".join(events))

    write_ics(output_path, ical_content)
    logger.info(f"Created: {output_path}")

    return output_path


def parse_args(args: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert CSV calendar data to iCalendar (.ics) format.",
        epilog="Example: python main.py termine.csv -o calendar.ics"
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Input CSV file path"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Output ICS file path (default: same as input with .ics extension)"
    )
    parser.add_argument(
        "-t", "--timezone",
        default=DEFAULT_TIMEZONE,
        help=f"Timezone for events (default: {DEFAULT_TIMEZONE})"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    return parser.parse_args(args)


def main() -> int:
    """Main entry point."""
    args = parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    try:
        if not args.input.exists():
            logger.error(f"File not found: {args.input}")
            return 1

        convert_csv_to_ics(args.input, args.output, args.timezone)
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except PermissionError as e:
        logger.error(f"Permission denied: {e}")
        return 1
    except csv.Error as e:
        logger.error(f"CSV error: {e}")
        return 1
    except ValueError as e:
        logger.error(str(e))
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
