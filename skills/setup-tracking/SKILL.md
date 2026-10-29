---
name: setup-tracking
description: Sets up product analytics (event tracking) in a Flutter app with the event_tracker_analytics SDK. Scans the whole app, tells the developer where events are worth tracking and why, opens a local dashboard report (where they also create their API key), and only after their approval adds the SDK, the init call, screen tracking and the chosen track calls, then checks the app still analyzes clean and its tests pass. Use when the user asks to add analytics, event tracking or the event tracker SDK to a Flutter app, or asks where their Flutter app should track events.
---

# Set up event tracking in a Flutter app

You guide the developer from "no analytics" to "events arriving", in this order: check → scan → review →
report and dashboard → approval → integrate → verify. Work with any state management and router.

## Rules (for the whole conversation)

1. **No code changes before approval.** Until the developer approves in step 5, the only files written are the
   setup tool's own: `.event_tracker/` (plan, selection). After approval, the `event-tracker-integrator` subagent
   makes the changes; you don't edit app code yourself, except step 7's property additions, each shown first and
   approved.
2. **Never read or print secrets.** `event_tracker.json` holds the API key: check that it exists
   (`test -f event_tracker.json`), never open it. Same for `.env*`, keystores, `key.properties`.
3. **Never commit, push or change git state.** The developer reviews `git diff` and commits.
4. **No personal data in events.** Never propose sending typed text, names, emails, phone numbers, passwords or
   tokens as properties. Ids, counts, choices from a fixed list, prices and screen names are fine.
5. Explain in plain words why each place matters. Keep messages short; long lists go in the dashboard.
6. If a command or the guard blocks something, say what and why, and stop that step. Don't work around it.

Command reference: [references/cli.md](references/cli.md). Below, `<app>` is the app's absolute path,
`<CLI>` the setup tool command and `<Flutter>` the flutter command, as found in step 1.

## Step 1: Check

1. Find the app: the current folder, or the folder the user named. It needs `pubspec.yaml` with
   `flutter: sdk: flutter`. If several apps are below the current folder, ask which one.
2. FVM: if the app has `.fvmrc` or `.fvm/`, use `fvm dart` / `fvm flutter`; otherwise `dart` / `flutter`.
3. The tool: run `<dart> pub global list` and look for `event_tracker_setup`. If it's missing, tell the
   developer it is needed and ask before installing it:
   - from GitHub: `<dart> pub global activate --source git https://github.com/NamanFiftyFive/event_tracker_setup.git`
     (while the repo is private, use `git@github.com:NamanFiftyFive/event_tracker_setup.git`, which needs SSH
     access to it)
   - from a local folder: `<dart> pub global activate --source path <folder>`
   It needs Dart 3.13 or newer (`<dart> --version`); if older, stop and say so.
   `<CLI>` is then `<dart> pub global run event_tracker_setup`.
4. If the app is a git repo with uncommitted changes, mention it: committing first makes the analytics changes
   easy to review and undo.

## Step 2: Scan

Run `<CLI> scan <app>`. It prints a summary and writes `<app>/.event_tracker/tracking_plan.json`; read that file.
Note the warnings: a Riverpod version conflict means init will refuse until the developer upgrades Riverpod
(never pass `--force` on your own).

## Step 3: Review (this is where you add value)

For every high and medium suggestion, and every `similar_tracked_event`:

1. Read the code around `file:line` (and the handler method it calls).
2. Decide:
   - **Keep**: a real user action that matters for the product (sign-up, purchase, booking, search, share, key
     settings, main feature use).
   - **Drop**: noise (retry buttons, close/cancel, pure navigation already covered by screen tracking, debug UI),
     or already sent (`similar_tracked_event` when the called method really tracks it: open it and check).
   - Low-priority suggestions: keep only if clearly useful.
3. Name each kept event `<object>_<past tense verb>`, snake_case, consistent with `tracked_events` already in the
   app: `test_drive_booked`, `car_liked`, `sign_in_submitted`, `checkout_started`, `filter_changed`. Rename when
   the scan's name is weak (`segmented_changed`, `likes_tapped`, `name_tapped`).
4. Note useful properties for later (step 7), within rule 4.

Then save your picks: `<CLI> select <app> --pick <id>=<event_name> --pick ...` (one `--pick` per kept place).

## Step 4: Report and dashboard

1. Run `<CLI> init <app> --dry-run --json` (writes nothing) to know exactly what would change.
2. Start the dashboard in the background (it keeps running): `<CLI> dashboard <app>`. It opens
   http://localhost:7777 (if the port is busy, use `--port 7778`).
3. Tell the developer, briefly:
   - what the app uses (state management, router) and the set-up changes (dependency, init in `main`, screen
     tracking on the router or app widget), with file:line;
   - a table of the places you chose: event, where (file:line, screen), why; and how many you dropped and why
     (one line);
   - files that will change (from the dry run) and any warning;
   - the dashboard: **Tracking report** shows the same list (they can tick or untick and press Save selection);
     **Connect** is where they log in or sign up and create the project's API key (it is saved into the app and
     git-ignored; you never see it); **Live events** will show events as they use the app.

## Step 5: Approval

Ask with the selection tool (AskUserQuestion) when available:

- **Integrate now** (recommended): apply the selection as saved.
- **I'll adjust in the dashboard first**: wait until they say they're done, then reread
  `.event_tracker/selection.json`, run the dry run again and ask again.
- **Set-up only**: SDK, init and screen tracking, no track calls (run `select` with no `--pick` first, which
  saves an empty selection).
- **Stop**: change nothing; the dashboard can stay open for reading.

Do not continue without an explicit yes.

## Step 6: Integrate (subagent)

Delegate to the `event-tracker-integrator` subagent (`flutter-event-tracker:event-tracker-integrator`) in the
foreground, with this message:

```
App root: <app>
Dart: <dart>    Flutter: <Flutter>
CLI: <CLI>
SDK flags: <empty, or e.g. --sdk-path ... when the developer uses a local SDK>
```

Relay its report: changed files, added events, anything skipped, analyze and test results, and any fix it made
beyond init. If it stopped, explain why and what the developer can do.

## Step 7: Finish

1. Key: `test -f <app>/event_tracker.json`. If missing, point them to the dashboard's **Connect** tab.
2. How to run: `<Flutter> run --dart-define-from-file=event_tracker.json`. For the Android emulator the live view
   needs `TRACKER_DEV_SERVER` set to `http://10.0.2.2:7777` (the dashboard saved `http://localhost:7777`, which is
   right for iOS simulators, web and desktop); they can pass `--dart-define=TRACKER_DEV_SERVER=http://10.0.2.2:7777`.
3. Verify: ask them to use the app and watch **Live events**; each chosen event gets a tick when it fires.
4. Optional, if you noted useful properties in step 3: offer to add them. Show the exact change per call first
   (e.g. `EventTracker.track('car_liked', {'model': car.model})`); make only the ones they approve, then run
   `<Flutter> analyze` on those files.
5. Remind them to review `git diff` and commit. The dashboard keeps running until they stop it.
