"""Error handling utilities for CLI commands.

Provides centralized error formatting and reporting for consistent
user experience across all CLI commands.
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import NoReturn

import yaml

from ...parsers.errors import ConfigError, ConfigErrors


class Colors:
    """ANSI color codes for terminal output."""

    def __init__(self, enabled: bool = True):
        if not enabled or os.environ.get("NO_COLOR"):
            self.reset = ""
            self.bold = ""
            self.red = ""
            self.yellow = ""
            self.cyan = ""
            self.white = ""
        else:
            self.reset = "\033[0m"
            self.bold = "\033[1m"
            self.red = "\033[31m"
            self.yellow = "\033[33m"
            self.cyan = "\033[36m"
            self.white = "\033[37m"


_PATH_SEGMENT = re.compile(r"([^.\[\]]+)|\[(\d+)\]")


def _find_line_number(yaml_file: str, path: str) -> int | None:
    """The 1-indexed line of the deepest key of a dotted path like ``controllers.items.access[0]``."""
    try:
        node = yaml.compose(Path(yaml_file).read_text())
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return None
    line = None
    for key, index in _PATH_SEGMENT.findall(path):
        located = _child(node, key, index)
        if located is None:
            break
        mark, node = located
        line = mark.line + 1
    return line


def _child(node: yaml.Node | None, key: str, index: str) -> tuple[yaml.Mark, yaml.Node] | None:
    """The mark naming a mapping key or sequence item, and the node it holds."""
    if index and isinstance(node, yaml.SequenceNode) and int(index) < len(node.value):
        item = node.value[int(index)]
        return item.start_mark, item
    if key and isinstance(node, yaml.MappingNode):
        return next(
            ((name.start_mark, value) for name, value in node.value if name.value == key),
            None,
        )
    return None


def _line_from_location(location: str) -> int | None:
    """Extract the line number from a ``file:line:col`` location string."""
    parts = location.rsplit(":", 2)
    if len(parts) != 3:
        return None
    try:
        return int(parts[1])
    except ValueError:
        return None


def _format_error_gcc_style(
    err: ConfigError,
    yaml_file: str | None,
    colors: Colors,
    content_lines: list[str] | None = None
) -> str:
    """Format a single error in GCC style.

    Args:
        err: Configuration error
        yaml_file: Path to YAML file
        colors: Color configuration
        content_lines: Pre-loaded file lines (optional)

    Returns:
        Formatted error string
    """
    output = []

    filename = yaml_file or "<input>"
    line_num = None

    if err.location:
        # A precise file:line:col from the parser beats guessing a line from
        # the dotted `path`, which only pinpoints a key once values are merged.
        location = err.location
        line_num = _line_from_location(err.location)
    else:
        if yaml_file and err.path:
            line_num = _find_line_number(yaml_file, err.path)
        location = f"{filename}:{line_num}:{err.path or ''}" if line_num else f"{filename}:{err.path or ''}"

    output.append(
        f"{colors.bold}{location}: "
        f"{colors.red}error:{colors.reset} "
        f"{err.message} "
        f"{colors.cyan}[{err.code}]{colors.reset}"
    )

    if line_num and content_lines and 1 <= line_num <= len(content_lines):
        source_line = content_lines[line_num - 1]
        line_num_str = str(line_num).rjust(5)

        output.append(f"{colors.cyan}{line_num_str} |{colors.reset} {source_line}")

        indent = len(source_line) - len(source_line.lstrip())
        marker_line = " " * (7 + indent) + f"{colors.red}^{colors.reset}"
        output.append(marker_line)

    if err.hint:
        output.append(f"{colors.yellow}note:{colors.reset} {err.hint}")

    return "\n".join(output)


def handle_config_errors(
    error: ConfigErrors,
    yaml_file: str | None = None,
    format: str = "human"
) -> NoReturn:
    """Format and report configuration errors, then exit.

    Args:
        error: Configuration errors from YAML parsing/validation
        yaml_file: Path to the YAML file being processed
        format: Output format - "human" (default) or "json"
    """
    if format == "json":
        payload = [item.to_dict() for item in error.errors]
        sys.stderr.write(json.dumps(payload, indent=2) + "\n")
    else:
        colors = Colors(enabled=sys.stderr.isatty())

        content_lines = None
        if yaml_file and Path(yaml_file).exists():
            try:
                with open(yaml_file, 'r') as f:
                    content_lines = f.read().split('\n')
            except (OSError, UnicodeDecodeError):
                pass

        for err in error.errors:
            formatted = _format_error_gcc_style(err, yaml_file, colors, content_lines)
            sys.stderr.write(formatted + "\n")

        error_count = len(error.errors)
        plural = "s" if error_count != 1 else ""
        summary = f"{colors.bold}{colors.red}{error_count} error{plural} generated.{colors.reset}\n"
        sys.stderr.write(summary)

    raise SystemExit(1)


def handle_generic_error(error: Exception) -> NoReturn:
    """Format and report generic errors, then exit.

    Args:
        error: Any exception raised during command execution
    """
    colors = Colors(enabled=sys.stderr.isatty())
    sys.stderr.write(f"{colors.bold}{colors.red}error:{colors.reset} {error}\n")
    raise SystemExit(1)
