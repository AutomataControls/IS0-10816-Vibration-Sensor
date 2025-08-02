/**
 * AutomataNexus HVAC Controls - Vibration Monitoring
 * Professional WitMotion WT901C-485 Integration for HVAC Systems
 * (c) 2025 AutomataNexus AI & AutomataControls
 */

module.exports = function(RED) {
    "use strict";
    
    function HVACVibrationParserNode(config) {
        RED.nodes.createNode(this, config);
        var node = this;
        
        // Configuration
        node.outputFormat = config.outputFormat || "standard";
        node.globalVars = config.globalVars !== false;
        node.hvacPrefix = config.hvacPrefix || "hvac_motor";
        
        // Statistics
        node.messageCount = 0;
        node.lastUpdate = null;
        
        // Node status
        node.status({fill: "blue", shape: "dot", text: "HVAC Ready"});
        
        // Process incoming messages
        node.on('input', function(msg, send, done) {
            send = send || function() { node.send.apply(node, arguments); };
            
            try {
                let parsedData = parseHVACData(msg.payload);
                
                if (parsedData) {
                    node.messageCount++;
                    node.lastUpdate = new Date();
                    
                    // Set global variables
                    if (node.globalVars) {
                        setHVACGlobals(parsedData);
                    }
                    
                    // Update status
                    updateStatus(parsedData);
                    
                    // Send output
                    send([{
                        payload: parsedData,
                        topic: `automatanexus/hvac/motor_${parsedData.motor_id}`,
                        motor_id: parsedData.motor_id,
                        hvac_type: parsedData.hvac_motor_type,
                        iso_zone: parsedData.iso_zone
                    }]);
                    
                    if (done) done();
                } else {
                    node.warn("Failed to parse HVAC data");
                    if (done) done();
                }
                
            } catch (error) {
                node.error("HVAC Parser Error: " + error.message, msg);
                node.status({fill: "red", shape: "ring", text: "Error"});
                if (done) done(error);
            }
        });
        
        // Parse HVAC data
        function parseHVACData(payload) {
            let data = {};
            
            try {
                if (typeof payload === 'string') {
                    // Parse console output
                    if (payload.includes('[OK]') || payload.includes('[WARN]') || 
                        payload.includes('[CRIT]') || payload.includes('[EMRG]')) {
                        data = parseConsoleOutput(payload);
                    } else {
                        data = JSON.parse(payload);
                    }
                } else if (typeof payload === 'object') {
                    data = payload;
                }
                
                return standardizeHVACData(data);
                
            } catch (error) {
                return null;
            }
        }
        
        // Parse console output
        function parseConsoleOutput(text) {
            let data = {};
            
            // Extract alert level
            let alertMatch = text.match(/\[(OK|WARN|CRIT|EMRG)\]/);
            if (alertMatch) data.alert_level = alertMatch[1];
            
            // Extract motor ID
            let motorMatch = text.match(/Motor 0x([0-9A-F]+)/);
            if (motorMatch) data.motor_id = parseInt(motorMatch[1], 16);
            
            // Extract temperature
            let tempMatch = text.match(/Temp: ([+-]?\d+\.\d+)°F/);
            if (tempMatch) data.temperature_f = parseFloat(tempMatch[1]);
            
            // Extract vibration velocity
            let velMatch = text.match(/Vel: ([+-]?\d+\.\d+)mm\/s/);
            if (velMatch) data.vibration_velocity = parseFloat(velMatch[1]);
            
            // Extract RMS acceleration
            let rmsMatch = text.match(/RMS: ([+-]?\d+\.\d+)g/);
            if (rmsMatch) data.rms_acceleration = parseFloat(rmsMatch[1]);
            
            return data;
        }
        
        // Standardize HVAC data
        function standardizeHVACData(rawData) {
            if (!rawData) return null;
            
            let hvacData = {
                timestamp: new Date().toISOString(),
                motor_id: rawData.motor_id || 0,
                hvac_motor_type: getHVACMotorType(rawData.motor_id),
                hvac_zone: getHVACZone(rawData.motor_id),
                
                temperature: {
                    fahrenheit: rawData.temperature_f || 70,
                    celsius: 0
                },
                
                vibration: {
                    velocity_mms: rawData.vibration_velocity || 0,
                    rms_acceleration_g: rawData.rms_acceleration || 0
                },
                
                alert_level: rawData.alert_level || "NORMAL",
                iso_zone: "",
                motor_condition: "",
                energy_efficiency: 95
            };
            
            // Calculate celsius
            hvacData.temperature.celsius = (hvacData.temperature.fahrenheit - 32) * 5.0 / 9.0;
            
            // ISO 10816 classification
            let velocity = hvacData.vibration.velocity_mms;
            if (velocity < 1.8) {
                hvacData.iso_zone = "A";
                hvacData.motor_condition = "EXCELLENT";
                hvacData.energy_efficiency = 95;
            } else if (velocity < 4.5) {
                hvacData.iso_zone = "B";
                hvacData.motor_condition = "GOOD";
                hvacData.energy_efficiency = 85;
            } else if (velocity < 11.0) {
                hvacData.iso_zone = "C";
                hvacData.motor_condition = "FAIR";
                hvacData.energy_efficiency = 70;
            } else {
                hvacData.iso_zone = "D";
                hvacData.motor_condition = "POOR";
                hvacData.energy_efficiency = 50;
            }
            
            return hvacData;
        }
        
        // Get HVAC motor type
        function getHVACMotorType(motorId) {
            switch (motorId) {
                case 0x50: return "AHU_SUPPLY_FAN";
                case 0x51: return "AHU_RETURN_FAN";
                case 0x52: return "CHILLER_PUMP";
                case 0x53: return "COOLING_TOWER_FAN";
                case 0x54: return "EXHAUST_FAN";
                case 0x55: return "HEAT_PUMP";
                default: return "HVAC_MOTOR";
            }
        }
        
        // Get HVAC zone
        function getHVACZone(motorId) {
            if (motorId >= 0x50 && motorId <= 0x52) return "MECHANICAL_ROOM_A";
            if (motorId >= 0x53 && motorId <= 0x55) return "ROOFTOP_UNIT_1";
            return "UNASSIGNED";
        }
        
        // Set global variables
        function setHVACGlobals(data) {
            let prefix = `${node.hvacPrefix}_${data.motor_id}_`;
            
            try {
                node.context().global.set(prefix + "temperature_f", data.temperature.fahrenheit);
                node.context().global.set(prefix + "temperature_c", data.temperature.celsius);
                node.context().global.set(prefix + "vibration_velocity", data.vibration.velocity_mms);
                node.context().global.set(prefix + "iso_zone", data.iso_zone);
                node.context().global.set(prefix + "motor_condition", data.motor_condition);
                node.context().global.set(prefix + "hvac_motor_type", data.hvac_motor_type);
                node.context().global.set(prefix + "hvac_zone", data.hvac_zone);
                node.context().global.set(prefix + "energy_efficiency", data.energy_efficiency);
                node.context().global.set(prefix + "alert_level", data.alert_level);
                
                // System status
                node.context().global.set("automatanexus_hvac_active", true);
                node.context().global.set("automatanexus_hvac_last_update", data.timestamp);
                
            } catch (error) {
                node.warn("Error setting globals: " + error.message);
            }
        }
        
        // Update node status
        function updateStatus(data) {
            let statusColor = "green";
            let statusShape = "dot";
            let statusText = `${data.hvac_motor_type}: ${data.motor_condition}`;
            
            switch (data.alert_level) {
                case "WARN":
                    statusColor = "yellow";
                    break;
                case "CRIT":
                    statusColor = "orange";
                    statusShape = "ring";
                    break;
                case "EMRG":
                    statusColor = "red";
                    statusShape = "ring";
                    break;
            }
            
            node.status({
                fill: statusColor,
                shape: statusShape,
                text: statusText
            });
        }
        
        // Cleanup
        node.on('close', function() {
            node.status({});
        });
    }
    
    // Register node
    RED.nodes.registerType("hvac-vibration-parser", HVACVibrationParserNode);
}
