/**
 * AutomataNexus Industrial Vibration Monitoring
 * Professional WitMotion WTVB01-485 Integration for Industrial Equipment
 * Supports up to 32 sensors with configurable applications
 * (c) 2025 AutomataNexus AI & AutomataControls
 */

module.exports = function(RED) {
    "use strict";
    
    function IndustrialVibrationParserNode(config) {
        RED.nodes.createNode(this, config);
        var node = this;
        
        // Configuration
        node.outputFormat = config.outputFormat || "standard";
        node.globalVars = config.globalVars !== false;
        node.globalPrefix = config.globalPrefix || "industrial";
        node.sensorMappings = config.sensorMappings || [];
        
        // ISO 10816 vibration severity zones based on machine class
        // Class I: Small machines (<15kW)
        // Class II: Medium machines (15-75kW or up to 300kW on special foundations)
        // Class III: Large machines (>75kW rigid foundation)
        // Class IV: Large machines (>75kW soft foundation)
        const ISO_10816_CLASSES = {
            "I": { zones: { A: 0.71, B: 1.8, C: 4.5, D: 7.1 }, desc: "Small (<15kW)" },
            "II": { zones: { A: 1.12, B: 2.8, C: 7.1, D: 11.2 }, desc: "Medium (15-75kW)" },
            "III": { zones: { A: 1.8, B: 4.5, C: 11.2, D: 18.0 }, desc: "Large Rigid (>75kW)" },
            "IV": { zones: { A: 2.8, B: 7.1, C: 18.0, D: 28.0 }, desc: "Large Soft (>75kW)" }
        };
        
        // Determine ISO class based on power rating
        function getISOClass(powerKW, foundationType) {
            if (powerKW < 15) return "I";
            if (powerKW <= 75) return "II";
            // For large machines, foundation type matters
            if (foundationType === "soft" || foundationType === "flexible") return "IV";
            return "III";
        }
        
        // Default ISO standards for different equipment types with power considerations
        const ISO_STANDARDS = {
            "HVAC_FAN": {
                baseClass: "II",
                adjustForPower: true,
                unit: "mm/s RMS"
            },
            "CENTRIFUGAL_PUMP": {
                baseClass: "II",
                adjustForPower: true,
                unit: "mm/s RMS"
            },
            "RECIPROCATING_COMPRESSOR": {
                // Reciprocating equipment has higher allowable vibration
                customZones: { A: 7.1, B: 11.0, C: 18.0, D: 28.0 },
                adjustForPower: false,
                unit: "mm/s RMS"
            },
            "SCREW_COMPRESSOR": {
                baseClass: "II",
                adjustForPower: true,
                unit: "mm/s RMS"
            },
            "COOLING_TOWER": {
                baseClass: "III",
                adjustForPower: true,
                unit: "mm/s RMS"
            },
            "CONVEYOR_MOTOR": {
                baseClass: "II",
                adjustForPower: true,
                unit: "mm/s RMS"
            },
            "MIXER_AGITATOR": {
                baseClass: "III",
                adjustForPower: true,
                unit: "mm/s RMS"
            },
            "BLOWER": {
                baseClass: "II",
                adjustForPower: true,
                unit: "mm/s RMS"
            },
            "GEARBOX": {
                customZones: { A: 3.5, B: 7.1, C: 11.0, D: 18.0 },
                adjustForPower: false,
                unit: "mm/s RMS"
            },
            "GENERATOR": {
                baseClass: "III",
                adjustForPower: true,
                unit: "mm/s RMS"
            },
            "MOTOR_GENERAL": {
                baseClass: "II",
                adjustForPower: true,
                unit: "mm/s RMS"
            },
            "TURBINE": {
                customZones: { A: 1.8, B: 2.8, C: 4.5, D: 7.1 },
                adjustForPower: false,
                unit: "mm/s RMS"
            },
            "VACUUM_PUMP": {
                baseClass: "II",
                adjustForPower: true,
                unit: "mm/s RMS"
            },
            "CRUSHER": {
                customZones: { A: 7.1, B: 11.0, C: 18.0, D: 28.0 },
                adjustForPower: false,
                unit: "mm/s RMS"
            },
            "CUSTOM": {
                baseClass: "II",
                adjustForPower: true,
                unit: "mm/s RMS"
            }
        };
        
        // Build sensor lookup map from configuration
        node.sensorMap = {};
        if (node.sensorMappings && Array.isArray(node.sensorMappings)) {
            node.sensorMappings.forEach(mapping => {
                if (mapping.address && mapping.enabled) {
                    node.sensorMap[mapping.address] = {
                        name: mapping.name || `Sensor_${mapping.address}`,
                        type: mapping.type || "MOTOR_GENERAL",
                        location: mapping.location || "Unspecified",
                        powerHP: mapping.powerHP || null,
                        powerKW: mapping.powerKW || mapping.powerHP ? mapping.powerHP * 0.746 : null,
                        foundationType: mapping.foundationType || "rigid",
                        rpmNominal: mapping.rpmNominal || 1800,
                        customZones: mapping.customZones || null,
                        alarmThresholds: mapping.alarmThresholds || null
                    };
                }
            });
        }
        
        // Statistics
        node.messageCount = 0;
        node.lastUpdate = null;
        node.sensorStatus = {};
        
        // Node status
        node.status({fill: "blue", shape: "dot", text: "Ready"});
        
        // Process incoming messages
        node.on('input', function(msg, send, done) {
            send = send || function() { node.send.apply(node, arguments); };
            
            try {
                let parsedData = parseIndustrialData(msg.payload);
                
                if (parsedData) {
                    node.messageCount++;
                    node.lastUpdate = new Date();
                    
                    // Update sensor status tracking
                    node.sensorStatus[parsedData.sensor_address] = {
                        lastSeen: node.lastUpdate,
                        condition: parsedData.equipment_condition
                    };
                    
                    // Set global variables
                    if (node.globalVars) {
                        setIndustrialGlobals(parsedData);
                    }
                    
                    // Update status
                    updateNodeStatus();
                    
                    // Send output
                    send([{
                        payload: parsedData,
                        topic: `${node.globalPrefix}/${parsedData.equipment_type.toLowerCase()}/${parsedData.sensor_address}`,
                        sensor_address: parsedData.sensor_address,
                        equipment_type: parsedData.equipment_type,
                        equipment_name: parsedData.equipment_name,
                        iso_zone: parsedData.iso_zone,
                        iso_class: parsedData.iso_class,
                        alerts: parsedData.alerts
                    }]);
                    
                    if (done) done();
                } else {
                    node.warn("Failed to parse industrial data");
                    if (done) done();
                }
                
            } catch (error) {
                node.error("Industrial Parser Error: " + error.message, msg);
                node.status({fill: "red", shape: "ring", text: "Error"});
                if (done) done(error);
            }
        });
        
        // Parse industrial data
        function parseIndustrialData(payload) {
            let data = {};
            
            try {
                if (typeof payload === 'string') {
                    // Parse console output or JSON
                    if (payload.includes('[OK]') || payload.includes('[WARN]') || 
                        payload.includes('[CRIT]') || payload.includes('[EMRG]')) {
                        data = parseConsoleOutput(payload);
                    } else {
                        data = JSON.parse(payload);
                    }
                } else if (typeof payload === 'object') {
                    data = payload;
                }
                
                return standardizeIndustrialData(data);
                
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
            
            // Extract sensor address - support multiple formats
            let addressMatch = text.match(/(?:Sensor|Motor|Address)\s*0x([0-9A-F]+)/i);
            if (addressMatch) {
                data.sensor_address = parseInt(addressMatch[1], 16);
            }
            
            // Extract temperature
            let tempMatch = text.match(/Temp:\s*([+-]?\d+(?:\.\d+)?)\s*°([FC])/i);
            if (tempMatch) {
                let temp = parseFloat(tempMatch[1]);
                if (tempMatch[2] === 'F') {
                    data.temperature_f = temp;
                } else {
                    data.temperature_c = temp;
                }
            }
            
            // Extract vibration velocity
            let velMatch = text.match(/Vel:\s*([+-]?\d+(?:\.\d+)?)\s*mm\/s/i);
            if (velMatch) data.vibration_velocity = parseFloat(velMatch[1]);
            
            // Extract RMS acceleration
            let rmsMatch = text.match(/RMS:\s*([+-]?\d+(?:\.\d+)?)\s*g/i);
            if (rmsMatch) data.rms_acceleration = parseFloat(rmsMatch[1]);
            
            // Extract frequency
            let freqMatch = text.match(/Freq:\s*([+-]?\d+(?:\.\d+)?)\s*Hz/i);
            if (freqMatch) data.frequency = parseFloat(freqMatch[1]);
            
            // Extract ISO zone if present
            let zoneMatch = text.match(/Zone:\s*([A-D])/i);
            if (zoneMatch) data.iso_zone = zoneMatch[1];
            
            return data;
        }
        
        // Standardize industrial data
        function standardizeIndustrialData(rawData) {
            if (!rawData) return null;
            
            // Handle both old format (motor_id) and new format (sensor_address)
            if (!rawData.sensor_address && rawData.motor_id !== undefined) {
                rawData.sensor_address = rawData.motor_id;
            }
            
            if (!rawData.sensor_address) return null;
            
            // Get sensor configuration
            let sensorConfig = node.sensorMap[rawData.sensor_address] || {
                name: `Sensor_${rawData.sensor_address}`,
                type: "MOTOR_GENERAL",
                location: "Unknown",
                powerKW: 30, // Default 30kW if not specified
                foundationType: "rigid"
            };
            
            // Get equipment type configuration
            let equipmentStandard = ISO_STANDARDS[sensorConfig.type] || ISO_STANDARDS["MOTOR_GENERAL"];
            
            // Determine ISO zones based on power rating and equipment type
            let isoZones;
            let isoClass = "";
            
            if (equipmentStandard.adjustForPower && sensorConfig.powerKW) {
                // Get ISO class based on power
                isoClass = getISOClass(sensorConfig.powerKW, sensorConfig.foundationType);
                isoZones = ISO_10816_CLASSES[isoClass].zones;
            } else if (equipmentStandard.customZones) {
                // Use equipment-specific zones
                isoZones = equipmentStandard.customZones;
                isoClass = "Equipment Specific";
            } else {
                // Use base class zones
                isoClass = equipmentStandard.baseClass;
                isoZones = ISO_10816_CLASSES[isoClass].zones;
            }
            
            // Override with custom zones if specified
            if (sensorConfig.customZones) {
                isoZones = sensorConfig.customZones;
                isoClass = "Custom";
            }
            
            let industrialData = {
                timestamp: new Date().toISOString(),
                sensor_address: rawData.sensor_address,
                equipment_name: sensorConfig.name,
                equipment_type: sensorConfig.type,
                equipment_location: sensorConfig.location,
                equipment_power: {
                    hp: sensorConfig.powerHP || (sensorConfig.powerKW ? sensorConfig.powerKW / 0.746 : null),
                    kw: sensorConfig.powerKW || (sensorConfig.powerHP ? sensorConfig.powerHP * 0.746 : null)
                },
                equipment_specs: {
                    foundation_type: sensorConfig.foundationType,
                    rpm_nominal: sensorConfig.rpmNominal,
                    iso_class: isoClass,
                    iso_zones: isoZones
                },
                
                temperature: {
                    fahrenheit: 0,
                    celsius: 0
                },
                
                vibration: {
                    velocity_mms: rawData.vibration_velocity || (rawData.vibration && rawData.vibration.velocity_mms) || 0,
                    rms_acceleration_g: rawData.rms_acceleration || (rawData.vibration && rawData.vibration.rms_acceleration_g) || 0,
                    frequency_hz: rawData.frequency || (rawData.vibration && rawData.vibration.frequency_hz) || 0,
                    displacement_um: rawData.displacement || (rawData.vibration && rawData.vibration.displacement_um) || 0
                },
                
                alert_level: rawData.alert_level || "NORMAL",
                iso_zone: "",
                iso_class: isoClass,
                equipment_condition: "",
                maintenance_priority: "LOW",
                estimated_rul_days: 365, // Remaining Useful Life
                alerts: []
            };
            
            // Temperature conversion - handle multiple formats
            if (rawData.temperature_f !== undefined) {
                industrialData.temperature.fahrenheit = rawData.temperature_f;
                industrialData.temperature.celsius = (rawData.temperature_f - 32) * 5.0 / 9.0;
            } else if (rawData.temperature_c !== undefined) {
                industrialData.temperature.celsius = rawData.temperature_c;
                industrialData.temperature.fahrenheit = (rawData.temperature_c * 9.0 / 5.0) + 32;
            } else if (rawData.temperature && typeof rawData.temperature === 'object') {
                // Handle nested temperature object
                industrialData.temperature.fahrenheit = rawData.temperature.fahrenheit || 70;
                industrialData.temperature.celsius = rawData.temperature.celsius || ((industrialData.temperature.fahrenheit - 32) * 5.0 / 9.0);
            } else if (rawData.temperature !== undefined && typeof rawData.temperature === 'number') {
                // Handle single temperature value (assume Fahrenheit from WTVB01-485)
                industrialData.temperature.fahrenheit = rawData.temperature;
                industrialData.temperature.celsius = (rawData.temperature - 32) * 5.0 / 9.0;
            }
            
            // Handle metrics from API format
            if (rawData.metrics && typeof rawData.metrics === 'object') {
                industrialData.vibration.velocity_mms = rawData.metrics.velocity_mms || rawData.metrics.vibration_velocity_rms || 0;
                industrialData.vibration.rms_acceleration_g = rawData.metrics.rms_acceleration || 0;
                industrialData.vibration.frequency_hz = rawData.metrics.dominant_frequency || 0;
                if (rawData.metrics.iso_zone) {
                    rawData.iso_zone = rawData.metrics.iso_zone;
                }
            }
            
            // Handle acceleration data from API format
            if (rawData.acceleration && typeof rawData.acceleration === 'object') {
                // Calculate RMS from 3-axis if not already provided
                if (!industrialData.vibration.rms_acceleration_g && 
                    (rawData.acceleration.x !== undefined || 
                     rawData.acceleration.y !== undefined || 
                     rawData.acceleration.z !== undefined)) {
                    let x = rawData.acceleration.x || 0;
                    let y = rawData.acceleration.y || 0;
                    let z = rawData.acceleration.z || 0;
                    industrialData.vibration.rms_acceleration_g = Math.sqrt(x*x + y*y + z*z) / Math.sqrt(3);
                }
            }
            
            // ISO zone classification
            let velocity = industrialData.vibration.velocity_mms;
            if (velocity < isoZones.A) {
                industrialData.iso_zone = "A";
                industrialData.equipment_condition = "EXCELLENT";
                industrialData.maintenance_priority = "LOW";
                industrialData.estimated_rul_days = 365;
            } else if (velocity < isoZones.B) {
                industrialData.iso_zone = "B";
                industrialData.equipment_condition = "GOOD";
                industrialData.maintenance_priority = "LOW";
                industrialData.estimated_rul_days = 180;
            } else if (velocity < isoZones.C) {
                industrialData.iso_zone = "C";
                industrialData.equipment_condition = "FAIR";
                industrialData.maintenance_priority = "MEDIUM";
                industrialData.estimated_rul_days = 90;
                industrialData.alerts.push({
                    type: "VIBRATION_WARNING",
                    message: `Vibration ${velocity.toFixed(2)} mm/s exceeds ISO ${isoClass} Zone B (${isoZones.B} mm/s)`,
                    severity: "WARNING"
                });
            } else {
                industrialData.iso_zone = "D";
                industrialData.equipment_condition = "POOR";
                industrialData.maintenance_priority = "HIGH";
                industrialData.estimated_rul_days = 30;
                industrialData.alerts.push({
                    type: "VIBRATION_CRITICAL",
                    message: `Vibration ${velocity.toFixed(2)} mm/s exceeds ISO ${isoClass} Zone C (${isoZones.C} mm/s)`,
                    severity: "CRITICAL"
                });
            }
            
            // Temperature alerts
            if (industrialData.temperature.celsius > 80) {
                industrialData.alerts.push({
                    type: "TEMPERATURE_HIGH",
                    message: `Temperature ${industrialData.temperature.celsius.toFixed(1)}°C exceeds 80°C threshold`,
                    severity: "WARNING"
                });
                industrialData.maintenance_priority = "HIGH";
            } else if (industrialData.temperature.celsius > 90) {
                industrialData.alerts.push({
                    type: "TEMPERATURE_CRITICAL",
                    message: `Temperature ${industrialData.temperature.celsius.toFixed(1)}°C exceeds 90°C critical threshold`,
                    severity: "CRITICAL"
                });
            }
            
            // RPM deviation alerts (if frequency data available)
            if (industrialData.vibration.frequency_hz > 0 && sensorConfig.rpmNominal) {
                let measuredRPM = industrialData.vibration.frequency_hz * 60;
                let rpmDeviation = Math.abs(measuredRPM - sensorConfig.rpmNominal) / sensorConfig.rpmNominal * 100;
                if (rpmDeviation > 10) {
                    industrialData.alerts.push({
                        type: "RPM_DEVIATION",
                        message: `RPM deviation ${rpmDeviation.toFixed(1)}% from nominal ${sensorConfig.rpmNominal} RPM`,
                        severity: "WARNING"
                    });
                }
            }
            
            // Custom alarm thresholds
            if (sensorConfig.alarmThresholds) {
                checkCustomAlarms(industrialData, sensorConfig.alarmThresholds);
            }
            
            return industrialData;
        }
        
        // Check custom alarm thresholds
        function checkCustomAlarms(data, thresholds) {
            if (thresholds.vibration && data.vibration.velocity_mms > thresholds.vibration) {
                data.alerts.push({
                    type: "CUSTOM_VIBRATION_ALARM",
                    message: `Vibration ${data.vibration.velocity_mms.toFixed(2)} mm/s exceeds custom threshold ${thresholds.vibration} mm/s`,
                    severity: "CUSTOM"
                });
            }
            
            if (thresholds.temperature && data.temperature.celsius > thresholds.temperature) {
                data.alerts.push({
                    type: "CUSTOM_TEMPERATURE_ALARM",
                    message: `Temperature ${data.temperature.celsius.toFixed(1)}°C exceeds custom threshold ${thresholds.temperature}°C`,
                    severity: "CUSTOM"
                });
            }
            
            if (thresholds.acceleration && data.vibration.rms_acceleration_g > thresholds.acceleration) {
                data.alerts.push({
                    type: "CUSTOM_ACCELERATION_ALARM",
                    message: `Acceleration ${data.vibration.rms_acceleration_g.toFixed(3)}g exceeds custom threshold ${thresholds.acceleration}g`,
                    severity: "CUSTOM"
                });
            }
        }
        
        // Set global variables
        function setIndustrialGlobals(data) {
            let prefix = `${node.globalPrefix}_${data.equipment_type.toLowerCase()}_${data.sensor_address}_`;
            
            try {
                // Basic measurements
                node.context().global.set(prefix + "temperature_f", data.temperature.fahrenheit);
                node.context().global.set(prefix + "temperature_c", data.temperature.celsius);
                node.context().global.set(prefix + "vibration_velocity", data.vibration.velocity_mms);
                node.context().global.set(prefix + "vibration_acceleration", data.vibration.rms_acceleration_g);
                node.context().global.set(prefix + "vibration_frequency", data.vibration.frequency_hz);
                
                // Equipment status
                node.context().global.set(prefix + "iso_zone", data.iso_zone);
                node.context().global.set(prefix + "iso_class", data.iso_class);
                node.context().global.set(prefix + "condition", data.equipment_condition);
                node.context().global.set(prefix + "maintenance_priority", data.maintenance_priority);
                node.context().global.set(prefix + "estimated_rul_days", data.estimated_rul_days);
                
                // Equipment info
                node.context().global.set(prefix + "name", data.equipment_name);
                node.context().global.set(prefix + "type", data.equipment_type);
                node.context().global.set(prefix + "location", data.equipment_location);
                node.context().global.set(prefix + "power_hp", data.equipment_power.hp);
                node.context().global.set(prefix + "power_kw", data.equipment_power.kw);
                
                // Alerts
                node.context().global.set(prefix + "alert_count", data.alerts.length);
                node.context().global.set(prefix + "alerts", data.alerts);
                
                // System status
                node.context().global.set(node.globalPrefix + "_monitoring_active", true);
                node.context().global.set(node.globalPrefix + "_last_update", data.timestamp);
                node.context().global.set(node.globalPrefix + "_sensor_count", Object.keys(node.sensorStatus).length);
                
            } catch (error) {
                node.warn("Error setting globals: " + error.message);
            }
        }
        
        // Update node status with overall system health
        function updateNodeStatus() {
            let totalSensors = Object.keys(node.sensorStatus).length;
            let poorCondition = 0;
            let warnings = 0;
            
            for (let addr in node.sensorStatus) {
                let status = node.sensorStatus[addr];
                if (status.condition === "POOR") poorCondition++;
                else if (status.condition === "FAIR") warnings++;
            }
            
            let statusColor = "green";
            let statusShape = "dot";
            let statusText = `${totalSensors} sensors active`;
            
            if (poorCondition > 0) {
                statusColor = "red";
                statusShape = "ring";
                statusText = `${poorCondition} critical, ${totalSensors} total`;
            } else if (warnings > 0) {
                statusColor = "yellow";
                statusText = `${warnings} warnings, ${totalSensors} total`;
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
    RED.nodes.registerType("industrial-vibration-parser", IndustrialVibrationParserNode);
}