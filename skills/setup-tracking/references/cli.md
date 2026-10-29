# event_tracker_setup CLI: what the skill uses

`<CLI>` below is `dart pub global run event_tracker_setup` (with `fvm` in front when the app uses FVM).
Every command takes the app folder as its argument and changes nothing outside it.

**Reading `--json` output:** when the tool was activated from a local path, pub first prints lines such as
`Resolving dependencies...` on stdout. The JSON starts at the first line that begins with `{`; ignore what comes
before it.

## scan (read-only on code)

`<CLI> scan <app>` prints a summary and writes `<app>/.event_tracker/tracking_plan.json`.
`<CLI> scan <app> --json` prints the plan instead (writes nothing).

Plan fields the skill needs:

| Field | Meaning |
|---|---|
| `state_management`, `router`, `sdk_installed`, `warnings` | what the app uses; warnings (e.g. Riverpod 2) stop `init` |
| `setup.run_app`, `setup.app_widget(_location)`, `setup.go_router` | where init and the screen observer go |
| `setup.existing_init`, `setup.existing_screen_observer` | already set up |
| `screens[]` | widgets that build a Scaffold; tracked automatically by the screen observer |
| `tracked_events[]` | `EventTracker.track('x')` calls already in the app |
| `suggestions[]` | places to track: `id` (`file:line:trigger`), `kind` (tap, submit, change, unnamedRoute, error), `file`, `line`, `event` (proposed name), `priority` (high/medium/low), `category`, `widget`, `label`, `trigger`, `handler`, `screen`, `already_tracked`, `similar_tracked_event`, `reason` |

`already_tracked`: the handler calls EventTracker itself. `similar_tracked_event`: probably sent already, through
the function the handler calls (followed 2 calls deep) or an event with a matching word. Check before choosing.

## select (writes only .event_tracker/selection.json)

`<CLI> select <app> --pick <id>[=<event_name>] [--pick ...] [--add] [--json]`

Replaces the selection (or adds to it with `--add`). `=<event_name>` renames the event (snake_case, letter first,
at most 100 characters, no `$`). Unknown ids, already-tracked places and bad names are refused, nothing saved, exit 1.
The dashboard's "Save selection" writes the same file and keeps the custom names.

## dashboard (local page, runs until stopped)

`<CLI> dashboard <app> [--port 7777] [--no-open] [--host <server>]` serves http://localhost:7777 with tabs
`/#report` (selection), `/#connect` (log in, create a project or key → `<app>/event_tracker.json`, git-ignored)
and `/#live` (events copied by the SDK in debug builds). Prints its URL; stop it with Ctrl+C (or SIGTERM).
Exit 69 when the port is busy.

## init (changes the app; the integrator subagent runs it)

`<CLI> init <app> [--dry-run] [--json] [--id <id> ...] [--sdk-path <dir> | --sdk-git <url> --sdk-ref <ref> | --sdk-version <v>]`

Adds the dependency, `EventTracker.init` before `runApp` (key, host and dev dashboard from dart-defines), the
screen observer, the selected track calls (custom names included), and `event_tracker.json` to `.gitignore`.
`--dry-run --json` returns the same result plus `diffs` (per file, readable before/after hunks) and writes nothing.
Safe to run again. Exit 1 when a warning stopped it (nothing changed), 66 when the folder is not a Flutter app.

Result JSON: `dry_run`, `files_changed`, `changes[]` (`what`, `status`: added / alreadyDone / skipped, `message`),
`warnings`, `next_steps`, `diffs`.
