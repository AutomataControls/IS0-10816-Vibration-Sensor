/**
 * ################################################################################
 * # AutomataNexus Vibration Monitor - Node-RED Industrial Parser
 * # Enterprise-Grade ISO 10816-3 Compliant Vibration Analysis Platform
 * ################################################################################
 * #
 * # 🔧 Professional Vibration Monitoring Solution - Node-RED Integration
 * # 📊 Enterprise-Grade Equipment Health Analysis with ISO Standards
 * #
 * # © 2025 AutomataNexus AI & AutomataControls. All rights reserved.
 * #
 * # COMMERCIAL LICENSE NOTICE:
 * # This software is commercially licensed, not open source. For licensing inquiries,
 * # contact DevOps@automatacontrols.com. See COMMERCIAL.md for full license terms.
 * # This code is protected and proprietary. No redistribution allowed.
 * #
 * # Author: Andrew Jewell Sr. - Dev Ops Automata Controls / AutomataNexus AI
 * # License: Commercial License Required (Professional/Business/Enterprise)
 * # Serial Number: VIB-2025-PARSER-001
 * # Website: https://vibration.automatacontrols.com
 * #
 * # Unauthorized use, reproduction, or distribution is strictly prohibited.
 * ################################################################################
 * 
 * Professional WitMotion WTVB01-485 Integration for Industrial Equipment
 * Supports up to 32 sensors with configurable applications
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
                    // Handle array of sensors from monitoring API
                    let dataArray = Array.isArray(parsedData) ? parsedData : [parsedData];
                    let messages = [];
                    
                    dataArray.forEach(data => {
                        let processedData = data;
                        
                        // If already standardized, use it
                        if (!data.sensor_address && !data.equipment_name) {
                            processedData = standardizeIndustrialData(data);
                        }
                        
                        if (processedData) {
                            node.messageCount++;
                            node.lastUpdate = new Date();
                            
                            // Update sensor status tracking
                            node.sensorStatus[processedData.sensor_address] = {
                                lastSeen: node.lastUpdate,
                                condition: processedData.equipment_condition
                            };
                            
                            // Set global variables
                            if (node.globalVars) {
                                setIndustrialGlobals(processedData);
                            }
                            
                            // Create output message
                            messages.push({
                                payload: processedData,
                                topic: `${node.globalPrefix}/${processedData.equipment_type.toLowerCase()}/${processedData.sensor_address}`,
                                sensor_address: processedData.sensor_address,
                                equipment_type: processedData.equipment_type,
                                equipment_name: processedData.equipment_name,
                                iso_zone: processedData.iso_zone,
                                iso_class: processedData.iso_class,
                                alerts: processedData.alerts
                            });
                        }
                    });
                    
                    // Update status
                    updateNodeStatus();
                    
                    // Send all messages
                    if (messages.length > 0) {
                        send([messages]);
                    }
                    
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
                        return standardizeIndustrialData(data);
                    } else {
                        data = JSON.parse(payload);
                    }
                } else if (typeof payload === 'object') {
                    data = payload;
                }
                
                // Check if this is monitoring API data (has equipment names as keys)
                if (isMonitoringAPIData(data)) {
                    // Convert monitoring API format - returns array or single object
                    let converted = convertMonitoringAPIData(data);
                    
                    // If array, standardize each item
                    if (Array.isArray(converted)) {
                        return converted.map(item => standardizeIndustrialData(item));
                    } else {
                        return standardizeIndustrialData(converted);
                    }
                } else {
                    return standardizeIndustrialData(data);
                }
                
            } catch (error) {
                return null;
            }
        }
        
        // Check if data is from monitoring API (equipment names as keys)
        function isMonitoringAPIData(data) {
            // Monitoring API has equipment names as keys with sensor data as values
            for (let key in data) {
                if (data.hasOwnProperty(key)) {
                    let value = data[key];
                    if (typeof value === 'object' && 
                        (value.hasOwnProperty('temperature_f') || 
                         value.hasOwnProperty('rms_acceleration') ||
                         value.hasOwnProperty('velocity_mms'))) {
                        return true;
                    }
                }
            }
            return false;
        }
        
        // Convert monitoring API format to parser format
        function convertMonitoringAPIData(apiData) {
            // Handle multiple sensors - return array
            let results = [];
            
            for (let equipmentName in apiData) {
                if (apiData.hasOwnProperty(equipmentName)) {
                    let sensorData = apiData[equipmentName];
                    
                    results.push({
                        equipment_name: equipmentName,
                        equipment_type: sensorData.equipment_type || detectEquipmentType(equipmentName),
                        temperature_f: sensorData.temperature_f,
                        vibration_velocity: sensorData.velocity_mms,
                        rms_acceleration: sensorData.rms_acceleration,
                        iso_zone: sensorData.iso_zone,
                        alert_level: sensorData.alert_level || "NORMAL",
                        // Include any additional fields from API
                        hp: sensorData.hp,
                        voltage: sensorData.voltage,
                        phase: sensorData.phase,
                        rpm: sensorData.rpm,
                        mounting: sensorData.mounting,
                        port: sensorData.port
                    });
                }
            }
            
            // Return array if multiple sensors, single object if one
            return results.length === 1 ? results[0] : results;
        }
        
        // Detect equipment type from name or type string
        function detectEquipmentType(name) {
            let lowerName = name.toLowerCase();
            
            // Direct equipment type mappings
            if (lowerName === 'cooling_tower_motor') return 'COOLING_TOWER';
            if (lowerName === 'centrifugal_pump') return 'CENTRIFUGAL_PUMP';
            if (lowerName === 'reciprocating_compressor') return 'RECIPROCATING_COMPRESSOR';
            if (lowerName === 'screw_compressor') return 'SCREW_COMPRESSOR';
            if (lowerName === 'scroll_compressor') return 'SCROLL_COMPRESSOR';
            if (lowerName === 'circulation_pump') return 'CIRCULATION_PUMP';
            if (lowerName === 'fan_motor') return 'HVAC_FAN';
            if (lowerName === 'general_motor') return 'MOTOR_GENERAL';
            
            // Name-based detection
            if (lowerName.includes('cooling') && lowerName.includes('tower')) return 'COOLING_TOWER';
            if (lowerName.includes('pump')) return 'CENTRIFUGAL_PUMP';
            if (lowerName.includes('compressor')) return 'SCREW_COMPRESSOR';
            if (lowerName.includes('fan')) return 'HVAC_FAN';
            if (lowerName.includes('blower')) return 'BLOWER';
            if (lowerName.includes('mixer')) return 'MIXER_AGITATOR';
            if (lowerName.includes('motor')) return 'MOTOR_GENERAL';
            
            return 'MOTOR_GENERAL';
        }
        
        // Parse console output
        function parseConsoleOutput(text) {
            let data = {};
            
            // Extract alert level
            let alertMatch = text.match(/\[(OK|WARN|CRIT|EMRG)\]/);
            if (alertMatch) data.alert_level = alertMatch[1];
            
            // Extract timestamp if present
            let timeMatch = text.match(/(\d{2}:\d{2}:\d{2})/);
            if (timeMatch) data.timestamp_str = timeMatch[1];
            
            // Extract equipment name (new format) or sensor address (old format)
            // New format: [OK] 10:01:35 | Cooling_Tower_1 | RMS: ...
            // Old format: [OK] Sensor 0x50 | RMS: ...
            let parts = text.split('|').map(p => p.trim());
            if (parts.length >= 2) {
                let sensorPart = parts[1];
                
                // Check if it's an address format
                let addressMatch = sensorPart.match(/(?:Sensor|Motor|Address|TTYUSB\d+)\s*(?:0x([0-9A-F]+))?/i);
                if (addressMatch && addressMatch[1]) {
                    data.sensor_address = parseInt(addressMatch[1], 16);
                } else if (sensorPart.match(/TTYUSB(\d+)/i)) {
                    // Handle TTYUSB format
                    let usbMatch = sensorPart.match(/TTYUSB(\d+)/i);
                    data.sensor_port = `TTYUSB${usbMatch[1]}`;
                    data.equipment_name = sensorPart; // May be overridden if actual name found
                } else {
                    // It's likely an equipment name
                    data.equipment_name = sensorPart;
                    // Try to extract equipment type from name
                    if (sensorPart.toLowerCase().includes('cooling_tower')) {
                        data.equipment_type = 'COOLING_TOWER';
                    } else if (sensorPart.toLowerCase().includes('pump')) {
                        data.equipment_type = 'CENTRIFUGAL_PUMP';
                    } else if (sensorPart.toLowerCase().includes('compressor')) {
                        data.equipment_type = 'SCREW_COMPRESSOR';
                    } else if (sensorPart.toLowerCase().includes('fan')) {
                        data.equipment_type = 'HVAC_FAN';
                    }
                }
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
            
            // Extract vibration velocity (supports both "Vel:" and "Velocity:")
            let velMatch = text.match(/(?:Vel|Velocity):\s*([+-]?\d+(?:\.\d+)?)\s*mm\/s/i);
            if (velMatch) data.vibration_velocity = parseFloat(velMatch[1]);
            
            // Extract RMS acceleration
            let rmsMatch = text.match(/RMS:\s*([+-]?\d+(?:\.\d+)?)\s*g/i);
            if (rmsMatch) data.rms_acceleration = parseFloat(rmsMatch[1]);
            
            // Extract frequency
            let freqMatch = text.match(/Freq:\s*([+-]?\d+(?:\.\d+)?)\s*Hz/i);
            if (freqMatch) data.frequency = parseFloat(freqMatch[1]);
            
            // Extract ISO zone if present
            let zoneMatch = text.match(/(?:ISO\s*)?Zone:\s*([A-D])/i);
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
            
            // If we have equipment_name but no sensor_address, create a pseudo-address
            if (!rawData.sensor_address && rawData.equipment_name) {
                // Use a hash of the equipment name as address for consistency
                let hash = 0;
                for (let i = 0; i < rawData.equipment_name.length; i++) {
                    hash = ((hash << 5) - hash) + rawData.equipment_name.charCodeAt(i);
                    hash = hash & hash; // Convert to 32bit integer
                }
                rawData.sensor_address = Math.abs(hash) % 256; // Keep it in byte range
            }
            
            if (!rawData.sensor_address && !rawData.equipment_name) return null;
            
            // Get sensor configuration - prefer data from message over internal config
            let sensorConfig;
            
            // If we have full equipment data from the monitoring API, use it directly
            if (rawData.equipment_name && rawData.equipment_type) {
                sensorConfig = {
                    name: rawData.equipment_name,
                    type: rawData.equipment_type,
                    location: rawData.location || "From Monitoring System",
                    powerHP: rawData.hp,
                    powerKW: rawData.hp ? rawData.hp * 0.746 : 30,
                    foundationType: rawData.mounting || "rigid",
                    rpmNominal: rawData.rpm || 1800,
                    voltage: rawData.voltage,
                    phase: rawData.phase
                };
            } else {
                // Fall back to internal configuration or defaults
                sensorConfig = node.sensorMap[rawData.sensor_address] || {
                    name: rawData.equipment_name || `Sensor_${rawData.sensor_address}`,
                    type: rawData.equipment_type || "MOTOR_GENERAL",
                    location: "Unknown",
                    powerKW: 30, // Default 30kW if not specified
                    foundationType: "rigid"
                };
            }
            
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
            
            // ISO zone classification - use provided zone if available
            if (rawData.iso_zone) {
                // Trust the ISO zone from the monitoring API
                industrialData.iso_zone = rawData.iso_zone;
                
                // Set condition based on zone
                switch(rawData.iso_zone) {
                    case "A":
                        industrialData.equipment_condition = "EXCELLENT";
                        industrialData.maintenance_priority = "LOW";
                        industrialData.estimated_rul_days = 365;
                        break;
                    case "B":
                        industrialData.equipment_condition = "GOOD";
                        industrialData.maintenance_priority = "LOW";
                        industrialData.estimated_rul_days = 180;
                        break;
                    case "C":
                        industrialData.equipment_condition = "FAIR";
                        industrialData.maintenance_priority = "MEDIUM";
                        industrialData.estimated_rul_days = 90;
                        industrialData.alerts.push({
                            type: "VIBRATION_WARNING",
                            message: `Equipment in ISO Zone C - Schedule maintenance`,
                            severity: "WARNING"
                        });
                        break;
                    case "D":
                        industrialData.equipment_condition = "POOR";
                        industrialData.maintenance_priority = "HIGH";
                        industrialData.estimated_rul_days = 30;
                        industrialData.alerts.push({
                            type: "VIBRATION_CRITICAL",
                            message: `Equipment in ISO Zone D - Immediate attention required`,
                            severity: "CRITICAL"
                        });
                        break;
                }
            } else {
                // Calculate ISO zone if not provided
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