#!/usr/bin/env python3
"""Ingest economic series metadata from CSV into OpenSearch.

This script mirrors the former Pinecone indexing flow but writes chunked
documents into an OpenSearch index using basic auth.

Environment variables:
    OPENSEARCH_HOST        (required)
    OPENSEARCH_USERNAME    (required)
    OPENSEARCH_PASSWORD    (required)
    OPENSEARCH_PORT        (optional, default 443)
    OPENSEARCH_INDEX       (optional, default "fred-series")
"""

from __future__ import annotations

import csv
import os
import sys
import uuid
from typing import Iterable, Iterator

from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from opensearchpy import OpenSearch, helpers
from tqdm import tqdm

load_dotenv()

DEFAULT_INDEX = "fred-series"


def get_env(name: str, *, required: bool = True, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if required and not value:
        raise RuntimeError(f"{name} environment variable is required.")
    return value or ""


def create_client() -> OpenSearch:
    host = get_env("OPENSEARCH_HOST")
    port = int(os.getenv("OPENSEARCH_PORT", "443"))
    username = get_env("OPENSEARCH_USERNAME")
    password = get_env("OPENSEARCH_PASSWORD")

    return OpenSearch(
        hosts=[{"host": host, "port": port}],
        http_auth=(username, password),
        use_ssl=port == 443,
        verify_certs=True,
        timeout=30,
    )


def ensure_index(client: OpenSearch, index_name: str, *, recreate: bool = False) -> None:
    if client.indices.exists(index=index_name):
        if recreate:
            print(f"Deleting existing index '{index_name}' …")
            client.indices.delete(index=index_name)
        else:
            return

    mapping = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 1,
        },
        "mappings": {
            "properties": {
                "series_id": {"type": "keyword"},
                "title": {
                    "type": "text",
                    "fields": {"raw": {"type": "keyword", "ignore_above": 256}},
                },
                "frequency": {"type": "keyword"},
                "frequency_short": {"type": "keyword"},
                "units": {"type": "keyword"},
                "units_short": {"type": "keyword"},
                "season": {"type": "keyword"},
                "season_short": {"type": "keyword"},
                "period_description": {"type": "text"},
                "content": {"type": "text"},
                "chunk_index": {"type": "integer"},
                "user_id": {"type": "keyword"},
                "data_type": {"type": "keyword"},
            }
        },
    }

    client.indices.create(index=index_name, body=mapping)
    print(f"Created index '{index_name}' with mapping.")


def build_content(row: dict[str, str]) -> str:
    parts: list[str] = [
        f"Series ID: {row.get('series_id', '')}",
        f"Title: {row.get('title', '')}",
        f"Frequency: {row.get('frequency', '')} ({row.get('frequency_short', '')})",
        f"Units: {row.get('units', '')} ({row.get('units_short', '')})",
        f"Seasonality: {row.get('season', '')} ({row.get('season_short', '')})",
    ]
    if row.get("period_description"):
        parts.append(f"Period Description: {row['period_description']}")
    return "\n".join(part for part in parts if part.strip())


splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100,
    separators=["\n\n", "\n", ".", " "],
)


def iter_documents(
    csv_path: str,
    *,
    user_id: str,
    index_name: str,
) -> Iterator[dict[str, object]]:
    with open(csv_path, "r", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            base = {
                "series_id": row.get("series_id", "").strip(),
                "title": row.get("title", "").strip(),
                "frequency": row.get("frequency", "").strip(),
                "frequency_short": row.get("frequency_short", "").strip(),
                "units": row.get("units", "").strip(),
                "units_short": row.get("units_short", "").strip(),
                "season": row.get("season", "").strip(),
                "season_short": row.get("season_short", "").strip(),
                "period_description": row.get("period_description", "").strip(),
                "user_id": user_id,
                "data_type": "economic_series",
            }
            content = build_content(row)
            chunks = splitter.split_text(content) or [content]
            for chunk_index, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue
                doc = {
                    **base,
                    "content": chunk,
                    "chunk_index": chunk_index,
                }
                yield {
                    "_index": index_name,
                    "_id": str(uuid.uuid4()),
                    "_source": doc,
                }


def bulk_index(
    client: OpenSearch,
    actions: Iterable[dict[str, object]],
    *,
    chunk_size: int = 500,
) -> int:
    success, errors = helpers.bulk(
        client,
        actions=actions,
        chunk_size=chunk_size,
        raise_on_error=False,
        request_timeout=60,
    )
    if errors:
        print(f"Encountered {len(errors)} errors during bulk indexing.", file=sys.stderr)
    return success


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "csv_path",
        nargs="?",
        default="seriesdatasample.csv",
        help="Path to the CSV file containing series metadata.",
    )
    parser.add_argument(
        "--user-id",
        default=os.getenv("DEFAULT_USER_ID", "series-user"),
        help="User ID to attach to documents (default: series-user).",
    )
    parser.add_argument(
        "--index",
        default=os.getenv("OPENSEARCH_INDEX", DEFAULT_INDEX),
        help=f"OpenSearch index name (default: {DEFAULT_INDEX}).",
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Delete the existing index before ingesting (use with caution).",
    )
    args = parser.parse_args()

    index_name = args.index

    client = create_client()
    ensure_index(client, index_name, recreate=args.recreate)

    print(f"Loading documents from {args.csv_path} ...")
    actions = list(
        tqdm(
            iter_documents(args.csv_path, user_id=args.user_id, index_name=index_name),
            desc="Preparing chunks",
        )
    )
    if not actions:
        print("No documents generated from CSV; aborting.")
        sys.exit(0)

    indexed = bulk_index(client, actions)
    client.indices.refresh(index=index_name)
    print(f"✅ Indexed {indexed} documents into '{index_name}'.")
