"""Unit tests for CalendarConvert."""

import csv
import tempfile
from pathlib import Path

import pytest

from main import (
    is_valid_date,
    is_valid_time,
    convert_to_ical_format,
    generate_uid,
    sanitize_text,
    create_event,
    read_csv,
    convert_csv_to_ics,
)


class TestIsValidDate:
    """Tests for is_valid_date function."""

    def test_valid_date(self):
        assert is_valid_date("30.11.23") is True
        assert is_valid_date("01.01.24") is True
        assert is_valid_date("31.12.99") is True

    def test_invalid_date_format(self):
        assert is_valid_date("2023-11-30") is False
        assert is_valid_date("30/11/23") is False
        assert is_valid_date("11.30.23") is False

    def test_invalid_date_values(self):
        assert is_valid_date("32.11.23") is False
        assert is_valid_date("30.13.23") is False
        assert is_valid_date("00.11.23") is False

    def test_empty_and_none(self):
        assert is_valid_date("") is False
        assert is_valid_date("   ") is False


class TestIsValidTime:
    """Tests for is_valid_time function."""

    def test_valid_time(self):
        assert is_valid_time("09:00 - 10:30") is True
        assert is_valid_time("00:00 - 23:59") is True
        assert is_valid_time("12:00 - 13:00") is True

    def test_invalid_time_format(self):
        assert is_valid_time("09:00-10:30") is False  # missing spaces around dash
        assert is_valid_time("09:00 to 10:30") is False
        assert is_valid_time("9am - 10am") is False

    def test_invalid_time_values(self):
        assert is_valid_time("25:00 - 10:30") is False
        assert is_valid_time("09:60 - 10:30") is False

    def test_empty_and_none(self):
        assert is_valid_time("") is False
        assert is_valid_time(None) is False


class TestConvertToIcalFormat:
    """Tests for convert_to_ical_format function."""

    def test_basic_conversion(self):
        start, end = convert_to_ical_format("30.11.23", "09:00 - 10:30")
        assert start == "20231130T090000"
        assert end == "20231130T103000"

    def test_midnight_times(self):
        start, end = convert_to_ical_format("01.01.24", "00:00 - 23:59")
        assert start == "20240101T000000"
        assert end == "20240101T235900"

    def test_with_extra_spaces(self):
        start, end = convert_to_ical_format("30.11.23", "09:00  -  10:30")
        assert start == "20231130T090000"
        assert end == "20231130T103000"


class TestGenerateUid:
    """Tests for generate_uid function."""

    def test_generates_uid(self):
        termin = {"datum": "30.11.23", "zeit": "09:00 - 10:30", "beschreibung": "Test"}
        uid = generate_uid(termin)
        assert uid.endswith("@calendarconvert")
        assert len(uid) > 16

    def test_same_input_same_uid(self):
        termin = {"datum": "30.11.23", "zeit": "09:00 - 10:30", "beschreibung": "Test"}
        uid1 = generate_uid(termin)
        uid2 = generate_uid(termin)
        assert uid1 == uid2

    def test_different_input_different_uid(self):
        termin1 = {"datum": "30.11.23", "zeit": "09:00 - 10:30", "beschreibung": "Test1"}
        termin2 = {"datum": "30.11.23", "zeit": "09:00 - 10:30", "beschreibung": "Test2"}
        assert generate_uid(termin1) != generate_uid(termin2)


class TestSanitizeText:
    """Tests for sanitize_text function."""

    def test_normal_text(self):
        assert sanitize_text("Hello World") == "Hello World"

    def test_escapes_semicolon(self):
        assert sanitize_text("Test;Value") == "Test\\;Value"

    def test_escapes_comma(self):
        assert sanitize_text("Test,Value") == "Test\\,Value"

    def test_escapes_backslash(self):
        assert sanitize_text("Test\\Value") == "Test\\\\Value"

    def test_escapes_newline(self):
        assert sanitize_text("Test\nValue") == "Test\\nValue"

    def test_empty_string(self):
        assert sanitize_text("") == ""

    def test_none_like(self):
        assert sanitize_text(None) == ""


class TestCreateEvent:
    """Tests for create_event function."""

    def test_creates_valid_event(self):
        termin = {
            "datum": "30.11.23",
            "zeit": "09:00 - 10:30",
            "beschreibung": "Test Event",
            "typ": "Lecture"
        }
        event = create_event(termin)
        assert "BEGIN:VEVENT" in event
        assert "END:VEVENT" in event
        assert "DTSTART;TZID=Europe/Berlin:20231130T090000" in event
        assert "DTEND;TZID=Europe/Berlin:20231130T103000" in event
        assert "SUMMARY:Test Event" in event
        assert "DESCRIPTION:Lecture" in event
        assert "UID:" in event

    def test_custom_timezone(self):
        termin = {
            "datum": "30.11.23",
            "zeit": "09:00 - 10:30",
            "beschreibung": "Test",
            "typ": ""
        }
        event = create_event(termin, timezone="America/New_York")
        assert "TZID=America/New_York" in event


class TestReadCsv:
    """Tests for read_csv function."""

    def test_reads_valid_csv(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("datum;zeit;beschreibung;typ\n")
            f.write("30.11.23;09:00 - 10:30;Test Event;Lecture\n")
            temp_path = Path(f.name)

        try:
            termine = read_csv(temp_path)
            assert len(termine) == 1
            assert termine[0]['beschreibung'] == "Test Event"
        finally:
            temp_path.unlink()

    def test_skips_invalid_rows(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("datum;zeit;beschreibung;typ\n")
            f.write("30.11.23;09:00 - 10:30;Valid;Type1\n")
            f.write("invalid;09:00 - 10:30;Invalid Date;Type2\n")
            f.write("30.11.23;invalid;Invalid Time;Type3\n")
            temp_path = Path(f.name)

        try:
            termine = read_csv(temp_path)
            assert len(termine) == 1
            assert termine[0]['beschreibung'] == "Valid"
        finally:
            temp_path.unlink()

    def test_missing_columns_raises_error(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("datum;zeit\n")
            f.write("30.11.23;09:00 - 10:30\n")
            temp_path = Path(f.name)

        try:
            with pytest.raises(csv.Error, match="Missing required columns"):
                read_csv(temp_path)
        finally:
            temp_path.unlink()

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            read_csv(Path("/nonexistent/file.csv"))


class TestConvertCsvToIcs:
    """Tests for convert_csv_to_ics function."""

    def test_creates_ics_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "test.csv"
            csv_path.write_text(
                "datum;zeit;beschreibung;typ\n"
                "30.11.23;09:00 - 10:30;Test Event;Lecture\n",
                encoding='utf-8'
            )

            output_path = convert_csv_to_ics(csv_path)

            assert output_path.exists()
            assert output_path.suffix == ".ics"
            content = output_path.read_text()
            assert "BEGIN:VCALENDAR" in content
            assert "BEGIN:VEVENT" in content

    def test_custom_output_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "test.csv"
            ics_path = Path(tmpdir) / "custom.ics"
            csv_path.write_text(
                "datum;zeit;beschreibung;typ\n"
                "30.11.23;09:00 - 10:30;Test;Type\n",
                encoding='utf-8'
            )

            output_path = convert_csv_to_ics(csv_path, ics_path)

            assert output_path == ics_path
            assert ics_path.exists()

    def test_empty_csv_raises_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "empty.csv"
            csv_path.write_text(
                "datum;zeit;beschreibung;typ\n",
                encoding='utf-8'
            )

            with pytest.raises(ValueError, match="No valid appointments"):
                convert_csv_to_ics(csv_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
