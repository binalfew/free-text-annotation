"""
Date Normalization Utilities
=============================

Normalizes relative and absolute dates from news articles.

Author: Binalfew Kassa Mekonnen
Date: October 2025
"""

import dateparser
from datetime import datetime, timedelta
from typing import Optional, Dict
import re


class DateNormalizer:
    """
    Normalize dates from news articles to ISO format.
    """

    def __init__(self):
        """Initialize date normalizer."""
        # Common date patterns in news articles
        self.day_of_week = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }

    def normalize_date(self, date_text: str, reference_date: Optional[str] = None) -> Optional[str]:
        """
        Normalize a date string to ISO format (YYYY-MM-DD).

        Args:
            date_text: Date text from article (e.g., "Friday", "March 15, 2024")
            reference_date: Reference date for relative dates (e.g., article publication date)

        Returns:
            ISO format date string or None if cannot parse
        """
        if not date_text:
            return None

        date_text = date_text.strip()

        # Parse reference date if provided
        ref_datetime = None
        if reference_date:
            ref_datetime = dateparser.parse(reference_date)

        # Try to parse the date
        settings = {
            'PREFER_DATES_FROM': 'past',  # Most news articles report past events
            'RETURN_AS_TIMEZONE_AWARE': False
        }

        if ref_datetime:
            settings['RELATIVE_BASE'] = ref_datetime

        parsed_date = dateparser.parse(date_text, settings=settings)

        if parsed_date and ref_datetime:
            # CRITICAL FIX: If parsed date is in the past and matches the reference date's day of week,
            # it's likely the same day (e.g., "Friday" on Friday March 15 should be March 15, not previous Friday)
            if parsed_date < ref_datetime and parsed_date.weekday() == ref_datetime.weekday():
                # Check if it's a simple day-of-week reference (no other date info)
                simple_day_refs = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                if any(day in date_text.lower() for day in simple_day_refs) and len(date_text.split()) <= 2:
                    # Use reference date instead (same day)
                    return ref_datetime.strftime('%Y-%m-%d')
            return parsed_date.strftime('%Y-%m-%d')
        elif parsed_date:
            return parsed_date.strftime('%Y-%m-%d')

        # If dateparser failed, try manual parsing for common patterns
        return self._manual_parse(date_text, ref_datetime)

    def _manual_parse(self, date_text: str, reference_date: Optional[datetime] = None) -> Optional[str]:
        """
        Manual parsing for patterns that dateparser might miss.

        Args:
            date_text: Date text
            reference_date: Reference datetime

        Returns:
            ISO format date or None
        """
        text_lower = date_text.lower()

        # If no reference date, use today
        if not reference_date:
            reference_date = datetime.now()

        # Handle day of week (e.g., "Friday", "Tuesday morning")
        for day_name, day_num in self.day_of_week.items():
            if day_name in text_lower:
                # Find the most recent occurrence of this day
                days_back = (reference_date.weekday() - day_num) % 7
                if days_back == 0:
                    # If same day as reference date, use reference date itself
                    # (e.g., article published Friday, event happened "Friday" = same day)
                    return reference_date.strftime('%Y-%m-%d')
                target_date = reference_date - timedelta(days=days_back)
                return target_date.strftime('%Y-%m-%d')

        # Handle relative dates
        if 'yesterday' in text_lower:
            target_date = reference_date - timedelta(days=1)
            return target_date.strftime('%Y-%m-%d')
        elif 'today' in text_lower or 'tonight' in text_lower:
            return reference_date.strftime('%Y-%m-%d')
        elif 'last week' in text_lower:
            target_date = reference_date - timedelta(days=7)
            return target_date.strftime('%Y-%m-%d')
        elif 'last month' in text_lower:
            target_date = reference_date - timedelta(days=30)
            return target_date.strftime('%Y-%m-%d')

        return None

    def extract_and_normalize_date_from_metadata(self, article_metadata: str) -> Optional[str]:
        """
        Extract and normalize date from article metadata.

        Args:
            article_metadata: Metadata string (e.g., "March 15, 2024")

        Returns:
            ISO format date or None
        """
        if not article_metadata:
            return None

        # Look for date patterns
        date_patterns = [
            r'[A-Z][a-z]+ \d{1,2},? \d{4}',  # March 15, 2024
            r'\d{4}-\d{2}-\d{2}',              # 2024-03-15
            r'\d{1,2}/\d{1,2}/\d{4}',          # 03/15/2024
            r'\d{1,2}-\d{1,2}-\d{4}',          # 03-15-2024
        ]

        for pattern in date_patterns:
            match = re.search(pattern, article_metadata)
            if match:
                return self.normalize_date(match.group(0))

        return None


# Example usage
if __name__ == '__main__':
    normalizer = DateNormalizer()

    # Test cases
    test_dates = [
        ("Friday", "March 15, 2024"),
        ("Tuesday", "March 18, 2024"),
        ("March 15, 2024", None),
        ("yesterday", "March 16, 2024"),
        ("March 20, 2024", None),
    ]

    for date_text, ref_date in test_dates:
        normalized = normalizer.normalize_date(date_text, ref_date)
        print(f"{date_text} (ref: {ref_date}) -> {normalized}")
