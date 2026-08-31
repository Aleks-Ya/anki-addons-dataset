#!/usr/bin/env bash
set -euo pipefail
uv lock --upgrade
uv sync
