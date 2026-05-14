"""Serverless CLI for the AWS SAM backend.

Manages the lifecycle of the serverless/ stack: build, deploy, local
testing (sam local invoke / start-api), CloudWatch logs, tests with
pytest + moto, SSM secrets setup, DNS verification for SES, and database
migration helpers for Neon PostgreSQL.

Entry point: ``python devtools/run.py serverless <command> [flags...]``.
Aligns with the existing ``docker`` module pattern: positional subcommand
+ flag-based parameterization.
"""
