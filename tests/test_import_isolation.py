"""Entry points must not import code that merely sits next to them in the working tree, and the hook must fail
closed when the guard cannot be loaded (PLAN-011).

Every case runs inside a throwaway copy of the repository. Nothing is ever planted in the real tree.
"""

from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRY_DIRS = ("scripts", "evals")
MARKER = "PLANTED-MODULE-RAN"
BODY = f'import sys\nsys.stderr.write("{MARKER}\\n")\nsys.exit(0)\n'
# A module the running OS does not ship, which parts of the standard library still try to import.
ABSENT_HERE = "pwd" if os.name == "nt" else "msvcrt"
PLANTS = ("json.py", "json/", "__future__.py", f"{ABSENT_HERE}.py")
PROTECTED_FILE = "docs/contracts/tasks.schema.json"
DROP_ENV = {
    "SDLC_ACTIVE_ROLE", "SDLC_ALLOW_PROTECTED", "SDLC_GUARD_FAIL_OPEN", "SDLC_REPO_ROOT", "RELEASE_APPROVAL",
    "CLAUDE_PROJECT_DIR", "PYTHONPATH", "PYTHONSAFEPATH", "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE",
}


def entry_scripts() -> list[Path]:
    found = []
    for directory in ENTRY_DIRS:
        for path in sorted((ROOT / directory).glob("*.py")):
            if '__name__ == "__main__"' in path.read_text(encoding="utf-8"):
                found.append(path)
    return found


class TestEntryScriptStructure(unittest.TestCase):
    """Static guard so a new or edited entry script cannot silently drop the isolation block."""

    def test_isolation_block_comes_before_every_other_import(self) -> None:
        scripts = entry_scripts()
        self.assertGreaterEqual(len(scripts), 10)
        for path in scripts:
            with self.subTest(script=path.relative_to(ROOT).as_posix()):
                source = path.read_text(encoding="utf-8")
                body = ast.parse(source).body
                if isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                    body = body[1:]
                head = [ast.unparse(node) for node in body[:4]]
                self.assertEqual(head[:2], ["import os", "import sys"])
                self.assertTrue(head[2].startswith("_HERE = os.path.dirname(os.path.realpath(__file__))"), head[2])
                self.assertTrue(head[3].startswith("sys.path[:] = [p for p in sys.path if os.path.normcase("), head[3])
                for forbidden in ("from __future__", "sys.path.insert", "sys.path.append"):
                    self.assertNotIn(forbidden, source)


class TestPlantedModules(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        base = Path(cls._tmp.name)
        cls.repo = base / "repo"
        listed = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            capture_output=True, check=True,
        ).stdout.decode("utf-8")
        for rel in filter(None, listed.split("\0")):
            source = ROOT / rel
            if source.is_file():
                target = cls.repo / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)

        empty_config = base / "gitconfig"
        empty_config.write_text("", encoding="utf-8")
        cls.env = {k: v for k, v in os.environ.items() if k not in DROP_ENV}
        cls.env.update(
            SDLC_TRACE_DIR=str(base / "traces"), SDLC_TRACE_LEVEL="off",
            GIT_CONFIG_GLOBAL=str(empty_config), GIT_CONFIG_NOSYSTEM="1",
            GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.test",
            GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.test",
        )
        for args in (("init", "-q"), ("add", "-A"), ("commit", "-qm", "chore: baseline")):
            subprocess.run(["git", "-C", str(cls.repo), *args], env=cls.env, capture_output=True, check=True)
        with open(cls.repo / PROTECTED_FILE, "a", encoding="utf-8", newline="\n") as fh:
            fh.write("\n")
        subprocess.run(["git", "-C", str(cls.repo), "add", PROTECTED_FILE], env=cls.env, capture_output=True, check=True)
        (cls.repo / "bad-tasks.json").write_text("{not json", encoding="utf-8")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def run_in_copy(self, command: list[str], stdin: str = "") -> subprocess.CompletedProcess:
        return subprocess.run(
            command, cwd=self.repo, env=self.env, input=stdin, capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=180, check=False,
        )

    def script(self, rel: str, *args: str, stdin: str = "") -> subprocess.CompletedProcess:
        # Deliberately without -I: CI and users call the entry scripts this way.
        return self.run_in_copy([sys.executable, rel, *args], stdin)

    def launcher(self, *args: str, stdin: str = "") -> subprocess.CompletedProcess:
        if os.name == "nt":
            return self.run_in_copy(["cmd", "/c", "scripts\\bin\\sdlc-hook.cmd", *args], stdin)
        return self.run_in_copy(["sh", "scripts/bin/sdlc-hook", *args], stdin)

    def assert_clean(self, result: subprocess.CompletedProcess) -> str:
        output = result.stdout + result.stderr
        self.assertNotIn(MARKER, output)
        return output

    def check_all_entry_points(self) -> None:
        payload = json.dumps({
            "tool_name": "Write", "agent_type": "dev-coding-agent", "cwd": str(self.repo),
            "tool_input": {"file_path": str(self.repo / PROTECTED_FILE), "content": "x"},
        })
        for name, result in (
            ("entry hook", self.script("scripts/sdlc_hook.py", "pretooluse", stdin=payload)),
            ("launcher hook", self.launcher("pretooluse", stdin=payload)),
        ):
            with self.subTest(check=name):
                self.assert_clean(result)
                self.assertEqual(result.returncode, 2, result.stderr)

        for name, result in (
            ("pre-commit launcher", self.launcher("precommit")),
            ("pre-commit wrapper", self.script("scripts/precommit.py")),
        ):
            with self.subTest(check=name):
                output = self.assert_clean(result)
                self.assertEqual(result.returncode, 1, output)
                self.assertIn("Protected governance path staged", output)

        expected = (
            (0, "scripts/validate-contracts.py", "--check-defaults"),
            (1, "scripts/validate-contracts.py", "--tasks", "bad-tasks.json"),
            (0, "scripts/validate_work_item.py", "work/INT-001"),
            (1, "scripts/validate_work_item.py", "no-such-dir"),
            (0, "scripts/validate-context-budget.py"),
            (0, "scripts/sync-adapters.py", "--check"),
            (0, "scripts/doctor.py"),
            (0, "scripts/sdlc_trace.py", "config", "show"),
            (64, "scripts/sdlc_hook.py", "no-such-command"),
            (0, "scripts/setup.py"),
            (0, "evals/run_evals.py", "--mode", "contract"),
        )
        for code, *command in expected:
            with self.subTest(check=" ".join(command)):
                result = self.script(*command)
                output = self.assert_clean(result)
                self.assertEqual(result.returncode, code, output)

    def test_without_planted_files(self) -> None:
        self.check_all_entry_points()

    def test_planted_files_are_never_imported(self) -> None:
        for plant in PLANTS:
            created = []
            for directory in ENTRY_DIRS:
                target = self.repo / directory / plant.rstrip("/")
                if plant.endswith("/"):
                    target.mkdir()
                    (target / "__init__.py").write_text(BODY, encoding="utf-8")
                else:
                    target.write_text(BODY, encoding="utf-8")
                created.append(target)
            try:
                with self.subTest(plant=plant):
                    self.check_all_entry_points()
            finally:
                for target in created:
                    shutil.rmtree(target) if target.is_dir() else target.unlink()

    def test_unchecked_bytecode_cache_is_ignored_for_single_file_modules(self) -> None:
        compile_cmd = (
            "import py_compile, sys; py_compile.compile(sys.argv[1], doraise=True, "
            "invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH)"
        )
        cases = (
            ("scripts/qa_report.py", ("scripts/validate_work_item.py", "no-such-dir"), 1),
            ("scripts/sdlc_hook.py", ("scripts/doctor.py",), 0),
            ("scripts/validate-contracts.py", ("evals/run_evals.py", "--mode", "contract"), 0),
        )
        for module, command, code in cases:
            with self.subTest(module=module):
                source = self.repo / module
                original = source.read_bytes()
                cache = source.parent / "__pycache__"
                try:
                    source.write_text(BODY, encoding="utf-8")
                    subprocess.run([sys.executable, "-I", "-c", compile_cmd, str(source)], env=self.env, check=True)
                    source.write_bytes(original)
                    result = self.script(*command)
                    output = self.assert_clean(result)
                    self.assertEqual(result.returncode, code, output)
                finally:
                    source.write_bytes(original)
                    shutil.rmtree(cache, ignore_errors=True)

    def run_hook(self, args: tuple[str, ...], env: dict | None = None) -> list[tuple[str, subprocess.CompletedProcess]]:
        payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "echo hi"}, "cwd": str(self.repo)})
        saved = self.env
        self.env = {**saved, **(env or {})}
        try:
            return [
                ("entry", self.script("scripts/sdlc_hook.py", *args, stdin=payload)),
                ("launcher", self.launcher(*args, stdin=payload)),
            ]
        finally:
            self.env = saved

    def test_hook_fails_closed_when_guard_cannot_be_loaded(self) -> None:
        guard_file = self.repo / "scripts" / "sdlc_guard" / "guard.py"
        original = guard_file.read_bytes()
        anchor = b"from __future__ import annotations\n"
        broken = {
            "syntax error": original + b"def (:\n",
            "runtime error": original.replace(anchor, anchor + b"raise RuntimeError('broken guard')\n", 1),
            "exits during import": original.replace(anchor, anchor + b"raise SystemExit(0)\n", 1),
        }
        blocking = (
            ("pretooluse",), ("hook",), (), ("--check-cmd", "git status"), ("--check-path", "README.md"),
            ("precommit",), ("commit-msg", "bad-tasks.json"),
        )
        try:
            for label, content in broken.items():
                self.assertNotEqual(content, original)
                guard_file.write_bytes(content)
                for args in blocking:
                    for via, result in self.run_hook(args):
                        with self.subTest(failure=label, args=args, via=via):
                            self.assertEqual(result.returncode, 2, result.stderr)
                            self.assertIn("BLOCKED: sdlc guard could not be loaded", result.stderr)
                for via, result in self.run_hook(("pretooluse", "--platform", "antigravity")):
                    with self.subTest(failure=label, platform="antigravity", via=via):
                        self.assertEqual(result.returncode, 0, result.stderr)
                        self.assertEqual(json.loads(result.stdout)["decision"], "deny")
                for sub_command in ("trace", "session-start"):
                    for platform, stdout in (("claude", ""), ("antigravity", "{}")):
                        for via, result in self.run_hook((sub_command, "--platform", platform)):
                            with self.subTest(failure=label, command=sub_command, platform=platform, via=via):
                                self.assertEqual(result.returncode, 0, result.stderr)
                                self.assertEqual(result.stdout.strip(), stdout)
        finally:
            guard_file.write_bytes(original)

    def test_human_fail_open_override_applies_to_tool_hooks_only(self) -> None:
        guard_file = self.repo / "scripts" / "sdlc_guard" / "guard.py"
        original = guard_file.read_bytes()
        override = {"SDLC_GUARD_FAIL_OPEN": "1"}
        try:
            guard_file.write_bytes(original + b"def (:\n")
            for via, result in self.run_hook(("pretooluse",), override):
                with self.subTest(command="pretooluse", via=via):
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn("WARNING", result.stderr)
            for via, result in self.run_hook(("pretooluse", "--platform", "antigravity"), override):
                with self.subTest(platform="antigravity", via=via):
                    self.assertEqual(json.loads(result.stdout)["decision"], "allow")
            for via, result in self.run_hook(("precommit",), override):
                with self.subTest(command="precommit", via=via):
                    self.assertEqual(result.returncode, 2, result.stderr)
        finally:
            guard_file.write_bytes(original)


if __name__ == "__main__":
    unittest.main()
