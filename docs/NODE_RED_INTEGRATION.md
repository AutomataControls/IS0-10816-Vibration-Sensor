# Node-RED Integration Guide
## AutomataNexus Vibration Monitor

This guide explains how to integrate the vibration monitoring system with Node-RED for advanced automation and visualization.

## Overview

The vibration monitor provides:
- **SQLite database** storing all sensor metrics
- **7-day automatic data retention**
- **REST API endpoints** for real-time and historical data
- **Custom Node-RED parser** for industrial data processing

## Database Schema

### sensor_metrics table
- Real-time sensor readings
- Stores every reading (1Hz frequency)
- Automatic cleanup after 7 days

### hourly_metrics table  
- Pre-aggregated hourly statistics
- Efficient for trend analysis
- Zone distribution counts

## API Endpoints

### 1. Get Latest Readings
```
GET http://localhost:5000/api/readings
```
Returns current sensor values in real-time.

**Node-RED Function:**
```javascript
msg.url = "http://localhost:5000/api/readings";
msg.method = "GET";
msg.headers = {
  "Accept": "application/json"
};
return msg;
```

### 2. Get Historical Data
```
GET http://localhost:5000/api/metrics/history
```

**Query Parameters:**
- `hours` - Number of hours to retrieve (1-168, default 24)
- `interval` - "raw" or "hourly" (default "hourly")
- `sensor_id` - Specific sensor (optional)

**Node-RED Function:**
```javascript
msg.url = "http://localhost:5000/api/metrics/history";
msg.method = "GET";
msg.payload = {
    hours: 24,
    interval: "hourly",
    sensor_id: "Cooling_Tower_1"  // Optional
};
return msg;
```

### 3. Get Summary Statistics
```
GET http://localhost:5000/api/metrics/summary
```

**Query Parameters:**
- `hours` - Hours to summarize (1-168, default 24)

Returns min/max/avg values and zone distribution percentages.

**Node-RED Function:**
```javascript
msg.url = "http://localhost:5000/api/metrics/summary?hours=24";
msg.method = "GET";
return msg;
```

### 4. Get Alerts
```
GET http://localhost:5000/api/metrics/alerts
```

**Query Parameters:**
- `hours` - Hours to check (1-168, default 24)
- `limit` - Maximum alerts (1-500, default 100)

Returns Zone C and D events only.

## Example Node-RED Flows

### Basic Real-Time Monitoring
```json
[
    {
        "id": "inject-1",
        "type": "inject",
        "repeat": "5",
        "topic": "",
        "x": 150,
        "y": 100,
        "wires": [["http-1"]]
    },
    {
        "id": "http-1",
        "type": "http request",
        "method": "GET",
        "url": "http://localhost:5000/api/readings",
        "x": 350,
        "y": 100,
        "wires": [["parser-1"]]
    },
    {
        "id": "parser-1",
        "type": "automatanexus-industrial-parser",
        "sensors": "3",
        "x": 550,
        "y": 100,
        "wires": [["debug-1"]]
    }
]
```

### Import Complete Examples
1. Copy contents of `node-red-examples.json`
2. In Node-RED: Menu → Import → Clipboard
3. Paste and deploy

## Dashboard Integration

### Create Vibration Gauge
```javascript
// In function node before ui_gauge
let sensor = msg.payload["Cooling_Tower_1"];
if (sensor) {
    msg.payload = sensor.velocity_mms;
    msg.topic = sensor.equipment_name || "Sensor";
    
    // Set color based on ISO zone
    if (sensor.iso_zone === 'A') msg.color = "#10b981";
    else if (sensor.iso_zone === 'B') msg.color = "#3b82f6";
    else if (sensor.iso_zone === 'C') msg.color = "#f97316";
    else msg.color = "#ef4444";
}
return msg;
```

### Create Trend Chart
```javascript
// Process history data for chart
let chartData = [];
if (msg.payload.data) {
    msg.payload.data.forEach(reading => {
        chartData.push({
            x: new Date(reading.timestamp),
            y: reading.avg_velocity,
            series: reading.sensor_id
        });
    });
}
msg.payload = chartData;
return msg;
```

## Alert Automation

### Email on Critical Vibration
```javascript
// After fetching alerts
if (msg.payload.alerts) {
    let critical = msg.payload.alerts.filter(a => a.iso_zone === 'D');
    if (critical.length > 0) {
        msg.topic = "CRITICAL: Vibration Alert";
        msg.payload = `${critical.length} critical vibration events detected:\n\n`;
        
        critical.forEach(alert => {
            msg.payload += `${alert.equipment_name}: ${alert.velocity_mms} mm/s at ${alert.timestamp}\n`;
        });
        
        return msg; // Send to email node
    }
}
```

### MQTT Publishing
```javascript
// Publish sensor data to MQTT
if (msg.payload) {
    Object.entries(msg.payload).forEach(([id, sensor]) => {
        let mqttMsg = {
            topic: `vibration/${id}/status`,
            payload: {
                velocity: sensor.velocity_mms,
                zone: sensor.iso_zone,
                temperature: sensor.temperature_f,
                alert: sensor.alert_level,
                timestamp: sensor.timestamp
            }
        };
        node.send(mqttMsg);
    });
}
```

## Performance Tips

1. **Use Hourly Aggregates** for trends longer than 6 hours
2. **Cache Summary Data** - Update every 5 minutes max
3. **Batch Alert Checks** - Check every 60 seconds
4. **Limit Raw Data** queries to specific sensors

## SQL Query Examples

If you need custom queries, use SQLite node:

### Get Maximum Vibration Last Hour
```sql
SELECT 
    sensor_id,
    MAX(velocity_mms) as max_velocity,
    MAX(rms_acceleration) as max_accel
FROM sensor_metrics
WHERE timestamp > datetime('now', '-1 hour')
GROUP BY sensor_id
```

### Count Alerts by Hour
```sql
SELECT 
    strftime('%Y-%m-%d %H:00', timestamp) as hour,
    sensor_id,
    COUNT(*) as alert_count
FROM sensor_metrics
WHERE iso_zone IN ('C', 'D')
AND timestamp > datetime('now', '-24 hours')
GROUP BY hour, sensor_id
ORDER BY hour DESC
```

### Equipment Health Score
```sql
SELECT 
    sensor_id,
    equipment_name,
    ROUND(
        (COUNT(CASE WHEN iso_zone = 'A' THEN 1 END) * 100.0) / COUNT(*), 
        1
    ) as health_score
FROM sensor_metrics
WHERE timestamp > datetime('now', '-24 hours')
GROUP BY sensor_id
```

## Troubleshooting

### No Data Returned
- Check monitoring service: `sudo systemctl status vibration-monitor`
- Verify sensors configured and monitoring started
- Check database exists: `/opt/automatanexus/IS0-10816-Vibration-Sensor/vibration_metrics.db`

### Parser Node Not Working
- Ensure using latest parser version 2.2.0
- Check Node-RED logs for errors
- Verify data format matches expected structure

### Database Growing Too Large
- Automatic cleanup runs daily
- Manual cleanup: `DELETE FROM sensor_metrics WHERE timestamp < datetime('now', '-7 days')`
- Check disk space: `df -h`

## Advanced Integration

### Predictive Maintenance
Use historical data to predict failures:
1. Query zone distribution trends
2. Calculate degradation rate
3. Alert when approaching critical thresholds

### Integration with Other Systems
- Export to InfluxDB for long-term storage
- Send to cloud analytics platforms
- Integrate with CMMS systems
- Trigger work orders automatically

## Support

For issues or questions about Node-RED integration:
- Check Node-RED logs: `node-red-log`
- Monitor API responses in debug nodes
- Verify network connectivity to port 5000

© 2025 AutomataNexus AI