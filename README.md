# flutter-event-tracker (Claude Code plugin)

An agent that sets up product analytics in any Flutter app with the `event_tracker_analytics` SDK. The developer
runs it inside their app; it:

1. **checks** the app (Flutter, FVM, the setup tool, Dart 3.13+);
2. **scans** the whole app (any state management or router) with `event_tracker_setup scan`;
3. **reviews** each suggestion in the code: keeps real user actions, drops noise and events already sent,
   and gives them good names (`car_liked`, `test_drive_booked`);
4. **reports** in the chat and opens the **local dashboard** (http://localhost:7777): the tracking report,
   **Connect** to create the API key on the analytics server (saved into the app, git-ignored), and live events;
5. asks for **approval**: integrate / adjust in the dashboard first / set-up only / stop;
6. **integrates** through a guarded subagent: `init` (SDK, init in `main`, screen tracking, track calls),
   `pub get`, `analyze`, tests, and fixes only what init broke;
7. **finishes**: how to run with the key, how to see live events, review `git diff` and commit.

Nothing in the app changes before step 5. The agent never reads the API key, never commits or pushes.

## Contents

```
.claude-plugin/plugin.json          the plugin
.claude-plugin/marketplace.json     a one-plugin marketplace, so it can be installed from this repo
skills/setup-tracking/SKILL.md      the flow above (run in the main conversation: it talks to the developer)
skills/setup-tracking/references/cli.md   the setup tool's commands and JSON, for the skill
agents/event-tracker-integrator.md  the subagent that applies the approved changes
hooks/hooks.json, hooks/integrator_guard.py   guard for that subagent only
tests/test_integrator_guard.py      guard tests
```

**The guard** acts only on the `event-tracker-integrator` subagent; your own session and other agents are never
affected. For the subagent: edits only with Edit, only in `lib/`, `test/` and `pubspec.yaml` of the app being set
up (the folder with `.event_tracker/`); no reading keys, keystores or env files; shell from an allow-list
(`dart`/`flutter` pub get, analyze, test, format; the setup tool's scan/init/select without `--force`; read-only
git and file tools). No commits, pushes, deletes, file redirects or network tools.

## Requirements

- Claude Code
- Dart 3.13+ / Flutter 3.47+ (FVM is detected)
- The setup tool (`event_tracker_setup`), installed once with `dart pub global activate` (the agent asks first):
  ```bash
  dart pub global activate --source git <event_tracker_setup repo url>
  dart pub global activate --source path ~/Desktop/hackathon_2026/event_tracker_setup   # local copy
  ```
- Python 3 (for the guard hook)
- The SDK must be reachable from the app: by default `init` uses the SDK's git repo; pass `--sdk-path` (local)
  or `--sdk-version` (pub.dev) through the agent if needed.

## Install

Try it for one session without installing:

```bash
cd my_flutter_app
claude --plugin-dir ~/Desktop/hackathon_2026/event_tracker_agent
```

Install (user scope) from a local folder or a git repo:

```bash
claude plugin marketplace add ~/Desktop/hackathon_2026/event_tracker_agent     # or the repo URL
claude plugin install flutter-event-tracker@event-tracker
```

Then, in the app folder: `/flutter-event-tracker:setup-tracking`, or just ask
"add analytics to this app" / "where should this app track events?".

## Development

```bash
python3 -m unittest discover -s tests      # guard tests
claude plugin validate .                   # manifest, skill, agent and hooks
```

Change the setup tool's behaviour in `../event_tracker_setup` (its README documents every command); keep
`references/cli.md` in step with it.
