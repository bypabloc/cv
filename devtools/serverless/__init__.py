"""Serverless CLI for the portfolio backend.

Manages the lifecycle of the serverless/ backend: build, deploy, local
execution (RIE / direct mode), CloudWatch logs, tests with pytest +
moto, SSM secrets setup, DNS verification for SES, and database
migration helpers for Neon PostgreSQL. devtools provisions every
resource with AWS CLI directly (no SAM, no CloudFormation).

Entry point: ``python devtools/run.py serverless <command> [flags...]``.
Aligns with the existing ``docker`` module pattern: positional subcommand
+ flag-based parameterization.
"""
