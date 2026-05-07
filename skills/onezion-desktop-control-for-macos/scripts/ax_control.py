#!/usr/bin/env python3
"""AX background control — operate macOS apps without bringing them to the foreground.

Uses the macOS Accessibility API (AXUIElement) via pyax to find and interact
with UI elements by semantic role, title, description, or value — no screenshots
or mouse coordinates needed.

Requirements:
  pip install pyax

Permissions:
  System Settings → Privacy & Security → Accessibility (must be granted)
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Optional

import pyax


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_attr(elem, attr: str, default=None):
    """Read an AX attribute, returning *default* on any error."""
    try:
        return elem[attr]
    except Exception:
        return default


def _describe(elem) -> dict[str, Any]:
    """Return a compact JSON-friendly description of an AX element."""
    role = _safe_attr(elem, "AXRole", "")
    subrole = _safe_attr(elem, "AXSubrole", "")
    title = _safe_attr(elem, "AXTitle", "")
    desc = _safe_attr(elem, "AXDescription", "")
    value = _safe_attr(elem, "AXValue", "")
    enabled = _safe_attr(elem, "AXEnabled", None)
    focused = _safe_attr(elem, "AXFocused", None)

    # Position / size (useful for debugging)
    pos = _safe_attr(elem, "AXPosition")
    size = _safe_attr(elem, "AXSize")
    pos_dict = None
    size_dict = None
    if pos is not None:
        try:
            pos_dict = {"x": float(pos.x), "y": float(pos.y)}
        except Exception:
            pass
    if size is not None:
        try:
            size_dict = {"w": float(size.width), "h": float(size.height)}
        except Exception:
            pass

    # Actions
    try:
        actions = list(elem.actions())
    except Exception:
        actions = []

    result: dict[str, Any] = {"role": role}
    if subrole:
        result["subrole"] = subrole
    if title:
        result["title"] = str(title)
    if desc:
        result["description"] = str(desc)
    if value is not None and value != "":
        result["value"] = str(value)
    if enabled is not None:
        result["enabled"] = enabled
    if focused is not None:
        result["focused"] = focused
    if pos_dict:
        result["position"] = pos_dict
    if size_dict:
        result["size"] = size_dict
    if actions:
        result["actions"] = actions
    return result


def _get_app(app_name: str, pid: Optional[int] = None):
    """Get an AXApplication element by name or PID."""
    if pid:
        return pyax.get_application_by_pid(pid)
    return pyax.get_application_by_name(app_name)


def _get_window(app, window_index: int = 0):
    """Return the Nth window of an application."""
    windows = app["AXWindows"]
    if not windows:
        raise SystemExit(f"No windows found for application.")
    if window_index >= len(windows):
        raise SystemExit(
            f"Window index {window_index} out of range (app has {len(windows)} windows)."
        )
    return windows[window_index]


def _matches(elem, role: Optional[str] = None, title: Optional[str] = None,
             description: Optional[str] = None, value: Optional[str] = None) -> bool:
    """Check whether an element matches all given criteria."""
    if role:
        try:
            if elem["AXRole"] != role:
                return False
        except Exception:
            return False
    if title:
        try:
            t = str(_safe_attr(elem, "AXTitle", "") or "")
            if title.lower() not in t.lower():
                return False
        except Exception:
            return False
    if description:
        try:
            d = str(_safe_attr(elem, "AXDescription", "") or "")
            if description.lower() not in d.lower():
                return False
        except Exception:
            return False
    if value:
        try:
            v = str(_safe_attr(elem, "AXValue", "") or "")
            if value.lower() not in v.lower():
                return False
        except Exception:
            return False
    return True


def _find_elements(root, role: Optional[str] = None, title: Optional[str] = None,
                   description: Optional[str] = None, value: Optional[str] = None,
                   max_results: int = 50) -> list:
    """Recursively search for ALL elements matching the given criteria.

    Note: pyax's built-in search_for() only returns the first match.
    This function traverses the full tree and collects all matches.
    """
    collected: list = []

    def _walk(node):
        if len(collected) >= max_results:
            return
        if _matches(node, role=role, title=title, description=description, value=value):
            collected.append(node)
        try:
            for child in node:
                if len(collected) >= max_results:
                    return
                _walk(child)
        except Exception:
            pass

    _walk(root)
    return collected


def _dump_tree(elem, depth: int = 0, max_depth: int = 5) -> list[dict[str, Any]]:
    """Recursively dump the AX tree as a list of dicts."""
    if depth > max_depth:
        return []
    node = _describe(elem)
    node["depth"] = depth
    children: list[dict[str, Any]] = []
    try:
        for child in elem:
            children.extend(_dump_tree(child, depth + 1, max_depth))
    except Exception:
        pass
    if children:
        node["children"] = children
    return [node]


def _format_tree_flat(nodes: list[dict], indent: str = "  ") -> list[str]:
    """Render tree nodes as flat indented lines."""
    lines: list[str] = []
    for node in nodes:
        d = node.get("depth", 0)
        role = node.get("role", "?")
        parts = [f"{indent * d}{role}"]
        if node.get("title"):
            parts.append(f'title={node["title"]!r}')
        if node.get("description"):
            parts.append(f'desc={node["description"]!r}')
        if node.get("value"):
            v = str(node["value"])
            if len(v) > 40:
                v = v[:40] + "..."
            parts.append(f'value={v!r}')
        if node.get("actions"):
            parts.append(f'actions={node["actions"]}')
        lines.append(" ".join(parts))
        if "children" in node:
            lines.extend(_format_tree_flat(node["children"], indent))
    return lines


def emit(payload: dict[str, Any], pretty: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2 if pretty else None))


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------

def action_tree(args) -> None:
    """Dump the AX element tree of an application or window."""
    app = _get_app(args.app, args.pid)
    if args.window:
        root = _get_window(app, args.window_index)
    else:
        root = app
    nodes = _dump_tree(root, max_depth=args.depth)
    if args.pretty_tree:
        lines = _format_tree_flat(nodes)
        emit({"ok": True, "tool": "ax_control", "action": "tree", "app": args.app, "lines": lines}, args.json_pretty)
    else:
        emit({"ok": True, "tool": "ax_control", "action": "tree", "app": args.app, "tree": nodes}, args.json_pretty)


def action_search(args) -> None:
    """Search for AX elements matching criteria."""
    app = _get_app(args.app, args.pid)
    if args.window:
        root = _get_window(app, args.window_index)
    else:
        root = app
    elements = _find_elements(root, role=args.role, title=args.title,
                              description=args.description, value=args.value,
                              max_results=args.max)
    results = [_describe(e) for e in elements]
    emit({
        "ok": True, "tool": "ax_control", "action": "search",
        "app": args.app, "count": len(results), "results": results,
    }, args.json_pretty)


def _resolve_element(app, args):
    """Find a single target element. Supports --role/--title/--description/--value
    or --index from a search, or --path for direct hierarchy navigation."""
    if args.window:
        root = _get_window(app, args.window_index)
    else:
        root = app

    if args.path:
        # Navigate by path like "AXToolbar/AXGroup/AXTextField"
        parts = args.path.split("/")
        current = root
        for part in parts:
            found = False
            for child in current:
                if child["AXRole"] == part:
                    current = child
                    found = True
                    break
            if not found:
                raise SystemExit(f"Path element '{part}' not found in hierarchy.")
        return current

    elements = _find_elements(root, role=args.role, title=args.title,
                              description=args.description, value=args.value,
                              max_results=args.max)
    if not elements:
        raise SystemExit("No matching elements found.")
    if args.index >= len(elements):
        raise SystemExit(f"Index {args.index} out of range ({len(elements)} matches found).")
    return elements[args.index]


def action_click(args) -> None:
    """Perform AXPress action on an element (background, no foreground needed)."""
    app = _get_app(args.app, args.pid)
    elem = _resolve_element(app, args)
    action_name = args.ax_action or "AXPress"
    try:
        elem.perform_action(action_name)
    except Exception as e:
        emit({"ok": False, "tool": "ax_control", "action": "click", "error": str(e)}, args.json_pretty)
        return
    info = _describe(elem)
    emit({
        "ok": True, "tool": "ax_control", "action": "click",
        "app": args.app, "performed": action_name, "element": info,
    }, args.json_pretty)


def action_set_value(args) -> None:
    """Set AXValue on an element (background, no foreground needed)."""
    app = _get_app(args.app, args.pid)
    elem = _resolve_element(app, args)
    text = args.text
    if text is None and args.stdin:
        text = sys.stdin.read()
    if text is None:
        raise SystemExit("Action 'set-value' requires --text or --stdin.")
    try:
        elem["AXValue"] = text
    except Exception as e:
        emit({"ok": False, "tool": "ax_control", "action": "set_value", "error": str(e)}, args.json_pretty)
        return
    info = _describe(elem)
    emit({
        "ok": True, "tool": "ax_control", "action": "set_value",
        "app": args.app, "text": text, "element": info,
    }, args.json_pretty)


def action_get_value(args) -> None:
    """Read AXValue from an element (background)."""
    app = _get_app(args.app, args.pid)
    elem = _resolve_element(app, args)
    info = _describe(elem)
    emit({
        "ok": True, "tool": "ax_control", "action": "get_value",
        "app": args.app, "element": info,
    }, args.json_pretty)


def action_focus(args) -> None:
    """Set AXFocused=True on an element (background)."""
    app = _get_app(args.app, args.pid)
    elem = _resolve_element(app, args)
    try:
        elem["AXFocused"] = True
    except Exception as e:
        emit({"ok": False, "tool": "ax_control", "action": "focus", "error": str(e)}, args.json_pretty)
        return
    info = _describe(elem)
    emit({
        "ok": True, "tool": "ax_control", "action": "focus",
        "app": args.app, "element": info,
    }, args.json_pretty)


def action_apps(args) -> None:
    """List running applications that have accessibility support."""
    import subprocess
    out = subprocess.run(
        ["osascript", "-e",
         'tell application "System Events" to return name of every application process'],
        capture_output=True, text=True, check=True,
    )
    names = [n.strip() for n in out.stdout.strip().split(",") if n.strip()]
    apps_info = []
    for name in names:
        try:
            app = pyax.get_application_by_name(name)
            windows = app["AXWindows"]
            apps_info.append({
                "name": name,
                "pid": app.pid,
                "windows": len(windows) if windows else 0,
                "ax_available": True,
            })
        except Exception:
            apps_info.append({"name": name, "ax_available": False})
    emit({
        "ok": True, "tool": "ax_control", "action": "apps",
        "count": len(apps_info), "apps": apps_info,
    }, args.json_pretty)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AX background control — operate macOS apps without foreground.",
    )
    parser.add_argument("--action", required=True, choices=[
        "tree", "search", "click", "set-value", "get-value", "focus", "apps",
    ])
    # Target app
    parser.add_argument("--app", help="Application name, e.g. Safari or 微信.")
    parser.add_argument("--pid", type=int, help="Application PID (alternative to --app).")
    parser.add_argument("--window", action="store_true", help="Target a window instead of the whole app.")
    parser.add_argument("--window-index", type=int, default=0, help="Which window (default 0).")

    # Element matching (for search, click, set-value, get-value, focus)
    parser.add_argument("--role", help="AXRole filter, e.g. AXButton, AXTextField.")
    parser.add_argument("--title", help="AXTitle substring match (case-insensitive).")
    parser.add_argument("--description", help="AXDescription substring match.")
    parser.add_argument("--value", help="AXValue substring match.")
    parser.add_argument("--index", type=int, default=0, help="Which match to use (default 0 = first).")
    parser.add_argument("--max", type=int, default=50, help="Max search results.")
    parser.add_argument("--path", help="Direct hierarchy path, e.g. AXToolbar/AXGroup/AXTextField.")

    # Action-specific
    parser.add_argument("--ax-action", help="AX action name for click (default AXPress).")
    parser.add_argument("--text", help="Text for set-value action.")
    parser.add_argument("--stdin", action="store_true", help="Read text from stdin for set-value.")

    # Tree options
    parser.add_argument("--depth", type=int, default=5, help="Max tree depth (for tree action).")
    parser.add_argument("--pretty-tree", action="store_true", help="Flat indented tree output.")

    # Output
    parser.add_argument("--json-pretty", action="store_true", help="Pretty-print JSON output.")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.action == "apps":
        action_apps(args)
        return

    if not args.app and not args.pid:
        raise SystemExit("Action '{}' requires --app or --pid.".format(args.action))

    if args.action == "tree":
        action_tree(args)
    elif args.action == "search":
        action_search(args)
    elif args.action == "click":
        action_click(args)
    elif args.action == "set-value":
        action_set_value(args)
    elif args.action == "get-value":
        action_get_value(args)
    elif args.action == "focus":
        action_focus(args)
    else:
        raise SystemExit(f"Unsupported action: {args.action}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stderr.write(str(e) + "\n")
        raise
