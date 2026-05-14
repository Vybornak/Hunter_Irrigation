# Repository Instructions

## Release Flow
- Bump `custom_components/hunter_irrigation/manifest.json` version first.
- Add a matching entry to `CHANGELOG.md` under `## [Nevydáno]` or a new version heading.
- Commit with a release message like `Release 1.0.26`.
- Create the matching git tag for the release version.
- Push the branch and the tag to `origin`.
- Create the GitHub Release from the tag using `gh release create` and the changelog notes.
- Do not force-update an already published release tag; if a published release needs a fix, cut a new patch version instead.

## GitHub CLI
- If `gh` is not visible in PATH, use `C:\Program Files\GitHub CLI\gh.exe` directly.
- Keep `gh` authenticated with the repository owner account before release work.

## Dashboard Notes
- Keep `examples/dashboard_modern.yaml` aligned with verified entities in `entities.txt`.
- Prefer showing the next cycle information near the top of the dashboard, not duplicated in badges.
