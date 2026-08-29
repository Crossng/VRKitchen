from __future__ import annotations

import subprocess
import sys
import unittest
from importlib.util import module_from_spec, spec_from_file_location
from io import StringIO
from pathlib import Path
from unittest.mock import patch


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPOSITORY_ROOT / "tools" / "verify_delivery_readiness.py"
CLIENT_PATH = REPOSITORY_ROOT / "tools" / "unreal_bridge_client.py"


def load_bridge_client_module():
    spec = spec_from_file_location("unreal_bridge_client", CLIENT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load unreal_bridge_client.py")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DeliveryReadinessTests(unittest.TestCase):
    def test_code_only_mode_passes_without_full_project_assets(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--skip-full-project",
                "--code-repo-root",
                str(REPOSITORY_ROOT),
            ],
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("No tracked Content, Unreal binary assets, or package artifacts", result.stdout)

    def test_bridge_client_sends_environment_token(self) -> None:
        client = load_bridge_client_module()
        response = {"success": True, "output": "pong", "error": ""}

        with (
            patch.dict("os.environ", {"UNREAL_BRIDGE_TOKEN": "test-token"}),
            patch.object(sys, "argv", [str(CLIENT_PATH), "--port", "54321", "--ping"]),
            patch.object(client, "send_request", return_value=response) as send_request,
            patch("sys.stdout", new_callable=StringIO),
        ):
            client.main()

        payload = send_request.call_args.args[2]
        self.assertEqual(payload["token"], "test-token")


if __name__ == "__main__":
    unittest.main()
