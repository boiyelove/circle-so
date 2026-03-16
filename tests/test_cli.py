"""Tests for CLI commands."""
import os
import csv
from click.testing import CliRunner
from circle_so.cli import main
from circle_so.db.connection import get_connection


class TestCLI:
    def test_help(self):
        result = CliRunner().invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "spaces" in result.output
        assert "members" in result.output
        assert "moderators" in result.output
        assert "report" in result.output

    def test_spaces_help(self):
        result = CliRunner().invoke(main, ["spaces", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output
        assert "search" in result.output
        assert "rename" in result.output
        assert "lock" in result.output

    def test_members_help(self):
        result = CliRunner().invoke(main, ["members", "--help"])
        assert result.exit_code == 0
        assert "import" in result.output
        assert "audit" in result.output
        assert "add" in result.output
        assert "fix-missing" in result.output

    def test_moderators_help(self):
        result = CliRunner().invoke(main, ["moderators", "--help"])
        assert result.exit_code == 0
        assert "verify" in result.output
        assert "add" in result.output

    def test_report_help(self):
        result = CliRunner().invoke(main, ["report", "--help"])
        assert result.exit_code == 0
        assert "counts" in result.output
        assert "inactive" in result.output
        assert "missing" in result.output
        assert "export" in result.output


class TestMembersImport:
    def test_import_csv(self, tmp_path, monkeypatch):
        db_path = str(tmp_path / "test.db")
        monkeypatch.setenv("CIRCLE_SO_DB", db_path)

        csv_path = str(tmp_path / "learners.csv")
        with open(csv_path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["first_name", "email", "country", "PLG"])
            w.writerow(["Alice", "alice@example.com", "Kenya", "KCNA 001"])
            w.writerow(["Bob", "bob@example.com", "Nigeria", "KCNA 002"])

        result = CliRunner().invoke(main, ["--db", db_path, "members", "import", csv_path])
        assert result.exit_code == 0
        assert "Imported 2" in result.output

        conn = get_connection(db_path)
        count = conn.execute("SELECT COUNT(*) FROM members").fetchone()[0]
        assert count == 2
        conn.close()

    def test_import_idempotent(self, tmp_path, monkeypatch):
        db_path = str(tmp_path / "test.db")
        monkeypatch.setenv("CIRCLE_SO_DB", db_path)

        csv_path = str(tmp_path / "learners.csv")
        with open(csv_path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["first_name", "email", "country", "PLG"])
            w.writerow(["Alice", "alice@example.com", "Kenya", "KCNA 001"])

        CliRunner().invoke(main, ["--db", db_path, "members", "import", csv_path])
        CliRunner().invoke(main, ["--db", db_path, "members", "import", csv_path])

        conn = get_connection(db_path)
        count = conn.execute("SELECT COUNT(*) FROM members").fetchone()[0]
        assert count == 1
        conn.close()


class TestReportCounts:
    def test_counts_empty(self, tmp_path, monkeypatch):
        db_path = str(tmp_path / "test.db")
        monkeypatch.setenv("CIRCLE_SO_DB", db_path)
        result = CliRunner().invoke(main, ["--db", db_path, "report", "counts"])
        assert result.exit_code == 0
        assert "Total: 0" in result.output

    def test_counts_with_data(self, tmp_path, monkeypatch):
        db_path = str(tmp_path / "test.db")
        monkeypatch.setenv("CIRCLE_SO_DB", db_path)

        csv_path = str(tmp_path / "learners.csv")
        with open(csv_path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["first_name", "email", "country", "PLG"])
            w.writerow(["Alice", "a@example.com", "Kenya", "KCNA 001"])
            w.writerow(["Bob", "b@example.com", "Kenya", "KCNA 001"])
            w.writerow(["Carol", "c@example.com", "Kenya", "KCNA 002"])

        CliRunner().invoke(main, ["--db", db_path, "members", "import", csv_path])
        result = CliRunner().invoke(main, ["--db", db_path, "report", "counts"])
        assert result.exit_code == 0
        assert "KCNA 001" in result.output
        assert "KCNA 002" in result.output
        assert "Total: 3" in result.output

    def test_counts_with_prefix_filter(self, tmp_path, monkeypatch):
        db_path = str(tmp_path / "test.db")
        monkeypatch.setenv("CIRCLE_SO_DB", db_path)

        csv_path = str(tmp_path / "learners.csv")
        with open(csv_path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["first_name", "email", "country", "PLG"])
            w.writerow(["Alice", "a@example.com", "Kenya", "KCNA 001"])
            w.writerow(["Bob", "b@example.com", "Kenya", "CKAD 001"])

        CliRunner().invoke(main, ["--db", db_path, "members", "import", csv_path])
        result = CliRunner().invoke(main, ["--db", db_path, "report", "counts", "--prefix", "kcna"])
        assert "KCNA 001" in result.output
        assert "CKAD" not in result.output


class TestReportMissing:
    def test_missing_none(self, tmp_path, monkeypatch):
        db_path = str(tmp_path / "test.db")
        monkeypatch.setenv("CIRCLE_SO_DB", db_path)
        result = CliRunner().invoke(main, ["--db", db_path, "report", "missing"])
        assert result.exit_code == 0
        assert "No missing" in result.output
