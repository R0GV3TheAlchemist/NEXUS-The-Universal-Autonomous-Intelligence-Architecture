from __future__ import annotations

import pytest
from unittest.mock import patch

from cli.main import main
from cli.context import CLIContext
from cli.render import Renderer
from core.fs.filesystem import GAIAFilesystem
from core.identity.gaian.registry import GAIANRegistry
from core.primordial.session import PrimordialSession


@pytest.fixture
def live_ctx(tmp_path):
    """A pre-booted CLIContext wired to a temp filesystem."""
    ctx = CLIContext(root=tmp_path / "gaia_cli_test", json_mode=True)
    ctx.boot()
    return ctx


class TestCLIBoot:
    def test_boot_idempotent(self, live_ctx):
        live_ctx.boot()  # second call should be no-op
        assert live_ctx.is_booted()

    def test_session_is_live(self, live_ctx):
        assert live_ctx.session.is_live

    def test_api_is_wired(self, live_ctx):
        assert live_ctx.api is not None


class TestCLIVersionCommand:
    def test_version_exits_zero(self, tmp_path, capsys):
        code = main(["--json", "version"])
        assert code == 0

    def test_version_has_os_version(self, tmp_path, capsys):
        main(["--json", "version"])
        out = capsys.readouterr().out
        import json
        data = json.loads(out)
        assert data["name"] == "GAIA"
        assert "os_version" in data


class TestCLIStatus:
    def test_status_ok(self, live_ctx):
        from cli.commands import cmd_status
        code = cmd_status(live_ctx)
        assert code == 0

    def test_status_payload_has_schumann(self, live_ctx, capsys):
        from cli.commands import cmd_status
        cmd_status(live_ctx)
        out = capsys.readouterr().out
        import json
        data = json.loads(out)
        assert data["payload"]["schumann_hz"] == 7.83


class TestCLISchumann:
    def test_schumann_confirmed(self, live_ctx, capsys):
        from cli.commands import cmd_schumann
        code = cmd_schumann(live_ctx)
        assert code == 0
        out = capsys.readouterr().out
        import json
        data = json.loads(out)
        assert data["payload"]["confirmed"] is True
        assert data["payload"]["frequency_hz"] == 7.83


class TestCLIGAIANBirth:
    ANSWERS = [
        "1990-08-05", "ocean", "rain", "dusk",
        "images and visions", "home",
    ]

    def _run_birth(self, live_ctx):
        """Simulate birth ceremony by answering all questions via stdin mock."""
        from cli.commands import cmd_gaian_birth
        with patch("builtins.input", side_effect=self.ANSWERS):
            code = cmd_gaian_birth(live_ctx)
        return code

    def test_birth_exits_zero(self, live_ctx):
        code = self._run_birth(live_ctx)
        assert code == 0

    def test_birth_registers_gaian(self, live_ctx):
        self._run_birth(live_ctx)
        assert len(live_ctx.session.registry.list_all()) >= 1

    def test_birth_creates_home(self, live_ctx):
        self._run_birth(live_ctx)
        gaians = live_ctx.session.registry.list_all()
        assert live_ctx.fs.home_exists(gaians[0].gaian_id)


class TestCLIGAIANList:
    def test_empty_list(self, live_ctx, capsys):
        from cli.commands import cmd_gaian_list
        code = cmd_gaian_list(live_ctx)
        assert code == 0

    def test_list_shows_born_gaian(self, live_ctx, capsys):
        from cli.commands import cmd_gaian_birth, cmd_gaian_list
        with patch("builtins.input",
                   side_effect=["1990-08-05", "ocean", "rain",
                                "dusk", "images and visions", "home"]):
            cmd_gaian_birth(live_ctx)
        capsys.readouterr()  # clear
        code = cmd_gaian_list(live_ctx)
        assert code == 0
        out = capsys.readouterr().out
        import json
        data = json.loads(out)
        assert data["payload"]["count"] >= 1


class TestCLITalk:
    def _born_gaian_id(self, live_ctx):
        from cli.commands import cmd_gaian_birth
        with patch("builtins.input",
                   side_effect=["1990-08-05", "ocean", "rain",
                                "dusk", "images and visions", "home"]):
            cmd_gaian_birth(live_ctx)
        return live_ctx.session.registry.list_all()[-1].gaian_id

    def test_talk_single_turn_then_exit(self, live_ctx, capsys):
        from cli.commands import cmd_talk
        gaian_id = self._born_gaian_id(live_ctx)
        # One message, then empty string to exit
        with patch.object(
            live_ctx.renderer, "talk_prompt",
            side_effect=["Hello!", ""]
        ):
            code = cmd_talk(live_ctx, gaian_id, human_id="cli-user")
        assert code == 0

    def test_talk_response_in_json(self, live_ctx, capsys):
        from cli.commands import cmd_talk
        gaian_id = self._born_gaian_id(live_ctx)
        with patch.object(
            live_ctx.renderer, "talk_prompt",
            side_effect=["What is your element?", ""]
        ):
            cmd_talk(live_ctx, gaian_id, human_id="cli-user")
        out = capsys.readouterr().out
        import json
        data = json.loads(out)
        assert "turns" in data
        assert len(data["turns"]) == 1


class TestCLIFilesystem:
    def test_fs_stats(self, live_ctx, capsys):
        from cli.commands import cmd_fs_stats
        code = cmd_fs_stats(live_ctx)
        assert code == 0

    def test_fs_integrity_clean(self, live_ctx, capsys):
        from cli.commands import cmd_fs_integrity
        code = cmd_fs_integrity(live_ctx)
        # No homes = all_clean by default
        assert code == 0
