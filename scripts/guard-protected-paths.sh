#!/bin/sh
# DEPRECATED compatibility wrapper (kept for one release). Use scripts/bin/sdlc-hook instead.
exec sh "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/bin/sdlc-hook" "$@"
