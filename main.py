import csv
from datetime import datetime
import re
import sys


# Funktion zum Überprüfen des Datums- und Zeitformats

def is_valid_date(date_str):
    try:
        datetime.strptime(date_str, "%d.%m.%y")
        return True
    except ValueError:
        return False


def is_valid_time(time_str):
    if re.match(r'\d{2}:\d{2} - \d{2}:\d{2}', time_str):
        return True
    return False


# Funktion zum Konvertieren von Datum und Zeit in das iCalendar-Format
def convert_to_ical_format(date_str, time_str):
    date_obj = datetime.strptime(date_str, "%d.%m.%y")
    time_start_str, time_end_str = time_str.split(" - ")
    time_start_obj = datetime.strptime(time_start_str, "%H:%M")
    time_end_obj = datetime.strptime(time_end_str, "%H:%M")
    start_datetime = datetime.combine(date_obj, time_start_obj.time())
    end_datetime = datetime.combine(date_obj, time_end_obj.time())
    return start_datetime.strftime("%Y%m%dT%H%M%S"), end_datetime.strftime("%Y%m%dT%H%M%S")


# lesen das erste agument als csv datei und gebe einen fehler aus, wenn das argument fehlt
if len(sys.argv) < 2:
    print("Bitte geben Sie eine CSV-Datei als Argument ein.")
    sys.exit(1)

csv_filepath = sys.argv[1]

# Termine aus der CSV-Datei lesen
termine = []
with open(csv_filepath, mode='r', encoding='utf-8-sig') as file:
    reader = csv.DictReader(file, delimiter=';')
    # print(reader.fieldnames)
    for row in reader:
        if is_valid_date(row['datum']) and is_valid_time(row['zeit']):
            termine.append(row)
        else:
            print(f"Ungültiges Format gefunden: {row}")

# iCalendar-Datei erstellen
ical_content = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Mein Kalender//mxm.dk//\n"
for termin in termine:
    start_str, end_str = convert_to_ical_format(termin['datum'], termin['zeit'])
    event = (
        "BEGIN:VEVENT\n"
        f"DTSTART;TZID=Europe/Berlin:{start_str}\n"
        f"DTEND;TZID=Europe/Berlin:{end_str}\n"
        f"SUMMARY:{termin['beschreibung']}\n"
        f"DESCRIPTION:{termin['typ']}\n"
        "END:VEVENT\n"
    )
    ical_content += event
ical_content += "END:VCALENDAR"

# ICS-Datei speichern mit dem namen der csv datei
with open('csv_filepath', mode='w', encoding='utf-8-sig') as file:
    file.write(ical_content)
