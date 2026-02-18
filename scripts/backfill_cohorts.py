#!/usr/bin/env python3
"""Backfill cohort fields (class_name, academic_year, major) for users and attempts.

Supports optional CSV mapping to set cohorts by username and/or email.
CSV columns (recommended): username,email,class,academic_year,major
"""

import argparse
import csv
from typing import Dict

from app import create_app
from app.models import get_user


DEFAULT_CLASS = "unknown"
DEFAULT_YEAR = "unknown"
DEFAULT_MAJOR = "unknown"


def scan_all(table):
    items = []
    response = table.scan()
    items.extend(response.get("Items", []))
    while response.get("LastEvaluatedKey"):
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        items.extend(response.get("Items", []))
    return items


def normalize(value, fallback):
    if value is None:
        return fallback
    if isinstance(value, str) and value.strip() == "":
        return fallback
    return value


def load_mapping(path):
    if not path:
        return {}, {}
    by_username = {}
    by_email = {}
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"class", "academic_year", "major"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("CSV must include class, academic_year, major columns")
        for row in reader:
            class_name = normalize(row.get("class"), DEFAULT_CLASS)
            academic_year = normalize(row.get("academic_year"), DEFAULT_YEAR)
            major = normalize(row.get("major"), DEFAULT_MAJOR)
            entry = {
                "class_name": class_name,
                "academic_year": academic_year,
                "major": major,
            }
            username = (row.get("username") or "").strip()
            email = (row.get("email") or "").strip()
            if username:
                by_username[username] = entry
            if email:
                by_email[email] = entry
    return by_username, by_email


def resolve_cohort(user, defaults, by_username, by_email):
    if user:
        if user.username in by_username:
            return by_username[user.username]
        if user.email in by_email:
            return by_email[user.email]
        return {
            "class_name": normalize(getattr(user, "class_name", None), defaults["class_name"]),
            "academic_year": normalize(getattr(user, "academic_year", None), defaults["academic_year"]),
            "major": normalize(getattr(user, "major", None), defaults["major"]),
        }
    return defaults


def backfill_users(table, defaults, by_username, by_email, apply):
    updated = 0
    users = scan_all(table)
    for user in users:
        mapped = None
        if user.get("username") in by_username:
            mapped = by_username[user["username"]]
        elif user.get("email") in by_email:
            mapped = by_email[user["email"]]

        class_name = normalize(user.get("class_name"), defaults["class_name"])
        academic_year = normalize(user.get("academic_year"), defaults["academic_year"])
        major = normalize(user.get("major"), defaults["major"])

        if mapped:
            class_name = mapped["class_name"]
            academic_year = mapped["academic_year"]
            major = mapped["major"]

        needs_update = (
            user.get("class_name") != class_name
            or user.get("academic_year") != academic_year
            or user.get("major") != major
        )
        if not needs_update:
            continue

        updated += 1
        if apply:
            table.update_item(
                Key={"username": user["username"]},
                UpdateExpression="SET class_name = :c, academic_year = :y, major = :m",
                ExpressionAttributeValues={
                    ":c": class_name,
                    ":y": academic_year,
                    ":m": major,
                },
            )
    return updated


def backfill_attempts(table, defaults, by_username, by_email, apply):
    updated = 0
    attempts = scan_all(table)
    for attempt in attempts:
        if attempt.get("class_name") and attempt.get("academic_year") and attempt.get("major"):
            continue

        user = get_user(attempt["username"])
        cohort = resolve_cohort(user, defaults, by_username, by_email)

        updated += 1
        if apply:
            table.update_item(
                Key={"username": attempt["username"], "quiz_id": attempt["quiz_id"]},
                UpdateExpression="SET class_name = :c, academic_year = :y, major = :m",
                ExpressionAttributeValues={
                    ":c": cohort["class_name"],
                    ":y": cohort["academic_year"],
                    ":m": cohort["major"],
                },
            )
    return updated


def backfill_inspector_attempts(table, defaults, by_username, by_email, apply):
    updated = 0
    attempts = scan_all(table)
    for attempt in attempts:
        if attempt.get("class_name") and attempt.get("academic_year") and attempt.get("major"):
            continue

        user = get_user(attempt["username"])
        cohort = resolve_cohort(user, defaults, by_username, by_email)

        updated += 1
        if apply:
            table.update_item(
                Key={"username": attempt["username"], "submitted_at": attempt["submitted_at"]},
                UpdateExpression="SET class_name = :c, academic_year = :y, major = :m",
                ExpressionAttributeValues={
                    ":c": cohort["class_name"],
                    ":y": cohort["academic_year"],
                    ":m": cohort["major"],
                },
            )
    return updated


def main():
    parser = argparse.ArgumentParser(description="Backfill cohort fields in DynamoDB tables.")
    parser.add_argument("--apply", action="store_true", help="Apply updates (default is dry-run).")
    parser.add_argument("--default-class", default=DEFAULT_CLASS)
    parser.add_argument("--default-year", default=DEFAULT_YEAR)
    parser.add_argument("--default-major", default=DEFAULT_MAJOR)
    parser.add_argument("--mapping-csv", help="CSV with columns: username,email,class,academic_year,major")
    args = parser.parse_args()

    defaults = {
        "class_name": args.default_class,
        "academic_year": args.default_year,
        "major": args.default_major,
    }

    by_username, by_email = load_mapping(args.mapping_csv)

    app = create_app()
    with app.app_context():
        users_table = app.dynamodb.Table(app.config["DYNAMODB_USERS"])
        attempts_table = app.dynamodb.Table(app.config["DYNAMODB_ATTEMPTS"])
        inspector_table = app.dynamodb.Table(app.config["DYNAMODB_INSPECTOR"])

        users_updated = backfill_users(users_table, defaults, by_username, by_email, args.apply)
        attempts_updated = backfill_attempts(attempts_table, defaults, by_username, by_email, args.apply)
        inspector_updated = backfill_inspector_attempts(inspector_table, defaults, by_username, by_email, args.apply)

    mode = "APPLIED" if args.apply else "DRY-RUN"
    print(f"[{mode}] Users updated: {users_updated}")
    print(f"[{mode}] Quiz attempts updated: {attempts_updated}")
    print(f"[{mode}] Inspector attempts updated: {inspector_updated}")


if __name__ == "__main__":
    main()
