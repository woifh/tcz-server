"""Changelog service for parsing and serving changelog data."""
import os
import re
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ChangelogEntry:
    """Represents a single changelog entry (version)."""
    version: str
    date: str
    changes: dict


class ChangelogService:
    """Service for parsing and serving changelog data from CHANGELOG.md."""

    CHANGELOG_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'CHANGELOG.md'
    )

    # Regex patterns for parsing
    VERSION_PATTERN = re.compile(r'^## \[(\d+\.\d+\.\d+(?:-\w+)?)\] - (\d{4}-\d{2}-\d{2})$')
    CATEGORY_PATTERN = re.compile(r'^### (.+)$')
    CHANGE_PATTERN = re.compile(r'^- (.+)$')

    @classmethod
    def get_changelog(cls) -> tuple[list[ChangelogEntry], Optional[str]]:
        """
        Parse and return all changelog entries.

        Returns:
            tuple: (list of ChangelogEntry, error message or None)
        """
        try:
            if not os.path.exists(cls.CHANGELOG_PATH):
                logger.warning(f"Changelog file not found: {cls.CHANGELOG_PATH}")
                return [], "Changelog-Datei nicht gefunden"

            with open(cls.CHANGELOG_PATH, 'r', encoding='utf-8') as f:
                content = f.read()

            return cls._parse_changelog(content), None

        except Exception as e:
            logger.error(f"Error reading changelog: {e}")
            return [], f"Fehler beim Lesen des Changelogs: {str(e)}"

    @classmethod
    def _parse_changelog(cls, content: str) -> list[ChangelogEntry]:
        """Parse changelog content into structured entries."""
        entries = []
        current_entry = None
        current_category = None

        for line in content.split('\n'):
            line = line.rstrip()

            # Check for version header
            version_match = cls.VERSION_PATTERN.match(line)
            if version_match:
                if current_entry:
                    entries.append(current_entry)
                current_entry = ChangelogEntry(
                    version=version_match.group(1),
                    date=version_match.group(2),
                    changes={}
                )
                current_category = None
                continue

            # Check for category header
            category_match = cls.CATEGORY_PATTERN.match(line)
            if category_match and current_entry:
                current_category = category_match.group(1)
                current_entry.changes[current_category] = []
                continue

            # Check for change item
            change_match = cls.CHANGE_PATTERN.match(line)
            if change_match and current_entry and current_category:
                current_entry.changes[current_category].append(change_match.group(1))

        # Add last entry
        if current_entry:
            entries.append(current_entry)

        return entries

    @classmethod
    def get_changelog_as_dict(cls) -> tuple[list[dict], Optional[str]]:
        """
        Get changelog entries as JSON-serializable dictionaries.

        Returns:
            tuple: (list of dict entries, error message or None)
        """
        entries, error = cls.get_changelog()
        if error:
            return [], error

        return [
            {
                'version': entry.version,
                'date': entry.date,
                'changes': entry.changes
            }
            for entry in entries
        ], None
