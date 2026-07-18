#!/usr/bin/env python3
"""Configure Vocal Bridge agent for the trip planner."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VOCAL_DIR = ROOT / "vocal-bridge"


def load_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip("'\"")
        os.environ.setdefault(key, value)

    if not os.environ.get("VOCAL_BRIDGE_API_KEY") and os.environ.get("VOCAL_BRIDE_API_KEY"):
        os.environ["VOCAL_BRIDGE_API_KEY"] = os.environ["VOCAL_BRIDE_API_KEY"]


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    print(f"$ {' '.join(args)}")
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True)


def main() -> int:
    load_env()
    api_key = os.environ.get("VOCAL_BRIDGE_API_KEY", "")
    if not api_key:
        print("Missing VOCAL_BRIDGE_API_KEY in .env")
        return 1

    auth = run([sys.executable, "-m", "vocal_bridge", "auth", "login", api_key])
    if auth.returncode != 0:
        auth = run(["vb", "auth", "login", api_key])
    if auth.returncode != 0:
        print(auth.stderr or auth.stdout)
        print("Install the CLI with: pip install vocal-bridge")
        return auth.returncode

    agents = run(["vb", "agent", "list"])
    if agents.returncode != 0:
        print(agents.stderr or agents.stdout)
        return agents.returncode

    if "Trip Planner" not in (agents.stdout or ""):
        created = run(
            [
                "vb",
                "agent",
                "create",
                "--name",
                "Trip Planner",
                "--style",
                "Chatty",
                "--prompt-file",
                str(prompt_file),
                "--greeting",
                "Hi! I'm Roam, your weekend trip planner. Where are you flying from, and what's your budget?",
                "--deploy-targets",
                "web",
                "--background-enabled",
                "false",
                "--client-actions-file",
                str(actions_file),
                "--ai-agent-file",
                str(ai_agent_file),
                "--json",
            ]
        )
        if created.returncode != 0:
            print(created.stderr or created.stdout)
            return created.returncode
        print(created.stdout)

        use = run(["vb", "agent", "use", "--name", "Trip Planner"])
        if use.returncode != 0:
            use = run(["vb", "agent", "use"])
        if use.returncode != 0:
            print(use.stderr or use.stdout)

    prompt_file = VOCAL_DIR / "agent_prompt.txt"
    actions_file = VOCAL_DIR / "client_actions.json"
    ai_agent_file = VOCAL_DIR / "ai_agent.json"

    for cmd in [
        ["vb", "prompt", "set", "--file", str(prompt_file)],
        ["vb", "config", "set", "--client-actions-file", str(actions_file)],
        ["vb", "config", "set", "--ai-agent-file", str(ai_agent_file)],
        ["vb", "config", "set", "--ai-agent-enabled", "true"],
    ]:
        result = run(cmd)
        if result.returncode != 0:
            print(result.stderr or result.stdout)
            return result.returncode

    info = run(["vb", "agent"])
    print(info.stdout or "Agent configured.")
    print("\nIf you use an account-level API key, copy the agent ID into VOCAL_BRIDGE_AGENT_ID in .env")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
