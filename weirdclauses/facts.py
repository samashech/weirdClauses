"""Rule-based key facts extraction (money, percentages, dates, durations, notice periods)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class ExtractedFact:
    fact_type: str  # "money", "percentage", "date", "duration", "notice_period"
    value: str
    start_char: int
    end_char: int
    source_label: str = "rule-based"


class FactExtractor:
    """Regex-based auxiliary extractor for key factual clauses."""

    MONEY_REGEX: ClassVar[re.Pattern] = re.compile(
        r"(?:[$€£]|USD|EUR|GBP)\s*[\d,]+(?:\.\d{2})?|\b[\d,]+(?:\.\d{2})?\s*(?:dollars|euros|pounds)",
        re.IGNORECASE,
    )
    PERCENT_REGEX: ClassVar[re.Pattern] = re.compile(
        r"\b\d+(?:\.\d+)?%",
        re.IGNORECASE,
    )
    NOTICE_REGEX: ClassVar[re.Pattern] = re.compile(
        r"\b\d+\s*(?:day|days|calendar days|business days|month|months|weeks?)"
        r"\s*(?:written\s*)?notice\b",
        re.IGNORECASE,
    )

    def extract(self, text: str) -> list[ExtractedFact]:
        """Extract all rule-based key facts from text."""
        facts: list[ExtractedFact] = []
        for match in self.MONEY_REGEX.finditer(text):
            facts.append(ExtractedFact("money", match.group(0), match.start(), match.end()))
        for match in self.PERCENT_REGEX.finditer(text):
            facts.append(ExtractedFact("percentage", match.group(0), match.start(), match.end()))
        for match in self.NOTICE_REGEX.finditer(text):
            facts.append(ExtractedFact("notice_period", match.group(0), match.start(), match.end()))
        return facts
