# Habit Tracker for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![HACS Default][hacs-badge]][hacs]
[![GitHub Workflow Status][action-badge]][action]
[![License][license-badge]][license]

A Home Assistant custom integration for tracking daily habits with a weekly grid view, per-person trackers, and completion statistics.

![Screenshot](https://raw.githubusercontent.com/Cynopolis/HASS-Habit-Tracker/main/docs/screenshot.png)

## Features

- **Weekly Grid View** — Track habits across Mon–Sun with toggle buttons
- **Multiple People** — Create separate habit trackers for each household member
- **Automatic Statistics** — Tracks total completions and completion rate (%) per habit
- **Persistent Storage** — All data saved to JSON, survives restarts
- **UI-Based Configuration** — Add/remove habits directly in the integration settings

## Installation

### Via HACS (Recommended)

Have [HACS](https://hacs.xyz/) installed, this will allow you to update easily.

Adding Habit Tracker for Home Assistant to HACS can be done using this button:

[![Add to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Cynopolis&repository=HASS-Habit-Tracker&category=integration)

> [!NOTE]
> If the button above doesn't work, add `https://github.com/Cynopolis/HASS-Habit-Tracker` as a custom repository of type **Integration** in HACS.

* Click **Download** on the **Habit Tracker** integration.
* Restart Home Assistant.

### Manual Installation

1. Using the [configurator](https://github.com/hassio-addons/addon-configurator) add-on, or by manually copying files:
2. Copy the `custom_components/habit_tracker/` folder into your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant

## Setup

### 1. Add a Person

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Habit Tracker**
3. Enter a name (e.g., "John", "Sarah")
4. Click **Submit**

### 2. Configure Habits

After adding a person, configure their habits:

1. Go to **Settings → Devices & Services**
2. Find your Habit Tracker instance and click **Configure**
3. Choose **Add Habit** or **Remove Habit**
4. For new habits, enter:
   - **Habit ID**: lowercase with underscores (e.g., `exercise`, `morning_reading`)
   - **Display Name**: human-readable name (e.g., "Exercise", "Morning Reading")

### 3. Repeat for Additional People

Repeat steps 1–2 for each household member.

## Usage

### Toggling Completion

Tap any binary sensor entity in the UI to toggle completion for today.

Or use the service:

```yaml
service: habit_tracker.set_completion
data:
  habit_id: exercise
  date: "2024-01-15"
  completed: true
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

| Entity                                         | Type          | Description                 |
| ---------------------------------------------- | ------------- | --------------------------- |
| `button.habit_tracker_{person}_add_habit`      | Button        | Service trigger (always present) |
| `binary_sensor.habit_tracker_{person}_{habit}` | Binary Sensor | Toggle completion for today |
| `sensor.habit_tracker_{person}_{habit}_total`  | Sensor        | Total days completed        |
| `sensor.habit_tracker_{person}_{habit}_rate`   | Sensor        | Completion rate (%)         |

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

## Services Reference (Advanced)

Services are available for automations and scripts:

| Service                        | Description                  | Required Data                   |
| ------------------------------ | ---------------------------- | ------------------------------- |
| `habit_tracker.add_habit`      | Add a new habit              | `habit_id`, `habit_name`        |
| `habit_tracker.remove_habit`   | Remove a habit               | `habit_id`                      |
| `habit_tracker.set_completion` | Set completion for a date    | `habit_id`, `date`, `completed` |
| `habit_tracker.reset_week`     | Uncheck all habits this week | —                               |

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
[releases-shield]: https://img.shields.io/github/v/release/Cynopolis/HASS-Habit-Tracker?style=for-the-badge&color=blue
[releases]: https://github.com/Cynopolis/HASS-Habit-Tracker/releases
[action-badge]: https://img.shields.io/github/actions/workflow/status/Cynopolis/HASS-Habit-Tracker/ci.yml?branch=main&style=for-the-badge
[action]: https://github.com/Cynopolis/HASS-Habit-Tracker/actions
[license-badge]: https://img.shields.io/github/license/Cynopolis/HASS-Habit-Tracker?style=for-the-badge
[license]: LICENSE
