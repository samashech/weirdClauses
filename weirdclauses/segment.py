"""Clause segmentation module partitioning documents into lossless spans."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

ClauseKind = Literal["clause", "heading", "frame"]


@dataclass
class Clause:
    id: int
    text: str
    start: int
    end: int
    kind: ClauseKind
    parent_heading: str | None = None

    @property
    def content(self) -> str:
        """Return the stripped content for scoring or display."""
        return self.text.strip()


# Backwards compatibility alias for Phase 0
ClauseSpan = Clause


def _is_signature_start(line: str) -> bool:
    clean = line.strip().upper()
    markers = (
        "IN WITNESS WHEREOF",
        "AS WITNESS",
        "SIGNED BY",
        "SIGNATURES:",
        "SIGNED, SEALED",
        "EXECUTED AS AN AGREEMENT",
    )
    if any(s in clean for s in markers):
        return True
    return bool(re.match(r"^(?:LANDLORD|TENANT|WITNESS|LESSOR|LESSEE)\s*[:_]", clean))


def _is_preamble_start(line: str) -> bool:
    clean = line.strip()
    pattern = r"^(?:This\s+.*?(?:Lease|Agreement|Tenancy|Contract)|Between:|Recitals|Witnesseth)"
    return bool(re.match(pattern, clean, re.IGNORECASE))


def _is_heading(line: str) -> bool:
    s = line.strip()
    if not s or len(s) > 80 or _is_signature_start(s):
        return False

    if re.match(r"^(?:ARTICLE|SECTION|CLAUSE|SCHEDULE)\s+[0-9IVXLCDM\.]+", s, re.IGNORECASE):
        return not (s.endswith(".") and len(s.split()) > 10)

    if re.match(r"^\d+(?:\.\d+)*\.?\s+[A-Z][A-Za-z0-9\s/&,\-:]*$", s):
        words = s.split()
        keywords = ("shall", "agrees", "must", "tenant", "landlord", "covenants", "warrants")
        if len(words) <= 10 and not any(w.lower() in keywords for w in words[2:]):
            return True

    title_words = ("AGREEMENT", "LEASE", "CONTRACT", "MEMORANDUM")
    return (
        s.isupper()
        and len(s.split()) <= 6
        and not s.endswith(".")
        and not any(w in s for w in title_words)
    )


def _is_clause_marker(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    pattern = r"^(?:\(\s*[a-zA-Z0-9]+\s*\)|[a-zA-Z0-9]+\)\s+|\d+(?:\.\d+)*\.?\s+|[IVXLCDM]+\.\s+)"
    return bool(re.match(pattern, s))


def _token_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def _find_boundaries(text: str) -> tuple[list[int], int | None]:
    line_spans: list[tuple[int, int, str]] = []
    for m in re.finditer(r"(.*?)(?:\r?\n|$)", text):
        if m.start() == len(text):
            break
        line_spans.append((m.start(), m.end(), m.group(0)))

    n = len(line_spans)
    boundaries = [0]
    has_seen_first_body = False
    first_body_pos: int | None = None
    has_any_headings = any(_is_heading(s[2]) or _is_clause_marker(s[2]) for s in line_spans)

    for i in range(n):
        start, end, full = line_spans[i]
        content = full.strip()
        if not content:
            continue

        if _is_signature_start(content):
            boundaries.append(start)
            break

        if _is_heading(content) or _is_clause_marker(content):
            if first_body_pos is None:
                first_body_pos = start
            has_seen_first_body = True
            boundaries.append(start)
            if _is_heading(content) and i + 1 < n:
                boundaries.append(line_spans[i + 1][0])
            continue

        is_prev_blank = i > 0 and not line_spans[i - 1][2].strip()
        if (has_seen_first_body or not has_any_headings) and is_prev_blank:
            is_new_body = (
                not has_seen_first_body
                and first_body_pos is None
                and not _is_preamble_start(content)
                and not any(w in content.upper() for w in ("AGREEMENT", "LEASE"))
            )
            if is_new_body:
                first_body_pos = start
                has_seen_first_body = True
            boundaries.append(start)

    boundaries.append(len(text))
    return sorted(set(boundaries)), first_body_pos


def segment_clauses(text: str, min_tokens: int = 12) -> list[Clause]:
    """Segment document text into clauses with exact character spans."""
    if not text:
        return []

    unique_b, first_body_pos = _find_boundaries(text)
    raw_clauses: list[Clause] = []
    current_parent_heading: str | None = None
    in_signature = False

    for i in range(len(unique_b) - 1):
        s, e = unique_b[i], unique_b[i + 1]
        chunk_text = text[s:e]
        first_line = chunk_text.strip().splitlines()[0] if chunk_text.strip() else ""

        if _is_signature_start(first_line):
            in_signature = True

        if in_signature or (first_body_pos is not None and s < first_body_pos):
            kind: ClauseKind = "frame"
            parent = None
        elif _is_heading(first_line):
            kind = "heading"
            current_parent_heading = first_line
            parent = None
        else:
            kind = "clause"
            parent = current_parent_heading

        raw_clauses.append(
            Clause(id=i, text=chunk_text, start=s, end=e, kind=kind, parent_heading=parent)
        )

    # First merge pass: combine adjacent frames and short fragments into previous clause
    merged: list[Clause] = []
    for c in raw_clauses:
        if not merged:
            merged.append(c)
            continue

        prev = merged[-1]
        if prev.kind == "frame" and c.kind == "frame":
            merged[-1] = Clause(prev.id, prev.text + c.text, prev.start, c.end, "frame", None)
            continue

        can_merge_prev = (
            c.kind == "clause"
            and _token_count(c.text) < min_tokens
            and prev.kind == "clause"
            and prev.parent_heading == c.parent_heading
        )
        if can_merge_prev:
            merged[-1] = Clause(
                prev.id, prev.text + c.text, prev.start, c.end, "clause", prev.parent_heading
            )
            continue

        merged.append(c)

    # Second merge pass: leading clause fragments merged forward into next clause
    final_clauses: list[Clause] = []
    idx = 0
    while idx < len(merged):
        curr = merged[idx]
        can_merge_fwd = (
            curr.kind == "clause"
            and _token_count(curr.text) < min_tokens
            and idx + 1 < len(merged)
            and merged[idx + 1].kind == "clause"
            and merged[idx + 1].parent_heading == curr.parent_heading
        )
        if can_merge_fwd:
            nxt = merged[idx + 1]
            merged[idx + 1] = Clause(
                curr.id, curr.text + nxt.text, curr.start, nxt.end, "clause", curr.parent_heading
            )
            idx += 1
            continue
        final_clauses.append(curr)
        idx += 1

    for cid, cl in enumerate(final_clauses):
        cl.id = cid

    return final_clauses
