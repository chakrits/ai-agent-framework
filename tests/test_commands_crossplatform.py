"""Shell command analysis tests for bash (POSIX), PowerShell and cmd."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from sdlc_guard import commands  # noqa: E402


class TestFamilyDetection(unittest.TestCase):
    def test_tool_name(self) -> None:
        self.assertEqual(commands.detect_family("PowerShell", "Get-Item x", windows_host=True)[0], "powershell")
        self.assertEqual(commands.detect_family("Bash", "ls", windows_host=False)[0], "posix")

    def test_unwrap_powershell_wrapper(self) -> None:
        family, inner = commands.detect_family(
            "Bash", 'powershell.exe -NoProfile -Command "Get-Content .env"', windows_host=True
        )
        self.assertEqual(family, "powershell")
        self.assertEqual(inner, "Get-Content .env")

    def test_unwrap_bash_lc(self) -> None:
        family, inner = commands.detect_family("Bash", "bash -lc 'git push -f'", windows_host=False)
        self.assertEqual((family, inner), ("posix", "git push -f"))

    def test_unwrap_cmd_c(self) -> None:
        family, inner = commands.detect_family("Bash", 'cmd /c "type .env"', windows_host=True)
        self.assertEqual((family, inner), ("cmd", "type .env"))


class TestAnalyze(unittest.TestCase):
    def test_segments_split_on_operators(self) -> None:
        facts = commands.analyze("git status && git push --force; echo ok", "posix")
        self.assertEqual(len(facts.segments), 3)

    def test_windows_backslashes_preserved_in_powershell(self) -> None:
        facts = commands.analyze(r"Get-Content C:\repo\.env", "powershell")
        self.assertIn(r"C:\repo\.env", facts.path_tokens)

    def test_redirect_targets_posix(self) -> None:
        facts = commands.analyze("echo x >> docs/operating-model/constitution.md", "posix")
        self.assertIn("docs/operating-model/constitution.md", facts.write_targets)

    def test_redirect_attached(self) -> None:
        facts = commands.analyze("echo x >docs/a.md 2>err.log", "posix")
        self.assertIn("docs/a.md", facts.write_targets)

    def test_powershell_write_cmdlets(self) -> None:
        facts = commands.analyze(r"Set-Content -Path docs\contracts\x.yaml -Value 1", "powershell")
        self.assertIn(r"docs\contracts\x.yaml", facts.write_targets)
        facts = commands.analyze(r"'x' | Out-File tests\test_a.py", "powershell")
        self.assertIn(r"tests\test_a.py", facts.write_targets)

    def test_cmd_write_commands(self) -> None:
        facts = commands.analyze(r"del /q tests\test_a.py", "cmd")
        self.assertIn(r"tests\test_a.py", facts.write_targets)

    def test_cp_destination_only(self) -> None:
        facts = commands.analyze("cp docs/operating-model/constitution.md /tmp/c.md", "posix")
        self.assertEqual(facts.write_targets, {"/tmp/c.md"})

    def test_sed_in_place(self) -> None:
        facts = commands.analyze("sed -i 's/a/b/' tests/test_a.py", "posix")
        self.assertIn("tests/test_a.py", facts.write_targets)

    def test_flag_value_tokens(self) -> None:
        facts = commands.analyze("tool --env-file=.env run", "posix")
        self.assertIn(".env", facts.path_tokens)


class TestRules(unittest.TestCase):
    def check(self, cmd: str, family: str = "posix", env: dict | None = None) -> list[str]:
        return commands.dangerous_command_reasons(commands.analyze(cmd, family), env or {}, allow_force_with_lease=False)

    def test_force_push_variants(self) -> None:
        for cmd in ("git push -f origin main", "git push --force", "git push origin +main", "git push -uf origin x"):
            self.assertTrue(self.check(cmd), cmd)
        self.assertFalse(self.check("git push origin main"))

    def test_force_with_lease_configurable(self) -> None:
        facts = commands.analyze("git push --force-with-lease", "posix")
        self.assertTrue(commands.dangerous_command_reasons(facts, {}, allow_force_with_lease=False))
        self.assertFalse(commands.dangerous_command_reasons(facts, {}, allow_force_with_lease=True))

    def test_no_verify(self) -> None:
        self.assertTrue(self.check("git commit --no-verify -m x"))
        self.assertTrue(self.check("git commit -n -m x"))

    def test_hooks_path_tampering(self) -> None:
        self.assertTrue(self.check("git config core.hooksPath /dev/null"))
        self.assertTrue(self.check("git config --unset core.hooksPath"))
        self.assertFalse(self.check("git config --get core.hooksPath"))

    def test_production_deploy_requires_approval(self) -> None:
        self.assertTrue(self.check("./deploy.sh production"))
        self.assertTrue(self.check("make deploy ENV=prod"))
        self.assertFalse(self.check("./deploy.sh production", env={"RELEASE_APPROVAL": "REL-1"}))

    def test_inline_override_assignment_is_blocked(self) -> None:
        self.assertTrue(self.check("RELEASE_APPROVAL=1 ./deploy.sh production", env={}))
        self.assertTrue(self.check("SDLC_ALLOW_PROTECTED=1 git commit -m x"))
        self.assertTrue(self.check("$env:SDLC_GUARD_FAIL_OPEN='1'; git status", family="powershell"))
        self.assertTrue(self.check("set SDLC_ALLOW_PROTECTED=1", family="cmd"))

    def test_assignment_text_in_data_is_not_an_override(self) -> None:
        for cmd in (
            'echo "RELEASE_APPROVAL=1"',
            "grep -rn SDLC_ALLOW_PROTECTED=1 docs",
            "cat > notes.md <<'EOF'\nSDLC_ALLOW_PROTECTED=1 git commit\nRELEASE_APPROVAL=1 ./go\nEOF",
            "python3 - <<EOF\nprint('SDLC_GUARD_FAIL_OPEN=1')\nEOF",
        ):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.check(cmd), [])

    def test_assignment_forms_that_take_effect_are_blocked(self) -> None:
        for cmd in (
            "export RELEASE_APPROVAL=1",
            "env SDLC_ALLOW_PROTECTED=1 git commit -m x",
            "FOO=1 SDLC_ALLOW_PROTECTED=1 git commit -m x",
            'bash -c "SDLC_ALLOW_PROTECTED=1 git commit -m x"',
            "bash <<EOF\nSDLC_ALLOW_PROTECTED=1 git commit -m x\nEOF",
            "git status && SDLC_GUARD_FAIL_OPEN=1 ./run",
        ):
            with self.subTest(cmd=cmd):
                facts = commands.analyze(commands.detect_family("Bash", cmd, windows_host=False)[1], "posix")
                self.assertTrue(commands.dangerous_command_reasons(facts, {}, allow_force_with_lease=False), cmd)

    def test_shell_heredoc_commands_are_still_analysed(self) -> None:
        for cmd in (
            "sh <<'EOF'\ngit push --force\nEOF",
            "cat <<'EOF' | bash\ngit push --force\nEOF",
            "cat <<EOF | sudo /bin/sh\ngit push -f\nEOF",
            "cat <<EOF | xargs bash -c\ngit push -f\nEOF",
            "FOO=1 bash <<EOF\ngit push -f\nEOF",
            "echo go; sh <<EOF\ngit push -f\nEOF",
        ):
            with self.subTest(cmd=cmd):
                self.assertTrue(self.check(cmd), cmd)

    def test_data_heredocs_are_not_analysed(self) -> None:
        for cmd in (
            "cat > run.sh <<'EOF'\ngit push --force\nEOF",
            "tee notes.md <<EOF\ngit push -f\nEOF",
            "python3 - <<'PY'\nprint('git push --force')\nPY",
        ):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.check(cmd), [], cmd)

    def test_powershell_force_push(self) -> None:
        self.assertTrue(self.check("git push --force origin main", family="powershell"))


if __name__ == "__main__":
    unittest.main()
