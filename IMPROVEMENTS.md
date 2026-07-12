# IMPROVEMENTS.md

*Analysis date: 2026-07-11*

This repo tracks the history of the Chatbot Arena ("botarena") Elo leaderboard by
downloading every historical revision of the Hugging Face dataset
`mathewhe/chatbot-arena-elo` (`download.py`) and inspecting the resulting Arrow
files (`arrowreader.py`). It is at proof-of-concept stage: two commits, dated
April 2025, with uncommitted edits to `download.py`/`pyproject.toml` and an
untracked `arrowreader.py` sitting in the working tree since then. The
project downloads data but does no actual Elo *tracking* yet — there is no
analysis, time-series extraction, or visualization.

## Bugs & Fixes

- **`download.py` never saves anything useful.** It calls
  `load_dataset(..., cache_dir=version_dir)` per commit, so each version lands
  as an opaque HF cache tree (hashes, lockfiles, duplicated metadata) rather
  than a clean per-revision snapshot. Prefer
  `dataset_at_revision["train"].to_pandas().to_parquet(version_dir / "elo.parquet")`
  (or `snapshot_download(revision=...)`) so downstream code doesn't need to
  spelunk cache directories with `arrowreader.py`.
- **No incrementality.** Every run re-downloads all revisions. Skip commits
  whose output directory/file already exists — the commit hash makes this a
  one-line check.
- **Silent failure swallowing.** The per-commit `except` logs and (with the
  commented-out `continue`) falls through; failed revisions leave partial
  directories. Decide: retry, record failures to a manifest, or delete the
  partial dir.
- **Dead code / unfinished decisions in `download.py`:** `datetime` is
  imported but unused, `HfApi` is imported but unused, and the
  `commits_sorted` / `commits_raw[::-1]` option block is three commented
  alternatives with no decision. Pick one ordering (oldest-first is the
  natural choice for time-series building) and delete the rest.

## Improvements (the actual point of the project)

- **Build the Elo time series.** Add a script (e.g. `build_timeseries.py`)
  that walks the per-commit snapshots, extracts `(commit_date, model, elo)`
  rows, and writes one tidy long-format Parquet/CSV. That is the deliverable
  the repo name promises; everything else is plumbing.
- **Add plotting/reporting** — e.g. Elo trajectories for selected models over
  time, model entry/exit dates, rank churn. Even a single matplotlib chart or
  an HTML page would make the dataset consumable.
- **Parameterize `download.py`** (argparse: `--repo-id`, `--output-dir`,
  `--limit`) instead of hard-coded module-level constants, and wrap the logic
  in a `main()` guard.
- **Cron-ability:** if the goal is ongoing tracking, add a mode that fetches
  only commits newer than the latest local snapshot, suitable for a scheduled
  run.

## Testing

- No tests exist. Minimal worthwhile coverage: a unit test for the
  snapshot-extraction/parsing logic (feed it a tiny fixture Arrow/Parquet
  file), and a test that the "skip already-downloaded revision" logic works.
  Network-touching download paths can stay untested or be mocked.

## Documentation

- `README.md` is one wry sentence. Add: what the scripts do, how to run them
  (`uv run download.py`, `uv run arrowreader.py --arrow-file ...`), where data
  lands, and roughly how much disk the full history consumes.
- Fix `pyproject.toml`'s placeholder `description = "Add your description
  here"`.

## Housekeeping

- **Commit or discard the dirty working tree.** `download.py`,
  `pyproject.toml`, `uv.lock`, and `.gitignore` have been modified-but-
  uncommitted since April 2025, and `arrowreader.py` is untracked. Commit the
  good state; these edits are one hard-drive failure away from vanishing.
- **Don't commit the data.** `chatbot_arena_elo_versions/` (36 revision dirs)
  is untracked; add it to `.gitignore` explicitly so it can never be staged by
  accident.
- **Delete editor droppings:** `arrowreader.py~` and `download.py~` — add
  `*~` to `.gitignore`.
- Tooling is already correct for this owner's preferences: uv with
  `pyproject.toml` + `uv.lock`, no `requirements.txt`. Keep it that way; run
  scripts as `uv run download.py`.
- Shebang nit: `#!/usr/bin/env uv run` relies on multi-argument shebang
  support (fine on macOS, not portable to Linux). If the scripts ever run on
  raksasa, use `#!/usr/bin/env -S uv run`.

## Security

- No secrets found in the repo. `list_repo_commits`/`load_dataset` hit a
  public dataset anonymously; if a token is ever needed, keep it in
  `HUGGING_FACE_HUB_TOKEN`, never in code.

## Quick Wins

1. `git add download.py arrowreader.py pyproject.toml uv.lock .gitignore && git commit` — bank the 15 months of uncommitted work.
2. Remove `*~` backup files and ignore them.
3. Delete the unused `datetime`/`HfApi` imports and the commented ordering block.
4. Real `pyproject.toml` description + three-paragraph README.
5. Skip-if-exists check in the download loop.
