# Habit Tracker for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![HACS Default][hacs-badge]][hacs]
[![GitHub Workflow Status][action-badge]][action]
[![License][license-badge]][license]

A Home Assistant custom integration for tracking daily habits with a weekly grid view, per-person trackers, and completion statistics.

![Screenshot](https://raw.githubusercontent.com/example/habit-tracker-ha/main/docs/screenshot.png)

## Features

- **Weekly Grid View** — Track habits across Mon–Sun with toggle buttons
- **Multiple People** — Create separate habit trackers for each household member
- **Automatic Statistics** — Tracks total completions and completion rate (%) per habit
- **Persistent Storage** — All data saved to JSON, survives restarts
- **Service-Based** — Add, remove, set completions, and reset weeks via services

## Installation

### Via HACS (Recommended)

1. Open **HACS** → **Integrations**
2. Click the **⋮** menu → **Custom repositories**
3. Set repository URL to `https://github.com/example/habit-tracker-ha`
4. Category: **Integration**
5. Click **Add**
6. Find **Habit Tracker** in the list and click **Download**
7. Restart Home Assistant

### Manual Installation

1. Using the [configurator](https://github.com/hassio-addons/addon-configurator) add-on, or by manually copying files:
2. Copy the `custom_components/habit_tracker/` folder into your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant

## Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Habit Tracker**
3. Enter a name (e.g., "John", "Sarah")
4. Click **Submit**
5. Repeat for additional people

## Usage

### Adding Habits

Use the service `habit_tracker.add_habit`:

```yaml
service: habit_tracker.add_habit
data:
  habit_id: exercise
  habit_name: Exercise
target:
  entity_id: button.habit_tracker_john_add_habit
```

### Toggling Completion

Tap any binary sensor entity in the UI to toggle completion for today. Or use the service:

```yaml
service: habit_tracker.set_completion
data:
  habit_id: exercise
  date: "2024-01-15"
  completed: true
target:
  entity_id: button.habit_tracker_john_add_habit
```

### Removing Habits

```yaml
service: habit_tracker.remove_habit
data:
  habit_id: exercise
target:
  entity_id: button.habit_tracker_john_add_habit
```

### Resetting the Week

```yaml
service: habit_tracker.reset_week
target:
  entity_id: button.habit_tracker_john_add_habit
```

## Entities Created Per Person

| Entity | Type | Description |
|--------|------|-------------|
| `button.habit_tracker_{person}_add_habit` | Button | Trigger to add new habits |
| `binary_sensor.habit_tracker_{person}_{habit}` | Binary Sensor | Toggle completion for today |
| `sensor.habit_tracker_{person}_{habit}_total` | Sensor | Total days completed |
| `sensor.habit_tracker_{person}_{habit}_rate` | Sensor | Completion rate (%) |

## Example Dashboard

```yaml
type: entities
title: John's Habits
entities:
  - entity: binary_sensor.habit_tracker_john_exercise
    name: Exercise
  - entity: binary_sensor.habit_tracker_john_reading
    name: Reading
  - entity: sensor.habit_tracker_john_exercise_rate
    name: Exercise Rate
```

## Services Reference

| Service | Description | Required Data |
|---------|-------------|---------------|
| `habit_tracker.add_habit` | Add a new habit | `habit_id`, `habit_name` |
| `habit_tracker.remove_habit` | Remove a habit | `habit_id` |
| `habit_tracker.set_completion` | Set completion for a date | `habit_id`, `date`, `completed` |
| `habit_tracker.reset_week` | Uncheck all habits this week | — |

## Data Storage

All data is stored in Home Assistant's `.storage` directory as JSON:

```
.config/.storage/habit_tracker_{entry_id}.json
```

## License

MIT License — See [LICENSE](LICENSE) for details.

---

**Icons used**: [Material Design Icons](https://materialdesignicons.com/) by Austin Andrews (SIL OFL 1.1)

[hacs-badge]: https://img.shields.io/badge/HACS-Default-orange.svg?logo=HomeAssistantCommunityStore&logoColor=white
[hacs]: https://hacs.xyz
[releases-shield]: https://img.shields.io/github/v/release/example/habit-tracker-ha?style=for-the-badge&color=blue
[releases]: https://github.com/example/habit-tracker-ha/releases
[action-badge]: https://img.shields.io/github/actions/workflow/status/example/habit-tracker-ha/ci.yml?branch=main&style=for-the-badge
[action]: https://github.com/example/habit-tracker-ha/actions
[license-badge]: https://img.shields.io/github/license/example/habit-tracker-ha?style=for-the-badge
[license]: LICENSE
