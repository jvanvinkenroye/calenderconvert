import csv
from datetime import datetime
import re
import sys

# Constants for date and time formats and iCalendar templates
DATE_FORMAT = "%d.%m.%y"
TIME_FORMAT = "%H:%M"
ICAL_FORMAT = "%Y%m%dT%H%M%S"
ICAL_TEMPLATE = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Mein Kalender//mxm.dk//\n{events}END:VCALENDAR"
EVENT_TEMPLATE = (
    "BEGIN:VEVENT\n"
    "DTSTART;TZID=Europe/Berlin:{start}\n"
    "DTEND;TZID=Europe/Berlin:{end}\n"
    "SUMMARY:{summary}\n"
    "DESCRIPTION:{description}\n"
    "END:VEVENT\n"
)

# Function to validate date string
def is_valid_date(date_str):
    """
    Check if the given date string is in the format "%d.%m.%y"

    Parameters:
    date_str (str): The date string to check

    Returns:
    bool: True if the date string is valid, False otherwise
    """
    try:
        datetime.strptime(date_str, DATE_FORMAT)
        return True
    except ValueError:
        return False

# Function to validate time string
def is_valid_time(time_str):
    """
    Check if the given time string is in the format "HH:MM - HH:MM"

    Parameters:
    time_str (str): The time string to check

    Returns:
    bool: True if the time string is valid, False otherwise
    """
    if re.match(r'\d{2}:\d{2} - \d{2}:\d{2}', time_str):
        return True
    return False

# Function to convert date and time strings to iCalendar format
def convert_to_ical_format(date_str, time_str):
    """
    Convert the given date and time strings to the iCalendar format

    Parameters:
    date_str (str): The date string to convert
    time_str (str): The time string to convert

    Returns:
    tuple: The start and end datetime strings in the iCalendar format
    """
    date_obj = datetime.strptime(date_str, DATE_FORMAT)
    time_start_str, time_end_str = time_str.split(" - ")
    time_start_obj = datetime.strptime(time_start_str, TIME_FORMAT)
    time_end_obj = datetime.strptime(time_end_str, TIME_FORMAT)
    start_datetime = datetime.combine(date_obj, time_start_obj.time())
    end_datetime = datetime.combine(date_obj, time_end_obj.time())
    return start_datetime.strftime(ICAL_FORMAT), end_datetime.strftime(ICAL_FORMAT)

# Function to create an iCalendar event
def create_event(termin):
    """
    Create an iCalendar event from the given termin

    Parameters:
    termin (dict): The termin to convert to an iCalendar event

    Returns:
    str: The iCalendar event as a string
    """
    start_str, end_str = convert_to_ical_format(termin['datum'], termin['zeit'])
    return EVENT_TEMPLATE.format(start=start_str, end=end_str, summary=termin['beschreibung'], description=termin['typ'])

# Check if a CSV file was provided as an argument
if len(sys.argv) < 2:
    print("Bitte geben Sie eine CSV-Datei als Argument ein.")
    sys.exit(1)

csv_filepath = sys.argv[1]

# Read appointments from the CSV file
termine = []
with open(csv_filepath, mode='r', encoding='utf-8-sig') as file:
    reader = csv.DictReader(file, delimiter=';')
    for row in reader:
        if is_valid_date(row['datum']) and is_valid_time(row['zeit']):
            termine.append(row)
        else:
            print(f"Ungültiges Format gefunden: {row}")

# Create iCalendar events for each appointment
events = [create_event(termin) for termin in termine]
ical_content = ICAL_TEMPLATE.format(events="".join(events))

# Save the iCalendar content to a file with the same name as the CSV file, but with a '.ics' extension
with open(csv_filepath.replace('.csv', '.ics'), mode='w', encoding='utf-8-sig') as file:
    file.write(ical_content)