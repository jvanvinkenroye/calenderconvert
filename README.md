# CalendarConvert

A Python utility to convert CSV calendar/appointment data to iCalendar (.ics) format.

## Features

- Converts CSV files with appointment data to standard iCalendar format
- Supports German date format (DD.MM.YY) and time ranges (HH:MM - HH:MM)
- Compatible with Outlook, Google Calendar, Apple Calendar, and other calendar apps
- Configurable timezone support
- Input validation with helpful error messages
- Unique event IDs for proper calendar syncing

## Requirements

- Python 3.9+

## Installation

Clone the repository:

```bash
git clone https://github.com/jvanvinkenroye/calenderconvert.git
cd calenderconvert
```

## Usage

### Basic Usage

```bash
python main.py termine.csv
```

This creates `termine.ics` in the same directory.

### Options

```bash
python main.py <input.csv> [-o OUTPUT] [-t TIMEZONE] [-v]
```

| Option | Description |
|--------|-------------|
| `-o, --output` | Output ICS file path (default: same name as input with .ics extension) |
| `-t, --timezone` | Timezone for events (default: Europe/Berlin) |
| `-v, --verbose` | Enable verbose output |
| `-h, --help` | Show help message |

### Examples

```bash
# Convert with custom output path
python main.py termine.csv -o calendar.ics

# Use different timezone
python main.py termine.csv -t America/New_York

# Verbose mode
python main.py termine.csv -v
```

## CSV Format

The input CSV file must use semicolons (`;`) as delimiters and include these columns:

| Column | Format | Description |
|--------|--------|-------------|
| `datum` | DD.MM.YY | Date of the appointment |
| `zeit` | HH:MM - HH:MM | Start and end time |
| `beschreibung` | text | Event summary/title |
| `typ` | text (optional) | Event description |

### Example CSV

```csv
datum;zeit;beschreibung;typ
30.11.23;09:00 - 10:30;Team Meeting;Weekly sync
01.12.23;14:00 - 15:00;Project Review;
```

## Running Tests

```bash
pip install pytest
pytest test_main.py -v
```

## License

MIT
