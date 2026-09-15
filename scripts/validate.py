#!/usr/bin/env python3
"""Validate the redfox-agent-plugins repository structure.

Checks:
1. All marketplace.json files parse and reference existing plugin dirs
2. Each plugin has all 5 manifests, each parses as JSON
3. Manifest names match the plugin directory name
4. Each plugin has skills/<name>/SKILL.md with valid frontmatter
5. SKILL.md frontmatter has name + description; name matches dir;
   name is kebab-case, <=64 chars, no consecutive hyphens
6. description <= 1024 chars
7. No Claude reserved marketplace/plugin names
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

RESERVED = {
    "claude-code-marketplace", "claude-code-plugins", "claude-plugins-official",
    "claude-plugins-community", "claude-community", "anthropic-marketplace",
    "anthropic-plugins", "agent-skills", "anthropic-agent-skills",
    "knowledge-work-plugins", "life-sciences", "claude-for-legal",
    "claude-for-financial-services", "financial-services-plugins",
    "first-party-plugins", "claude-tag-plugins", "healthcare",
}

MARKETPLACES = [
    ".claude-plugin/marketplace.json",
    ".agents/plugins/marketplace.json",
    ".cursor-plugin/marketplace.json",
]

PLUGIN_MANIFESTS = [
    "plugin.json",
    ".claude-plugin/plugin.json",
    ".codex-plugin/plugin.json",
    ".cursor-plugin/plugin.json",
    "gemini-extension.json",
]

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def parse_frontmatter(text: str) -> dict | None:
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    fm: dict = {}
    current_key = None
    for line in text[4:end].splitlines():
        if not line.strip():
            continue
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m and not line.startswith(" "):
            current_key = m.group(1)
            fm[current_key] = m.group(2).strip()
        elif line.startswith(" ") and current_key:
            fm[current_key] = (fm[current_key] + " " + line.strip()).strip()
    return fm


def check_marketplaces() -> list[str]:
    plugin_dirs: set[str] = set()
    for rel in MARKETPLACES:
        p = ROOT / rel
        if not p.exists():
            err(f"missing marketplace manifest: {rel}")
            continue
        try:
            data = json.loads(p.read_text())
        except json.JSONDecodeError as e:
            err(f"{rel}: invalid JSON ({e})")
            continue
        if "name" in data and data["name"] in RESERVED:
            err(f"{rel}: marketplace name '{data['name']}' is reserved")
        plugins = data.get("plugins", [])
        if not plugins:
            err(f"{rel}: no plugins listed")
        plugin_root = (data.get("metadata") or {}).get("pluginRoot", "./plugins")
        for entry in plugins:
            name = entry.get("name", "?")
            src = entry.get("source", "")
            d = None
            if isinstance(src, dict):
                # Codex style: {"source": "local", "path": "./plugins/<name>"}
                path = src.get("path")
                if path:
                    d = (ROOT / path).resolve()
            elif isinstance(src, str) and src.startswith("./"):
                # Claude style: "./plugins/<name>"
                d = (ROOT / src).resolve()
            elif isinstance(src, str) and src:
                # Cursor style: "<name>" relative to metadata.pluginRoot
                d = (ROOT / plugin_root / src).resolve()
            if d is None or not d.is_dir():
                err(f"{rel}: plugin '{name}' source '{src}' does not exist")
            else:
                plugin_dirs.add(d.name)
                if d.name != name:
                    err(f"{rel}: plugin name '{name}' != dir '{d.name}'")
    return sorted(plugin_dirs)


def check_plugin(d: Path) -> None:
    name = d.name
    if name in RESERVED:
        err(f"{name}: plugin name is reserved by Claude")
    if not NAME_RE.match(name) or "--" in name or len(name) > 64:
        err(f"{name}: invalid kebab-case name")

    for rel in PLUGIN_MANIFESTS:
        p = d / rel
        if not p.exists():
            err(f"{name}: missing manifest {rel}")
            continue
        try:
            data = json.loads(p.read_text())
        except json.JSONDecodeError as e:
            err(f"{name}/{rel}: invalid JSON ({e})")
            continue
        mname = data.get("name")
        if mname != name:
            err(f"{name}/{rel}: manifest name '{mname}' != '{name}'")
        if not data.get("description"):
            err(f"{name}/{rel}: missing description")
        if rel == "gemini-extension.json":
            if not data.get("contextFileName"):
                warnings.append(f"{name}/{rel}: no contextFileName")

    skill_md = d / "skills" / name / "SKILL.md"
    if not skill_md.exists():
        err(f"{name}: missing skills/{name}/SKILL.md")
        return
    text = skill_md.read_text()
    fm = parse_frontmatter(text)
    if fm is None:
        err(f"{name}: SKILL.md has no valid frontmatter")
        return
    if fm.get("name") != name:
        err(f"{name}: SKILL.md name '{fm.get('name')}' != dir name")
    desc = fm.get("description", "")
    if not desc:
        err(f"{name}: SKILL.md missing description")
    if len(desc) > 1024:
        err(f"{name}: SKILL.md description too long ({len(desc)} > 1024)")
    body_lines = text.count("\n")
    if body_lines > 500:
        warnings.append(f"{name}: SKILL.md is {body_lines} lines (>500 recommended max)")

    if not (d / "assets" / "logo.svg").exists():
        warnings.append(f"{name}: missing assets/logo.svg")


def main() -> int:
    names = check_marketplaces()
    plugins_root = ROOT / "plugins"
    dirs = sorted(p.name for p in plugins_root.iterdir() if p.is_dir()) if plugins_root.is_dir() else []
    for d in dirs:
        check_plugin(plugins_root / d)
    # marketplace coverage
    for d in dirs:
        if d not in names:
            err(f"plugin '{d}' not referenced by any marketplace.json")

    print(f"Plugins checked: {len(dirs)}")
    for w in warnings:
        print(f"WARNING: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    if errors:
        print(f"\nFAILED with {len(errors)} error(s)")
        return 1
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
