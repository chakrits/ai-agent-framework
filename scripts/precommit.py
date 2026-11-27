#!/usr/bin/env python3
"""Cross-platform wrapper: python scripts/precommit.py (Windows: py -3 scripts\\precommit.py)."""

# Import isolation (PLAN-011): keep this file's directory off sys.path so that files placed next to it are
# never imported by name. Nothing above this block may import a module that is not already loaded at startup.
import os
import sys

_HERE = os.path.dirname(os.path.realpath(__file__))
sys.path[:] = [p for p in sys.path if os.path.normcase(os.path.realpath(p or os.curdir)) != os.path.normcase(_HERE)]

import importlib.util  # noqa: E402


def _load(name: str, path: str) -> None:
    """Load one module by path, compiled from source so a stale or planted bytecode cache is never used."""
    if name not in sys.modules:
        module = importlib.util.module_from_spec(importlib.util.spec_from_file_location(name, path))
        sys.modules[name] = module
        with open(path, "rb") as fh:
            exec(compile(fh.read(), path, "exec"), module.__dict__)


_load("sdlc_hook", os.path.join(_HERE, "sdlc_hook.py"))


from sdlc_hook import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(["precommit", *sys.argv[1:]]))
