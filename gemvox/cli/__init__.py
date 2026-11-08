from .command_runner import (
    parse_cli_args,
    handle_speak,
    handle_dialogue,
    handle_voices,
    handle_design,
    handle_update,
)


def run_interactive_cli(*args, **kwargs):
    from .interactive_cli import run_interactive_cli as _run
    return _run(*args, **kwargs)


__all__ = [
    "run_interactive_cli",
    "parse_cli_args",
    "handle_speak",
    "handle_dialogue",
    "handle_voices",
    "handle_design",
    "handle_update",
]
