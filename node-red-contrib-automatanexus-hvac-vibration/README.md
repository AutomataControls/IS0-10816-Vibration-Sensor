# AutomataNexus HVAC Controls - Vibration Monitoring

Professional Node-RED integration for HVAC motor vibration monitoring and predictive maintenance.

## Features

- **ISO 10816 Compliance** - Motor condition classification
- **HVAC-Specific** - AHU fans, chillers, pumps, cooling towers
- **Energy Efficiency** - Performance impact monitoring
- **Global Variables** - Node-RED dashboard integration
- **Building Automation** - MQTT, OPC-UA outputs

## Installation

```bash
npm install node-red-contrib-automatanexus-hvac-vibration
```

## Usage

1. Drag the "HVAC Vibration Monitor" node into your flow
2. Connect to your vibration data source
3. Configure HVAC settings
4. Use global variables in dashboards

## Global Variables

- `hvac_motor_{ID}_temperature_f` - Temperature (°F)
- `hvac_motor_{ID}_vibration_velocity` - Velocity (mm/s)
- `hvac_motor_{ID}_hvac_motor_type` - Equipment type
- `hvac_motor_{ID}_energy_efficiency` - Efficiency rating

## License

Commercial - (c) 2025 AutomataNexus AI & AutomataControls
