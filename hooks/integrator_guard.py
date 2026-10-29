#!/usr/bin/env python3
"""PreToolUse guard for the flutter-event-tracker plugin.

It only acts on calls from the plugin's own `event-tracker-integrator` subagent; every other call
(the user's session, other agents) passes untouched (exit 0).

For the integrator it enforces, mechanically:
- edits only with Edit/MultiEdit, only in lib/, test/ or pubspec.yaml of the Flutter app being set up
  (the nearest folder with pubspec.yaml and .event_tracker/, inside the session folder);
- no reading of keys, keystores or env files (event_tracker.json holds the API key);
- shell commands from an allow-list: dart/flutter pub get, analyze, test, format; the setup CLI's
  scan/init/select (no --force, no dashboard); read-only git and file tools. No commits, pushes,
  deletes, redirects into files or network tools.

Exit 2 with a message on stderr blocks the call.
"""
import json
import os
import re
import shlex
import sys

AGENT_NAMES = {"event-tracker-integrator", "flutter-event-tracker:event-tracker-integrator"}

SECRET_NAME = re.compile(
    r"(^|/)(\.env(\.[^/]*)?|event_tracker\.json|key\.properties|google-services\.json|GoogleService-Info\.plist"
    r"|[^/]*\.(jks|keystore|p12|pem|key|mobileprovision))$"
)
SECRET_WORD = re.compile(
    r"(^|[\s/'\"=])(\.env(\.\w+)?|event_tracker\.json|key\.properties|[\w.-]+\.(jks|keystore|p12|pem))(?=$|[\s'\";|&)])"
)
EDITABLE = re.compile(r"^(lib|test)/.+\.dart$|^pubspec\.yaml$")

READ_ONLY_TOOLS = {"ls", "cat", "head", "tail", "wc", "grep", "rg", "pwd", "echo", "test", "[", "true", "which", "diff", "sort", "uniq"}
GIT_READ = {"diff", "status", "log", "show", "rev-parse", "ls-files"}
DART_FLUTTER_OK = {"analyze", "test", "format", "--version", "doctor"}
PUB_OK = {"get", "deps", "outdated"}
CLI_OK = {"scan", "init", "select"}


class Deny(Exception):
    pass


def deny(reason):
    raise Deny(reason)


def app_root_of(path):
    """Nearest folder above `path` with pubspec.yaml and .event_tracker/ (an app being set up)."""
    folder = path if os.path.isdir(path) else os.path.dirname(path)
    while True:
        if os.path.isfile(os.path.join(folder, "pubspec.yaml")) and os.path.isdir(os.path.join(folder, ".event_tracker")):
            return folder
        parent = os.path.dirname(folder)
        if parent == folder:
            return None
        folder = parent


def check_edit(tool, tool_input, cwd):
    if tool not in ("Edit", "MultiEdit"):
        deny(f"{tool} is not allowed; the integrator changes code only with Edit (init writes the rest)")
    path = os.path.realpath(os.path.join(cwd, tool_input.get("file_path", "")))
    if SECRET_NAME.search(path):
        deny("key and env files are never edited")
    if not (path == cwd or path.startswith(cwd + os.sep)):
        deny("only files inside the session folder may be edited")
    root = app_root_of(path)
    if root is None:
        deny("only the Flutter app being set up (the folder with .event_tracker/) may be edited")
    relative = os.path.relpath(path, root)
    if not EDITABLE.match(relative):
        deny(f"only lib/, test/ and pubspec.yaml may be edited, not {relative}")


def check_read(tool, tool_input):
    for key in ("file_path", "path", "pattern", "glob"):
        value = tool_input.get(key) or ""
        if key in ("file_path", "path") and SECRET_NAME.search(value.rstrip("/")):
            deny("keys and env files are never read (event_tracker.json holds the API key)")
        if key == "glob" and re.search(r"\.env|event_tracker\.json|\.jks|\.keystore|key\.properties", value):
            deny("keys and env files are never searched")
    if tool == "Glob" and re.search(r"\.env|event_tracker\.json", tool_input.get("pattern", "")):
        deny("keys and env files are never listed")


def segments(command):
    """Split on && || ; | (outside quotes) into word lists."""
    parts, current, quote = [], "", None
    i = 0
    while i < len(command):
        ch = command[i]
        if quote:
            current += ch
            if ch == quote:
                quote = None
        elif ch in "'\"":
            quote = ch
            current += ch
        elif command.startswith("&&", i) or command.startswith("||", i):
            parts.append(current)
            current = ""
            i += 1
        elif ch in ";|\n":
            parts.append(current)
            current = ""
        else:
            current += ch
        i += 1
    parts.append(current)
    try:
        return [shlex.split(p) for p in parts if p.strip()]
    except ValueError:
        deny("the command could not be read (unbalanced quotes)")


def check_dart_flutter(words):
    tool = words[0]
    rest = words[1:]
    if tool == "fvm":
        if rest[:1] == ["spawn"] and len(rest) >= 3:
            rest = ["flutter"] + rest[2:]
        if not rest or rest[0] not in ("dart", "flutter"):
            deny("fvm may only run dart or flutter")
        tool, rest = rest[0], rest[1:]
    if not rest:
        deny(f"bare '{tool}' is not allowed")
    sub = rest[0]
    if sub in DART_FLUTTER_OK:
        if sub == "format" and any(w.startswith("--") and w not in ("--output=none", "--set-exit-if-changed") for w in rest[1:]):
            deny("dart format: only file paths (and --output=none)")
        return
    if sub == "pub":
        if rest[1:2] and rest[1] in PUB_OK:
            return
        if rest[1:4] == ["global", "run", "event_tracker_setup"] or rest[1:3] == ["global", "list"]:
            if rest[1:3] == ["global", "list"]:
                return
            command = rest[4] if len(rest) > 4 else ""
            if command not in CLI_OK:
                deny(f"event_tracker_setup {command or '(none)'}: the integrator may run only scan, init and select")
            if "--force" in rest:
                deny("init --force overrides a warning the user must decide on; ask them instead")
            return
        deny(f"'{tool} pub {' '.join(rest[1:2])}' is not allowed (only pub get, deps, outdated, global run event_tracker_setup)")
    deny(f"'{tool} {sub}' is not allowed (only analyze, test, format, pub get)")


def check_bash(command):
    if SECRET_WORD.search(command):
        deny("keys and env files are never read or touched")
    if re.search(r"(?<![0-9&])>(?!\s*&|\s*/dev/null)|(^|\s)\d?>>", command):
        deny("writing files with > is not allowed; use Edit")
    for words in segments(command):
        if not words:
            continue
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[0]):
            deny("setting environment variables in commands is not allowed")
        program = os.path.basename(words[0])
        if program == "cd":
            continue
        if program in ("dart", "flutter", "fvm"):
            check_dart_flutter([program] + words[1:])
        elif program == "git":
            sub = next((w for w in words[1:] if not w.startswith("-")), "")
            if sub not in GIT_READ:
                deny(f"git {sub}: the integrator never commits, pushes or changes git state; the user does that")
        elif program == "sed":
            if any(w == "-i" or w.startswith("-i") or w == "--in-place" for w in words[1:]):
                deny("sed -i edits files; use Edit")
        elif program == "find":
            if any(w in ("-delete", "-exec", "-execdir", "-ok") for w in words[1:]):
                deny("find may only list files")
        elif program not in READ_ONLY_TOOLS:
            deny(f"'{program}' is not on the integrator's allow-list")


def main():
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except Exception:
        if re.search(r'"agent_type"\s*:\s*"(flutter-event-tracker:)?event-tracker-integrator"', raw):
            print("Blocked by flutter-event-tracker guard: unreadable hook input.", file=sys.stderr)
            sys.exit(2)
        sys.exit(0)
    if data.get("agent_type") not in AGENT_NAMES:
        sys.exit(0)  # not the integrator: never interfere with the user's session
    try:
        tool = data.get("tool_name", "")
        tool_input = data.get("tool_input") or {}
        cwd = os.path.realpath(data.get("cwd") or os.getcwd())
        if tool in ("Edit", "MultiEdit", "Write", "NotebookEdit"):
            check_edit(tool, tool_input, cwd)
        elif tool in ("Read", "Grep", "Glob"):
            check_read(tool, tool_input)
        elif tool == "Bash":
            check_bash(tool_input.get("command", ""))
    except Deny as error:
        print(f"Blocked by flutter-event-tracker guard: {error}.", file=sys.stderr)
        sys.exit(2)
    except Exception as error:  # fail closed for the integrator
        print(f"Blocked by flutter-event-tracker guard: internal error ({type(error).__name__}).", file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
