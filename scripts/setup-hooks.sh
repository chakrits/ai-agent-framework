#!/bin/sh
# DEPRECATED compatibility wrapper. Cross-platform setup: python scripts/setup.py (Windows: py -3 scripts\setup.py)
exec sh "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/bin/sdlc-hook" setup "$@"
