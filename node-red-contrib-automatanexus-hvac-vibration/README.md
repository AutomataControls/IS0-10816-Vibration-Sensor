# node-red-contrib-automatanexus-hvac-vibration

Professional Industrial Vibration Monitoring for Node-RED by AutomataNexus AI

## Overview

This Node-RED node provides professional-grade parsing and analysis of WitMotion WTVB01-485 vibration sensor data for industrial equipment monitoring. It supports ISO 10816-3 compliance and handles multiple equipment types including cooling towers, pumps, compressors, and more.

## Features

- **ISO 10816-3 Compliant**: Automatic vibration severity classification based on equipment type and power rating
- **Multi-Format Support**: Parses console output, JSON API data, and legacy formats
- **Equipment-Based Configuration**: Define custom settings for each piece of equipment
- **Smart Equipment Detection**: Automatically detects equipment type from naming conventions (v2.1.0+)
- **Real-time Alerts**: Generate warnings and critical alerts based on ISO standards
- **Global Variables**: Optional Node-RED global variable integration for dashboard compatibility
- **Maintenance Predictions**: Estimated remaining useful life based on vibration trends

## What's New in v2.2.0

- Direct integration with multi-port monitoring system API
- Parser trusts monitoring system's configuration instead of overriding it
- Automatic detection of monitoring API JSON format
- Equipment configuration from API is preserved (HP, voltage, phase)

## What's New in v2.1.0

- Support for equipment name-based identification (e.g., "Cooling_Tower_1")
- Auto-detection of equipment type from equipment names
- Better handling of new multi-port monitor output format
- Improved parsing for both sensor addresses and equipment names

## Installation

```bash
npm install node-red-contrib-automatanexus-hvac-vibration
```

Or install directly from Node-RED's palette manager.

## Supported Equipment Types

- Cooling Tower Motors
- Centrifugal Pumps
- Reciprocating Compressors
- Screw Compressors
- Scroll Compressors
- Circulation Pumps
- HVAC Fans
- Blowers
- Generators
- Gearboxes
- General Motors
- And more...

## Input Formats

### Console Output Format (v2.1.0+)
```
[OK] 10:01:35 | Cooling_Tower_1 | RMS: 0.0246g | Velocity: 1.28mm/s | ISO Zone: A | Temp: 77.0°F
```

### JSON API Format (Direct)
```json
{
  "equipment_name": "Cooling_Tower_1",
  "equipment_type": "COOLING_TOWER",
  "temperature_f": 77.0,
  "rms_acceleration": 0.0246,
  "velocity_mms": 1.28,
  "iso_zone": "A",
  "alert_level": "NORMAL"
}
```

### Monitoring API Format (v2.2.0+)
```json
{
  "Cooling_Tower_1": {
    "temperature_f": 77.0,
    "rms_acceleration": 0.0246,
    "velocity_mms": 1.28,
    "iso_zone": "A",
    "alert_level": "NORMAL",
    "hp": 50,
    "voltage": 480,
    "phase": 3
  }
}
```

### Legacy Address Format
```
[OK] Sensor 0x50 | RMS: 0.0156g | Vel: 0.85mm/s | Temp: 75.0°F
```

## Configuration

### Node Properties

- **Output Format**: Standard (full industrial data structure)
- **Global Variables**: Enable/disable global variable setting
- **Global Prefix**: Prefix for global variable names (default: "industrial")
- **Sensor Mappings**: Configure equipment details for each sensor

### Sensor Mapping Configuration

Each sensor can be configured with:
- **Address**: Sensor address (hex or decimal)
- **Name**: Equipment name (e.g., "Cooling_Tower_1")
- **Type**: Equipment type from supported list
- **Location**: Physical location
- **Power (HP)**: Motor horsepower
- **Foundation Type**: rigid or flexible
- **RPM**: Nominal operating RPM
- **Custom Zones**: Override ISO zones if needed

## Output Structure

```javascript
{
  timestamp: "2025-08-02T10:00:00.000Z",
  sensor_address: 80,
  equipment_name: "Cooling_Tower_1",
  equipment_type: "COOLING_TOWER",
  equipment_location: "Rooftop",
  equipment_power: {
    hp: 50,
    kw: 37.3
  },
  equipment_specs: {
    foundation_type: "rigid",
    rpm_nominal: 1800,
    iso_class: "II",
    iso_zones: {A: 1.12, B: 2.8, C: 7.1, D: 11.2}
  },
  temperature: {
    fahrenheit: 77.0,
    celsius: 25.0
  },
  vibration: {
    velocity_mms: 1.28,
    rms_acceleration_g: 0.0246,
    frequency_hz: 30,
    displacement_um: 0
  },
  iso_zone: "A",
  equipment_condition: "EXCELLENT",
  maintenance_priority: "LOW",
  estimated_rul_days: 365,
  alerts: []
}
```

## ISO 10816-3 Classifications

The node automatically determines ISO class based on:
- Equipment power rating (HP/kW)
- Foundation type (rigid/flexible)
- Equipment type specific requirements

### Vibration Zones:
- **Zone A**: Good condition (newly commissioned)
- **Zone B**: Acceptable for long-term operation
- **Zone C**: Unsatisfactory for long-term operation
- **Zone D**: Vibration levels likely to cause damage

## Global Variables

When enabled, sets variables like:
- `industrial_cooling_tower_1_temperature_f`
- `industrial_cooling_tower_1_vibration_velocity`
- `industrial_cooling_tower_1_iso_zone`
- `industrial_cooling_tower_1_condition`
- `industrial_cooling_tower_1_alerts`

## Example Flow

Import the test flow from the package:
```bash
node-red-contrib-automatanexus-hvac-vibration/test-flow.json
```

## Support

For support, feature requests, or bug reports:
- Email: devops@automatacontrols.com
- GitHub: https://github.com/AutomataControls/IS0-10816-Vibration-Sensor

## License

Commercial - (c) 2025 AutomataNexus AI & AutomataControls
