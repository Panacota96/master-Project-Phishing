#!/usr/bin/env python3
"""Migrate legacy inspector attempts into anonymous table (GDPR-safe)."""

from __future__ import annotations

import argparse
import os
from datetime import datetime, timezone
from uuid import uuid4

import boto3


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def scan_all(table):
    items = []
    kwargs = {}
    while True:
        resp = table.scan(**kwargs)
        items.extend(resp.get('Items', []))
        last_key = resp.get('LastEvaluatedKey')
        if not last_key:
            break
        kwargs['ExclusiveStartKey'] = last_key
    return items


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='Do not write, only count')
    parser.add_argument('--limit', type=int, default=0, help='Limit number of items to migrate')
    args = parser.parse_args()

    region = os.environ.get('AWS_REGION_NAME', 'eu-west-3')
    source_name = os.environ.get('DYNAMODB_INSPECTOR')
    target_name = os.environ.get('DYNAMODB_INSPECTOR_ANON')

    if not source_name or not target_name:
        raise SystemExit('DYNAMODB_INSPECTOR and DYNAMODB_INSPECTOR_ANON must be set.')

    dynamodb = boto3.resource('dynamodb', region_name=region)
    source = dynamodb.Table(source_name)
    target = dynamodb.Table(target_name)

    items = scan_all(source)
    if args.limit:
        items = items[: args.limit]

    migrated = 0
    for item in items:
        anon = {
            'attempt_id': str(uuid4()),
            'submitted_at': item.get('submitted_at') or now_iso(),
            'email_file': item.get('email_file', 'unknown'),
            'classification': item.get('classification'),
            'selected_signals': item.get('selected_signals', []),
            'expected_classification': item.get('expected_classification'),
            'expected_signals': item.get('expected_signals', []),
            'is_correct': item.get('is_correct', False),
            'class_name': item.get('class_name', 'unknown'),
            'academic_year': item.get('academic_year', 'unknown'),
            'major': item.get('major', 'unknown'),
        }

        if not args.dry_run:
            target.put_item(Item=anon)
        migrated += 1

    mode = 'DRY RUN' if args.dry_run else 'WRITE'
    print(f'{mode}: migrated {migrated} inspector attempts')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
