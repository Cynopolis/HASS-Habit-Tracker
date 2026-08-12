# Agent Guidelines — Habit Tracker for Home Assistant

This file captures key learnings, conventions, and constraints discovered during development of this HACS custom integration. Future agents should read and follow these guidelines.

---

## Branch Protection & Commit Practices

- Check which branch you're on before making a commit. If you're on main or develop stop and ask the user what to do.
- **Never commit directly to `main` or `develop`** — branch protection rules block this
- Always create a feature branch: `git checkout -b <feature-name> develop`
- Push branches yourself only when explicitly asked — **never auto-push**

### Branch Naming Convention

```
add-<feature-name>   # e.g., add-release-workflow, add-add-to-hacs-button
fix-<issue>          # e.g., fix-import-ordering
```

### Commit Message Format

```
<type>: <subject>

- bullet points for details
- keep subject under 72 chars
```

Types: `feat`, `fix`, `docs`, `refactor`, `chore`

---

## Repository Structure

```
habit-tracker/
├── .github/workflows/
│   ├── ci.yml            # CI pipeline (JSON, compile, lint, schema, structure)
│   └── release.yml       # Release pipeline (version bump + ZIP upload)
├── custom_components/
│   └── habit_tracker/    # ← domain name must match manifest.json "domain"
│       ├── __init__.py
│       ├── const.py
│       ├── config_flow.py
│       ├── data_manager.py
│       ├── binary_sensor.py  # daily habit toggles + week_grid attributes
│       ├── button.py         # add_habit service button
│       ├── sensor.py         # completion rate & total sensors
│       ├── manifest.json     # version, domain, config_flow: true
│       ├── strings.json      # translation keys
│       └── translations/
│           └── en.json       # English translations
├── hacs.json               # HACS metadata (name, version, homeassistant min)
├── README.md               # Rendered in HACS UI — includes "Add to HACS" button
├── .ruff.toml              # Ruff lint/format config
├── .gitignore
└── LICENSE
```

### Key Naming Rules

- Domain name (`habit_tracker`) must match the folder name under `custom_components/`
- Entity IDs follow pattern: `binary_sensor.habit_tracker_{person}_{habit}`
- Service calls target: `button.habit_tracker_{person}_add_habit`

---

## CI/CD Pipelines

### CI Workflow (`.github/workflows/ci.yml`)

Triggers on push/PR to **both** `main` and `develop`:

| Job          | Tool                                 | What it checks                                             |
| ------------ | ------------------------------------ | ---------------------------------------------------------- |
| `json`       | `python3 -m json.tool`               | All `.json` files parse correctly                          |
| `py_compile` | `python3 -m py_compile`              | All `.py` files compile (Python 3.12 + 3.13)               |
| `lint`       | `ruff check` + `ruff format --check` | Code style, unused imports, formatting                     |
| `schema`     | Custom Python                        | manifest.json has required fields; domain matches dir name |
| `structure`  | Bash file checks                     | All required HA integration files exist                    |

### Release Workflow (`.github/workflows/release.yml`)

Triggers on push to **`main`** only (or manual dispatch):

1. Reads version from `custom_components/habit_tracker/manifest.json`
2. Checks if release `v{version}` already exists (idempotent)
3. Creates ZIP of `custom_components/habit_tracker/`
4. Creates GitHub Release with auto-generated notes + ZIP asset

---

## HACS Deployment

### hacs.json Requirements

- `name` — displayed in HACS UI
- `homeassistant` — minimum HA version (e.g., `"2024.11.0"`)
- `render_readme: true` — shows README.md in HACS details page

### manifest.json Requirements

- `domain` — must match folder name exactly
- `name` — displayed in HA UI
- `version` — bumped before each release
- `config_flow: true` — enables UI-based setup
- `codeowners` — recommended for config flows

---

## Python Code Conventions (Ruff)

Configured in `.ruff.toml`:

```toml
line-length = 88
target-version = "py312"

[lint]
select = ["E", "F", "I001", "W"]
ignore = ["E501"]  # ruff handles line length itself

[format]
quote-style = "double"
indent-style = "space"
```

Key rules enforced:

- **I001**: Import sorting (isort style)
- **F401**: Unused imports → remove them
- **F821**: Undefined names → fix typos in variable references
- **f-string**: No `f"string with no placeholders"` — remove the `f`
- **Trailing whitespace**: Trim blank lines

Run locally:

```bash
ruff check ./custom_components/   # lint
ruff format ./custom_components/  # auto-format
```

---

## Entity Design Patterns

### binary_sensor — Daily Habit Toggle

Each day of the week is a `binary_sensor` with:

- `extra_state_attributes.week_grid` — dict of `{date_str: bool}` for all 7 days
- Toggling one sensor updates the grid and triggers stats recalculation

### sensor — Statistics

Two sensors per habit:

- `*_total` — count of completed days this week
- `*_rate` — completion percentage (0–100)

### button — Service Trigger

One button per person instance:

- Triggers `add_habit`, `remove_habit`, `set_completion`, `reset_week` services

---

## Data Persistence

All habit data is stored via Home Assistant's `storage` system in `.storage/`:

```
.config/.storage/habit_tracker_{entry_id}.json
```

The `DataManager` class handles:

- Reading/writing JSON on service calls
- Loading state on integration setup
- Graceful fallback to empty dict if file is missing/corrupt

---

## Common Pitfalls (Learned During Development)

1. **Import ordering** — Ruff's I001 catches unsorted imports; use `ruff check --fix` or `ruff format`
2. **Unused imports** — `F401` errors are common when refactoring; run `ruff check` after every change
3. **Undefined variable typos** — e.g., `self._instance_name = name` when the param is `instance_name`; always verify variable names match
4. **f-strings without placeholders** — `f"Add New Habit"` → `"Add New Habit"` (the `f` prefix is unnecessary)
5. **Domain mismatch** — manifest `domain` must exactly match the folder name under `custom_components/`
6. **Release idempotency** — always check if release exists before creating; otherwise CI runs on every push will fail

---

## Testing Checklist Before Pushing

Run this locally before asking to push:

```bash
# 1. JSON validation
find . -name '*.json' -not -path './.git/*' -exec python3 -m json.tool {} \; > /dev/null

# 2. Python compilation
find ./custom_components -name '*.py' -not -path '*/__pycache__/*' -exec python3 -m py_compile {} \;

# 3. Ruff lint + format
ruff check ./custom_components/
ruff format --check ./custom_components/

# 4. YAML validation (for workflow files)
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml'))"
```

---

## Repository Info

- **Owner**: Cynopolis
- **Repo**: HASS-Habit-Tracker
- **URL**: https://github.com/Cynopolis/HASS-Habit-Tracker
- **HACS category**: Integration
- **Minimum HA version**: 2024.11.0
