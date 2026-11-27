# Contributing

Issues and pull requests are welcome. For a large change, open an issue first.

## Development

```bash
./run.sh test    # pytest            (or make test)
./run.sh check   # ruff and mypy     (or make check)
./run.sh demo    # draws the invented weekend
```

`run.sh` installs [uv](https://docs.astral.sh/uv/) if it is missing. On Windows: `make test` and `make check`.

- `run.sh` and `ACC-Race-Stats.command` are POSIX `sh` (`dash -n run.sh` checks it) and must stay executable.

- Code, comments and documentation are in English. `README.pt-BR.md` mirrors `README.md`: change both. Text for users goes in `messages.py` (questions and errors) or
  `i18n.py` (charts), in English and Portuguese.
- Every fix comes with a test. Tests use invented data only: no real drivers, player ids, addresses or passwords.
- Look at the charts you change, with categories and with `--divisions none`.

## Commits

[Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/): `<type>[optional scope][!]: <description>`

| Type | Use |
|---|---|
| `feat` | new feature |
| `fix` | bug fix |
| `docs`, `refactor`, `perf`, `test`, `build`, `ci`, `style`, `chore`, `revert` | the rest |

Types are lowercase, one logical change per commit. A breaking change has `!` before the colon or a
`BREAKING CHANGE:` footer. The CI checks the commits of pull requests.

## Versions

[Semantic Versioning](https://semver.org). **The maintainer chooses every version**; nothing is bumped automatically.
Before 1.0.0, a minor version may have breaking changes.

To release, the maintainer:

1. sets the version in `pyproject.toml` and `src/acc_race_stats/__init__.py`, and runs `uv lock`;
2. moves the entries of `CHANGELOG.md` to the new version;
3. commits `chore(release): X.Y.Z` and pushes the tag `vX.Y.Z`.

The release workflow checks that the tag and the version match, runs the tests and publishes the packages on GitHub.

## Logos

`tools/build_logos.py` draws the logos from [Simple Icons](https://simpleicons.org) files. Do not add artwork from other
sources.
