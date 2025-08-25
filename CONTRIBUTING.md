# Contributing to LightWin

If you implement your own :class:`.OptimisationAlgorithm` or add support for some :class:`.Element`, we encourage you to integrate your work in LightWin source code.

---

## 🛠 Development Workflow

We use long-lived branches for each major series (e.g., `1.7.x`).

### TL;DR

- Base your work on the relevant `X.Y.x` branch
- Run `pre-commit` hooks before committing
- Run and write tests
- Submit a **pull request**

### 🧪 Running Tests

The project uses `pytest`. From the root of the repository:

```bash
pytest -m "not implementation"
```

You will need to install development dependencies:

```bash
pip install lightwin -e ".[test]"
```

## 🎯 Pre-commit Hooks

We use [`pre-commit`](https://pre-commit.com) to enforce formatting and static checks.
It should be automatically installed when running `pip install lightwin`.
Set it up as follows:

```bash
pre-commit install
```

This ensures that all required hooks run automatically before each commit.

### Hook configuration

The repository uses the following hooks:

- `black` (code formatting)
- `isort` (import sorting)
- `pyupgrade` (modernize Python syntax)
- Various `pre-commit-hooks` like:
  - `check-docstring-first`
  - `check-merge-conflict`
  - `end-of-file-fixer`
  - `trailing-whitespace`
  - and many more

The full configuration is in `.pre-commit-config.yaml`.

To run all hooks manually:

```bash
pre-commit run --all-files
```

---

## ✨ Contributing Code

1. **Fork** the repository and clone your fork.
2. Create a branch from the appropriate `X.Y.x` branch:

   ```bash
   git checkout -b fix/some-bug 1.7.x
   ```

3. Make your changes.
4. Ensure pre-commit hooks pass.
5. Add tests if applicable.
6. Commit and push:

   ```bash
   git commit -m "Fix: correct bug in XYZ"
   git push origin fix/some-bug
   ```

7. Open a **pull request** into the corresponding `X.Y.x` branch.

---

## 🧾 Changelog and Versioning

Please **add an entry** to `CHANGELOG.md` under the appropriate unreleased version header:

```
## [X.Y.Z]
```

We use [Semantic Versioning](https://semver.org/spec/v2.0.0.html): `MAJOR.MINOR.PATCH`.

---

## 🗣 Questions or Suggestions?

Open an [issue](https://github.com/AdrienPlacais/LightWin/issues) or start a discussion. We're happy to help!

---

Thank you again for contributing 🙏

-- Adrien
