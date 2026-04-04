#!/usr/bin/env python3
import argparse
import os
import sys
import time
from typing import Dict, List

import boto3


TABLE_KEYS = [
    "users",
    "quizzes",
    "attempts",
    "responses",
    "inspector_attempts",
]


def _resolve_table_name(env: str, app_name: str, key: str) -> str:
    return f"{app_name}-{env}-{key.replace('_', '-')}"


def _get_table_names(env: str, app_name: str, prefix: str) -> Dict[str, str]:
    explicit = {
        "users": os.getenv(f"{prefix}_DYNAMODB_USERS"),
        "quizzes": os.getenv(f"{prefix}_DYNAMODB_QUIZZES"),
        "attempts": os.getenv(f"{prefix}_DYNAMODB_ATTEMPTS"),
        "responses": os.getenv(f"{prefix}_DYNAMODB_RESPONSES"),
        "inspector_attempts": os.getenv(f"{prefix}_DYNAMODB_INSPECTOR"),
    }
    return {
        key: explicit[key] or _resolve_table_name(env, app_name, key)
        for key in TABLE_KEYS
    }


def _scan_all(table, limit: int | None) -> List[dict]:
    items: List[dict] = []
    kwargs = {}
    while True:
        if limit is not None:
            remaining = limit - len(items)
            if remaining <= 0:
                break
            kwargs["Limit"] = remaining
        response = table.scan(**kwargs)
        items.extend(response.get("Items", []))
        if "LastEvaluatedKey" not in response:
            break
        kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
    return items


def _write_items(table, items: List[dict]) -> None:
    with table.batch_writer() as batch:
        for item in items:
            batch.put_item(Item=item)


def _sleep_backoff(attempt: int) -> None:
    time.sleep(min(1 + attempt * 0.5, 5))


def migrate_table(src_table, dst_table, limit: int | None, dry_run: bool) -> int:
    items = _scan_all(src_table, limit)
    if dry_run:
        return len(items)
    _write_items(dst_table, items)
    return len(items)


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate DynamoDB data from dev to prod.")
    parser.add_argument("--from", dest="from_env", default="dev", help="source env (default: dev)")
    parser.add_argument("--to", dest="to_env", default="prod", help="target env (default: prod)")
    parser.add_argument("--dry-run", action="store_true", help="scan only, do not write")
    parser.add_argument("--limit", type=int, default=None, help="limit items per table")
    parser.add_argument("--app-name", default=os.getenv("TF_VAR_app_name", "phishing-app"))
    args = parser.parse_args()

    region = os.getenv("AWS_DEFAULT_REGION") or os.getenv("AWS_REGION_NAME")
    if not region:
        print("ERROR: AWS_DEFAULT_REGION or AWS_REGION_NAME must be set.", file=sys.stderr)
        return 1

    dynamodb = boto3.resource("dynamodb", region_name=region)

    src_tables = _get_table_names(args.from_env, args.app_name, "DEV")
    dst_tables = _get_table_names(args.to_env, args.app_name, "PROD")

    print(f"Source env: {args.from_env} | Target env: {args.to_env} | Region: {region}")
    print(f"Dry run: {args.dry_run} | Limit: {args.limit or 'none'}")

    for key in TABLE_KEYS:
        src_name = src_tables[key]
        dst_name = dst_tables[key]
        print(f"\nMigrating table: {key}")
        print(f"  source: {src_name}")
        print(f"  target: {dst_name}")
        src_table = dynamodb.Table(src_name)
        dst_table = dynamodb.Table(dst_name)
        count = migrate_table(src_table, dst_table, args.limit, args.dry_run)
        print(f"  copied: {count} items")

    print("\nMigration complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
