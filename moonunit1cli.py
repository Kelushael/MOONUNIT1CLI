#!/usr/bin/env python3
"""
moonunit1cli.py
MOONUNIT1 — Sovereign AI Agent
Type the alias. It boots. You're in. That's it.
"""

import sys
import os
from pathlib import Path

AGENT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(AGENT_DIR))

import chat
import serve
import config
from agent import Agent


# ============================================================
# Boot sequence
# ============================================================

def boot():
    """Start everything. Local server first. Remote check second. Then ready."""

    chat.blank()
    chat.box([
        "  MOONUNIT1  ",
        "  Sovereign Agent  ",
    ], color_code=chat.NEON_ORANGE)
    chat.blank()

    # 1. Local model server
    existing = serve.find_existing_server(
        port=config.get("model.port", 8181),
        host=config.get("model.host", "127.0.0.1")
    )

    if existing:
        chat.status_dot("Local model server", ok=True)
    else:
        chat.system_msg("Starting local model server...")
        server = serve.ModelServer()
        ok = server.start(quiet=False)
        if not ok:
            chat.warning("  Local server unavailable. Will try remote.")

    # 2. Remote check
    import requests
    remote_url = config.get("remote.url", "https://axismundi.fun/v1/chat/completions")
    try:
        r = requests.get(remote_url.replace("/v1/chat/completions", "/health"), timeout=5)
        remote_ok = r.status_code == 200
    except Exception:
        remote_ok = False

    chat.status_dot(f"Remote ({remote_url.split('/')[2]})", ok=remote_ok)
    chat.blank()

    return remote_ok


# ============================================================
# Interactive chat loop
# ============================================================

def chat_loop(agent):
    """Main interactive loop. Clean. Direct."""

    chat.out(chat.muted("  /help  /status  /ssh  /remote  /release  /exit"))
    chat.blank()

    while True:
        try:
            user_input = chat.prompt_input("you > ")
        except (EOFError, KeyboardInterrupt):
            chat.blank()
            chat.system_msg("Goodbye.")
            break

        if user_input is None:
            break

        user_input = user_input.strip()
        if not user_input:
            continue

        # Built-in slash commands
        if user_input.lower() in ("/exit", "/quit", "exit", "quit"):
            chat.system_msg("Goodbye.")
            break

        elif user_input.lower() == "/help":
            chat.blank()
            chat.out(chat.orange("  Commands"))
            chat.bullet("/status     — agent + server status")
            chat.bullet("/ssh        — connect to remote server")
            chat.bullet("/remote     — switch to remote inference")
            chat.bullet("/local      — switch to local inference")
            chat.bullet("/release    — publish tested artifact to release hub")
            chat.bullet("/exit       — exit")
            chat.blank()
            chat.out(chat.muted("  Everything else goes straight to the agent."))
            chat.blank()
            continue

        elif user_input.lower() == "/status":
            _show_status(agent)
            continue

        elif user_input.lower().startswith("/ssh"):
            rest = user_input[4:].strip()
            if rest:
                user_input = f"SSH connect to {rest}"
            else:
                user_input = "Connect to the remote server via SSH. You know the domain and the user."

        elif user_input.lower() == "/remote":
            config.set_value("agent.use_remote", True, source="cli")
            chat.out(chat.success("  Switched to remote inference"))
            continue

        elif user_input.lower() == "/local":
            config.set_value("agent.use_remote", False, source="cli")
            chat.out(chat.success("  Switched to local inference"))
            continue

        elif user_input.lower().startswith("/release"):
            rest = user_input[8:].strip()
            user_input = f"Run tests on {rest if rest else 'the current project'}. If all tests pass, publish it to the release hub at markyninox.com. Do not publish if any test fails."

        # Send to agent
        chat.blank()
        response = agent.send(user_input)
        if response:
            chat.blank()
            chat.agent_msg(response)
        chat.blank()


# ============================================================
# Status display
# ============================================================

def _show_status(agent):
    chat.blank()
    chat.header("Status")

    # Server
    server = serve.ModelServer()
    status = server.get_status()
    chat.label("Local server", "running" if status["healthy"] else "down",
               val_color=chat.NEON_GREEN if status["healthy"] else chat.BRIGHT_RED)
    chat.label("Port", str(status["port"]))

    # Remote
    remote_url = config.get("remote.url", "https://axismundi.fun/v1/chat/completions")
    use_remote = config.get("agent.use_remote", False)
    chat.label("Remote", remote_url.split("/")[2])
    chat.label("Using remote", str(use_remote))

    # Memory
    import memory as mem
    mc = mem.count()
    chat.label("Memories", str(mc))

    # Context
    import context_engine
    ctx = context_engine.get_active_context()
    chat.label("Active context", f"{ctx['count']} chunks ({ctx['pressure']:.0%} pressure)")

    # Dynamic tools
    import tool_registry
    tools = tool_registry.list_dynamic_tools()
    chat.label("Dynamic tools", str(len(tools)))

    chat.blank()


# ============================================================
# Entry point
# ============================================================

def main():
    # Boot
    boot()

    # Start agent
    agent = Agent()

    # Chat
    chat_loop(agent)


if __name__ == "__main__":
    main()
