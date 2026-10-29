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
- Dart 3.13+ / Flutter 3.47+. With FVM, run `fvm use 3.47.0` inside the app folder (the agent also finds
  FVM set in a parent folder, or uses it when `flutter` isn't on the PATH)
- The setup tool (`event_tracker_setup`); the agent installs it after asking. By hand:
  ```bash
  dart pub global activate --source git https://github.com/NamanFiftyFive/event_tracker_setup.git
  ```
- Python 3 (for the guard hook)
- Internet access to GitHub: `init` adds the SDK from its public git repo by default (`--sdk-path` for a local
  copy, `--sdk-version` for pub.dev, if the developer asks)
- Git in the app is recommended (not required), so the changes can be reviewed with `git diff` and undone

All three repos are public:
plugin https://github.com/NamanFiftyFive/event_tracker_agent,
setup tool https://github.com/NamanFiftyFive/event_tracker_setup,
SDK https://github.com/NamanFiftyFive/evnet_tracker_analytics_sdk.

## Install (from GitHub)

Once per computer:

```bash
claude plugin marketplace add NamanFiftyFive/event_tracker_agent
claude plugin install flutter-event-tracker@event-tracker
claude plugin list          # flutter-event-tracker@event-tracker, enabled
```

Or inside Claude Code: `/plugin` → Marketplaces → Add marketplace → `NamanFiftyFive/event_tracker_agent` →
install **flutter-event-tracker**. Restart an open Claude session afterwards.

| To | Run |
|---|---|
| Update after changes are pushed | `claude plugin marketplace update event-tracker` then `claude plugin update flutter-event-tracker@event-tracker` |
| Turn off / on | `claude plugin disable flutter-event-tracker@event-tracker` / `enable` |
| Remove | `claude plugin uninstall flutter-event-tracker@event-tracker` |
| Try a local copy without installing (plugin development) | `claude --plugin-dir ~/Desktop/hackathon_2026/event_tracker_agent` |

## Use

```bash
cd my_flutter_app
fvm use 3.47.0                                                   # FVM users, once
git init && git add -A && git commit -m "Before analytics"       # recommended, once
claude
```

Then ask "add analytics to this app" (or run `/flutter-event-tracker:setup-tracking`). After you approve and
the agent finishes, run the app with the key it saved:

```bash
fvm flutter run --dart-define-from-file=event_tracker.json
# Android emulator, for Live events: add --dart-define=TRACKER_DEV_SERVER=http://10.0.2.2:7777
```

**Later runs:** the key stays in `event_tracker.json`, so just run the app again. The local dashboard
(report, Connect, Live events) stops when the Claude session ends; start it again in its own terminal:

```bash
fvm dart pub global run event_tracker_setup dashboard .     # http://localhost:7777, Ctrl+C to stop
```

To track new screens or buttons later, ask the agent again: it only proposes what's new.

Other ways to ask: "where should this app track events?", "set up event tracking".

## Development

```bash
python3 -m unittest discover -s tests      # guard tests
claude plugin validate .                   # manifest, skill, agent and hooks
```

Change the setup tool's behaviour in `../event_tracker_setup` (its README documents every command); keep
`references/cli.md` in step with it.
