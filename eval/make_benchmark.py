"""Generate synthetic rental agreements benchmark with seeded ground truth."""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent / "data"
STANDARDS_FILE = DATA_DIR / "held_out_standards.json"
UNUSUAL_FILE = DATA_DIR / "planted_unusual.json"
BENCHMARK_OUTPUT_FILE = DATA_DIR / "benchmark.json"


@dataclass
class BenchmarkClause:
    """Clause record inside a synthetic benchmark document."""

    index: int
    title: str
    text: str
    is_planted: bool
    category: str
    source_id: str


@dataclass
class BenchmarkAgreement:
    """Synthetic benchmark agreement with text and ground truth labels."""

    id: str
    title: str
    text: str
    clauses: list[BenchmarkClause]
    num_total_clauses: int
    num_planted_clauses: int


def load_pool_data() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Load held-out standards and planted unusual clause pools."""
    if not STANDARDS_FILE.exists() or not UNUSUAL_FILE.exists():
        raise FileNotFoundError("Missing held-out standards or planted unusual JSON files.")
    standards = json.loads(STANDARDS_FILE.read_text(encoding="utf-8"))
    unusual = json.loads(UNUSUAL_FILE.read_text(encoding="utf-8"))
    return standards, unusual


def build_agreement(
    doc_index: int,
    rng: random.Random,
    standards_pool: list[dict[str, Any]],
    unusual_pool: list[dict[str, Any]],
) -> BenchmarkAgreement:
    """Generate a single synthetic agreement with sampled standard and planted clauses."""
    num_standards = rng.randint(10, 15)
    num_planted = rng.randint(2, 4)

    sampled_standards = rng.sample(standards_pool, num_standards)
    sampled_unusual = rng.sample(unusual_pool, num_planted)

    # Convert to candidate items
    items: list[tuple[dict[str, Any], bool]] = [(c, False) for c in sampled_standards] + [
        (c, True) for c in sampled_unusual
    ]

    # Deterministic shuffle to scatter planted clauses throughout document
    rng.shuffle(items)

    # Format document with numbered section headings
    formatted_clauses: list[BenchmarkClause] = []
    text_blocks: list[str] = [
        "RESIDENTIAL LEASE AGREEMENT",
        "This agreement is entered into between Landlord and Tenant on the terms below.\n",
    ]

    for idx, (data, is_planted) in enumerate(items, start=1):
        title = data["title"].upper()
        content = data["text"].strip()
        category = data.get("category", "standard")
        source_id = data["id"]

        text_blocks.append(f"{idx}. {title}\n{content}\n")
        formatted_clauses.append(
            BenchmarkClause(
                index=idx,
                title=title,
                text=content,
                is_planted=is_planted,
                category=category,
                source_id=source_id,
            )
        )

    full_text = "\n".join(text_blocks).strip()
    return BenchmarkAgreement(
        id=f"benchmark_agreement_{doc_index:03d}",
        title=f"Synthetic Rental Lease #{doc_index + 1}",
        text=full_text,
        clauses=formatted_clauses,
        num_total_clauses=len(formatted_clauses),
        num_planted_clauses=num_planted,
    )


def generate_benchmark(
    count: int = 100,
    seed: int = 42,
    output_path: Path = BENCHMARK_OUTPUT_FILE,
) -> list[BenchmarkAgreement]:
    """Generate reproducible benchmark of N agreements with seeded ground truth."""
    standards_pool, unusual_pool = load_pool_data()
    rng = random.Random(seed)

    agreements: list[BenchmarkAgreement] = []
    for i in range(count):
        doc = build_agreement(i, rng, standards_pool, unusual_pool)
        agreements.append(doc)

    serialized = [asdict(a) for a in agreements]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(serialized, indent=2, ensure_ascii=False), encoding="utf-8")
    return agreements


if __name__ == "__main__":
    docs = generate_benchmark(100, seed=42)
    total_clauses = sum(d.num_total_clauses for d in docs)
    total_planted = sum(d.num_planted_clauses for d in docs)
    print(f"Generated {len(docs)} benchmark agreements in {BENCHMARK_OUTPUT_FILE}")
    print(f"Total clauses: {total_clauses} | Total planted unusual: {total_planted}")
