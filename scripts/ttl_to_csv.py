#!/usr/bin/env python3
"""Convert SPARQL example Turtle files into the CSV format used by EMI."""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

try:
    from rdflib import Graph, Namespace, RDF, RDFS
    from rdflib.term import Identifier, Literal
except ImportError as exc:  # pragma: no cover - rdflib is a runtime dependency
    raise SystemExit(
        "rdflib is required to run this utility. Install it with 'pip install rdflib'."
    ) from exc


SH = Namespace("http://www.w3.org/ns/shacl#")
SPEX = Namespace("https://purl.expasy.org/sparql-examples/ontology#")

# Order matters: the first predicate that has a value is used as the query text.
QUERY_PREDICATES = (SH.select, SH.ask, SH.construct, SPEX.describe)


@dataclass
class ExampleRow:
    """Represents a single CSV row."""

    identifier: str
    backend_id: int
    name: str
    query: str

    def as_csv_row(self, include_identifier: bool = True) -> List[str]:
        return [
            self.identifier if include_identifier else "",
            str(self.backend_id),
            self.name,
            self.query,
            "",
            "~",
        ]


def iter_examples(ttl_file: Path, backend_id: int) -> Iterable[ExampleRow]:
    """Yield ExampleRow objects for each sh:SPARQLExecutable in a TTL file."""
    graph = Graph()
    graph.parse(ttl_file)

    for subject in graph.subjects(RDF.type, SH.SPARQLExecutable):
        identifier = extract_identifier(subject, ttl_file)
        name = pick_comment(graph.objects(subject, RDFS.comment), ttl_file)
        query = pick_query(graph, subject, ttl_file)

        yield ExampleRow(identifier=identifier, backend_id=backend_id, name=name, query=query)


def extract_identifier(subject: Identifier, ttl_file: Path) -> str:
    """Extract a readable identifier from a subject URI or blank node."""
    text = str(subject).strip()
    for separator in ("#", "/"):
        if separator in text:
            text = text.rsplit(separator, 1)[-1]
    return text or ttl_file.stem


def pick_comment(comments: Iterable[Literal], ttl_file: Path) -> str:
    """Return the preferred comment, favouring English labels."""
    fallback = None
    for literal in comments:
        if not isinstance(literal, Literal):
            continue
        if literal.language == "en":
            return str(literal)
        if fallback is None:
            fallback = str(literal)
    if fallback:
        return fallback
    return ttl_file.stem


def pick_query(graph: Graph, subject: Identifier, ttl_file: Path) -> str:
    """Return the SPARQL query string, checking predicates in priority order."""
    for predicate in QUERY_PREDICATES:
        literal = next(graph.objects(subject, predicate), None)
        if literal is not None:
            return str(literal)
    raise ValueError(f"No SPARQL query found in {ttl_file} for subject {subject}")


def natural_sort_key(value: str) -> Sequence:
    """Split strings into numeric and textual chunks for deterministic ordering."""
    if value.isdigit():
        return (0, int(value))
    return (1, value)


def parse_arguments(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "examples_dir",
        type=Path,
        help="Directory containing turtle files for one example collection.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Destination CSV file. Defaults to stdout when omitted.",
    )
    parser.add_argument(
        "--backend-id",
        type=int,
        default=69,
        help="Numeric backend identifier to include in the CSV (default: 69).",
    )
    parser.add_argument(
        "--prefix-id-in-title",
        action="store_true",
        help="Prefix each title with its identifier (e.g. '#1 Title').",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_arguments(argv or sys.argv[1:])

    if not args.examples_dir.is_dir():
        raise SystemExit(f"Directory not found: {args.examples_dir}")

    rows: List[ExampleRow] = []
    ttl_files = sorted(
        path
        for path in args.examples_dir.iterdir()
        if path.is_file() and path.suffix.lower() == ".ttl"
    )

    if not ttl_files:
        raise SystemExit(f"No .ttl files found in {args.examples_dir}")

    for ttl_file in ttl_files:
        rows.extend(iter_examples(ttl_file, args.backend_id))

    rows.sort(key=lambda row: natural_sort_key(row.identifier))

    if args.prefix_id_in_title:
        for row in rows:
            row.name = f"ex:{row.identifier} {row.name}"

    destination = args.output.open("w", newline="", encoding="utf-8") if args.output else sys.stdout
    # Ensure we do not close stdout when using context manager
    close_output = destination is not sys.stdout

    writer = csv.writer(destination, quoting=csv.QUOTE_ALL, lineterminator="\n")
    writer.writerow(["id", "backend", "name", "query", "Structure of sortKey [idcode]", "sortKey"])
    for row in rows:
        writer.writerow(row.as_csv_row(include_identifier=not args.prefix_id_in_title))

    if close_output:
        destination.close()

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
