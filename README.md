# Habit Tracker Integration for Home Assistant

A custom Home Assistant integration for tracking daily habits with a weekly grid view, statistics, and support for multiple people.

## Features

- **Weekly Grid View**: Track habits across the days of the week (Mon-Sun)
- **Multiple People**: Create separate habit trackers for each household member
- **Statistics**: Automatic tracking of completion rate and total days completed
- **Easy Habit Management**: Add/remove habits via services or automations
- **Persistent Storage**: All data saved to JSON files

## Installation

1. Copy the `custom_components/habit_tracker` folder to your Home Assistant `config/custom_components/` directory:

```bash
cp -r custom_components/habit_tracker /path/to/homeassistant/config/custom_components/
```

2. Restart Home Assistant

3. Add a new Habit Tracker instance via **Settings → Devices & Services → Add Integration → Habit Tracker**

## Configuration

### Adding via UI

1. Go to **Settings → Devices & Services**
2. Click **Add Integration**
3. Search for "Habit Tracker"
4. Enter a name (e.g., "John", "Family")
5. Optionally specify a custom data file name

### YAML Configuration (Optional)

No YAML configuration is required. The integration is fully UI-configurable. However, you can use services in automations:

```yaml
# Example automation to add habits on first setup
automation:
  - alias: "Add initial habits"
    trigger:
      - platform: homeassistant
        event: start
    action:
      - service: habit_tracker.add_habit
        data:
          habit_id: exercise
          habit_name: Exercise
      - service: habit_tracker.add_habit
        data:
          habit_id: reading
          habit_name: Reading
        target:
          entity_id: button.habit_tracker_john_add_habit  # Use your person's button entity
```

## Entities Created

For each habit tracker instance (person), the integration creates:

| Entity Type | Entity ID Pattern | Description |
|------------|-------------------|-------------|
| Button | `button.habit_tracker_{person}_add_habit` | Click to trigger add-habit flow |
| Binary Sensor | `binary_sensor.habit_tracker_{person}_{habit}` | Toggle habit completion for today |
| Sensor | `sensor.habit_tracker_{person}_{habit}_total` | Total days completed |
| Sensor | `sensor.habit_tracker_{person}_{habit}_rate` | Completion rate (%) |

## Services

### `habit_tracker.add_habit`

Add a new habit to track.

```yaml
service: habit_tracker.add_habit
data:
  habit_id: meditation      # Unique ID (lowercase, underscores)
  habit_name: Meditation    # Display name
target:
  entity_id: button.habit_tracker_john_add_habit
```

### `habit_tracker.remove_habit`

Remove a habit from tracking.

```yaml
service: habit_tracker.remove_habit
data:
  habit_id: meditation
target:
  entity_id: button.habit_tracker_john_add_habit
```

### `habit_tracker.set_completion`

Set or unset completion for a habit on a specific date.

```yaml
service: habit_tracker.set_completion
data:
  habit_id: exercise
  date: "2024-01-15"
  completed: true
target:
  entity_id: button.habit_tracker_john_add_habit
```

### `habit_tracker.reset_week`

Uncheck all habits for the current week.

```yaml
service: habit_tracker.reset_week
target:
  entity_id: button.habit_tracker_john_add_habit
```

## Home Assistant Dashboard Examples

### Grid View Card (Manual)

Use a markdown card to display the weekly grid using templates:

```yaml
type: entities
title: John's Habits
entities:
  - binary_sensor.habit_tracker_john_exercise
  - binary_sensor.habit_tracker_john_reading
  - binary_sensor.habit_tracker_john_meditation
```

### Statistics Card

```yaml
type: entities
title: John's Stats
entities:
  - sensor.habit_tracker_john_exercise_total
  - sensor.habit_tracker_john_exercise_rate
  - sensor.habit_tracker_john_reading_total
  - sensor.habit_tracker_john_reading_rate
```

### Multi-Person Dashboard

```yaml
type: vertical-stack
cards:
  - type: entities
    title: John's Habits
    entities:
      - binary_sensor.habit_tracker_john_exercise
      - binary_sensor.habit_tracker_john_reading
      - binary_sensor.habit_tracker_john_meditation
  - type: entities
    title: Sarah's Habits
    entities:
      - binary_sensor.habit_tracker_sarah_exercise
      - binary_sensor.habit_tracker_sarah_yoga
```

### Lovelace Card with Custom Buttons

Use the [button-card](https://github.com/custom-cards/button-card) custom card for a beautiful grid:

```yaml
type: custom:button-card
template: habit_grid
entities:
  - binary_sensor.habit_tracker_john_exercise
  - binary_sensor.habit_tracker_john_reading
  - binary_sensor.habit_tracker_john_meditation
```

## Automations

### Daily Reminder

```yaml
automation:
  - alias: "Evening habit reminder"
    trigger:
      - platform: time
        at: "20:00:00"
    action:
      - service: persistent_notification.create
        data:
          title: "Time to log your habits!"
          message: >
            Don't forget to check off today's completed habits!
```

### Auto-uncheck past days (optional)

```yaml
automation:
  - alias: "Reset past week on Monday"
    trigger:
      - platform: time
        at: "00:01:00"
    condition:
      - platform: numeric_state
        entity_id: sensor.date
        attribute: weekday
        above: 0  # Not Sunday
    action:
      - service: habit_tracker.reset_week
        target:
          entity_id: button.habit_tracker_john_add_habit
```

## Data Storage

All habit data is stored as JSON files in Home Assistant's `.storage` directory:

```
.config/.storage/habit_tracker_{entry_id}.json
```

Example data structure:

```json
{
  "people": {
    "a1b2c3d4e5f6...": {
      "name": "John",
      "habits": [
        {
          "id": "exercise",
          "name": "Exercise",
          "completions": {
            "2024-01-15": true,
            "2024-01-16": false,
            "2024-01-17": true
          }
        }
      ]
    }
  }
}
```

## Multiple People Setup

1. Add the first Habit Tracker instance (e.g., name it "John")
2. Add a second instance (name it "Sarah")
3. Each instance has its own set of habits and data
4. Use separate buttons to add/remove habits per person

The service calls target the specific person's button entity:

```yaml
# Add habit for John
service: habit_tracker.add_habit
data:
  habit_id: running
  habit_name: Running
target:
  entity_id: button.habit_tracker_john_add_habit

# Add habit for Sarah  
service: habit_tracker.add_habit
data:
  habit_id: yoga
  habit_name: Yoga
target:
  entity_id: button.habit_tracker_sarah_add_habit
```

## Development

To develop this integration:

1. Place the `habit_tracker` folder in your HA `config/custom_components/` directory
2. Restart Home Assistant
3. Make changes and reload the integration

## License

MIT
