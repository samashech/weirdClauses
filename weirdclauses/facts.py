"""Rule-based key facts extraction (money, percentages, dates, durations, notice periods).

This layer is strictly deterministic and rule-based (regex pattern matching).
It is distinct and independent from any language model surprisal scores.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, ClassVar

from weirdclauses.segment import Clause


@dataclass(frozen=True)
class ExtractedFact:
    """A rule-based extracted factual element from a contract clause."""

    kind: str  # "money", "percentage", "date", "duration", "notice_period", "auto_renewal"
    value: str
    start: int
    end: int
    source_label: str = "rule-based"

    @property
    def fact_type(self) -> str:
        return self.kind

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "value": self.value,
            "start": self.start,
            "end": self.end,
            "source_label": self.source_label,
        }


class FactExtractor:
    """Regex-based auxiliary extractor for key factual clauses.

    Explicitly labeled 'rule-based' to prevent any confusion with LM surprisal scoring.
    """

    MONEY_REGEX: ClassVar[re.Pattern] = re.compile(
        r"(?:[\$€£]|USD\s*|EUR\s*|GBP\s*)\d{1,3}(?:,\d{3})*(?:\.\d{2})?"
        r"|\b\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars|euros|pounds|USD|EUR|GBP)\b",
        re.IGNORECASE,
    )
    PERCENT_REGEX: ClassVar[re.Pattern] = re.compile(
        r"\b\d+(?:\.\d+)?\s*%(?!\w)"
        r"|\b\d+(?:\.\d+)?\s*percent\b"
        r"|\b(?:one|two|three|four|five|six|seven|eight|nine|ten|fifteen|twenty|twenty-five|"
        r"thirty|forty|fifty|hundred)\s+percent\b",
        re.IGNORECASE,
    )
    NOTICE_REGEX: ClassVar[re.Pattern] = re.compile(
        r"\b(?:at\s+least\s+)?\d+\s*(?:calendar\s+|business\s+)?"
        r"(?:hours?|days?|weeks?|months?)\s*(?:prior\s+)?(?:written\s+)?notice\b"
        r"|\bnotice\s+of\s+(?:at\s+least\s+)?\d+\s*(?:calendar\s+|business\s+)?"
        r"(?:hours?|days?|weeks?|months?)\b",
        re.IGNORECASE,
    )
    AUTO_RENEWAL_REGEX: ClassVar[re.Pattern] = re.compile(
        r"\b(?:automatically\s+renew(?:s|ed|ing)?|"
        r"automatic\s+renewal|"
        r"renew\s+automatically|"
        r"roll\s+over\s+automatically|"
        r"successive\s+(?:terms?|periods?|months?|years?)|"
        r"shall\s+renew\s+unless|"
        r"continue\s+on\s+a\s+month-to-month\s+basis)\b",
        re.IGNORECASE,
    )
    DATE_REGEX: ClassVar[re.Pattern] = re.compile(
        r"\b\d{4}-\d{2}-\d{2}\b"
        r"|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"
        r"|\b(?:\d{1,2}(?:st|nd|rd|th)?\s+(?:day\s+of\s+|of\s+)?)?"
        r"(?:January|February|March|April|May|June|July|August|September|October|November|December|"
        r"Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.?"
        r"(?:\s+\d{1,2}(?:st|nd|rd|th)?)?,?\s+\d{4}\b",
        re.IGNORECASE,
    )
    DURATION_REGEX: ClassVar[re.Pattern] = re.compile(
        r"\b(?:month-to-month|week-to-week|year-to-year)\b"
        r"|\b(?:term\s+of\s+)?(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|twelve|"
        r"twenty-four)\s+(?:calendar\s+|business\s+|continuous\s+)?(?:hours?|days?|weeks?|months?|years?)\b",
        re.IGNORECASE,
    )

    def extract(self, text: str, base_offset: int = 0) -> list[ExtractedFact]:
        """Extract all rule-based key facts from text, avoiding overlapping spans."""
        # Priority order: auto-renewal, notice, money, percent, date, duration
        patterns: list[tuple[str, re.Pattern]] = [
            ("auto_renewal", self.AUTO_RENEWAL_REGEX),
            ("notice_period", self.NOTICE_REGEX),
            ("money", self.MONEY_REGEX),
            ("percentage", self.PERCENT_REGEX),
            ("date", self.DATE_REGEX),
            ("duration", self.DURATION_REGEX),
        ]

        occupied_spans: list[tuple[int, int]] = []
        facts: list[ExtractedFact] = []

        for kind, pattern in patterns:
            for match in pattern.finditer(text):
                m_start, m_end = match.start(), match.end()
                # Check overlap with already extracted spans
                overlaps = any(max(m_start, s) < min(m_end, e) for s, e in occupied_spans)
                if overlaps:
                    continue
                occupied_spans.append((m_start, m_end))
                facts.append(
                    ExtractedFact(
                        kind=kind,
                        value=match.group(0),
                        start=m_start + base_offset,
                        end=m_end + base_offset,
                        source_label="rule-based",
                    )
                )

        facts.sort(key=lambda f: f.start)
        return facts


_GLOBAL_EXTRACTOR = FactExtractor()


def extract_facts(text: str, base_offset: int = 0) -> list[ExtractedFact]:
    """Convenience function to extract facts from text."""
    return _GLOBAL_EXTRACTOR.extract(text, base_offset=base_offset)


def attach_facts_to_clauses(clauses: Sequence[Clause]) -> dict[int, list[ExtractedFact]]:
    """Extract and attach rule-based facts to each clause keyed by clause ID."""
    mapping: dict[int, list[ExtractedFact]] = {}
    for c in clauses:
        mapping[c.id] = extract_facts(c.text, base_offset=c.start)
    return mapping
