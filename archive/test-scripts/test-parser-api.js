#!/usr/bin/env node
/**
 * Test script for updated parser with monitoring API data
 */

// Load the parser module
const parserModule = require('./node-red-contrib-automatanexus-hvac-vibration/industrial-vibration-parser.js');

// Mock RED object
const RED = {
    nodes: {
        createNode: function(node, config) {
            // Mock implementation
            node.on = function() {};
            node.status = function() {};
            node.warn = function() {};
            node.error = function() {};
            node.context = function() {
                return {
                    global: {
                        set: function(key, value) {
                            console.log(`Setting global: ${key} = ${JSON.stringify(value)}`);
                        }
                    }
                };
            };
        },
        registerType: function(type, constructor) {
            console.log(`Registered node type: ${type}`);
            // Create test instance
            testParser(constructor);
        }
    }
};

// Initialize the module
parserModule(RED);

function testParser(ParserConstructor) {
    console.log('\n=== Testing Updated Parser v2.2.0 ===\n');
    
    // Create parser instance with minimal config
    const config = {
        outputFormat: "standard",
        globalVars: false,
        sensorMappings: [
            {
                address: "80",
                enabled: true,
                name: "Old_Config_Name",
                type: "MOTOR_GENERAL",
                location: "Old Location",
                powerHP: 10,
                foundationType: "rigid",
                rpmNominal: 1800
            }
        ]
    };
    
    const parser = new ParserConstructor(config);
    
    // Test 1: Monitoring API format (should override internal config)
    console.log('Test 1: Monitoring API Format');
    console.log('--------------------------------');
    const apiData = {
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
    };
    
    parser.on('input', function(msg, send) {
        send = send || function(msgs) {
            console.log('\nParsed Output:');
            console.log(JSON.stringify(msgs[0].payload, null, 2));
            
            // Verify key values
            const data = msgs[0].payload;
            console.log('\nVerification:');
            console.log(`- Equipment Name: ${data.equipment_name} (should be "Cooling_Tower_1")`);
            console.log(`- Equipment Type: ${data.equipment_type} (should be "COOLING_TOWER")`);
            console.log(`- Power HP: ${data.equipment_power.hp} (should be 50, not 10)`);
            console.log(`- ISO Zone: ${data.iso_zone} (should be "A")`);
            console.log(`- Location: ${data.equipment_location} (should be "From Monitoring System")`);
        };
    });
    
    // Trigger parsing
    parser.emit('input', { payload: apiData }, null, null);
    
    // Test 2: Direct JSON format
    console.log('\n\nTest 2: Direct JSON Format');
    console.log('--------------------------------');
    const directData = {
        "equipment_name": "Chiller_Pump_1",
        "equipment_type": "CENTRIFUGAL_PUMP",
        "temperature_f": 85.0,
        "rms_acceleration": 0.0856,
        "velocity_mms": 4.2,
        "iso_zone": "C",
        "alert_level": "WARN"
    };
    
    parser.emit('input', { payload: directData }, null, null);
    
    // Test 3: Console format
    console.log('\n\nTest 3: Console Format');
    console.log('--------------------------------');
    const consoleData = "[OK] 10:01:35 | Air_Handler_1 | RMS: 0.0156g | Velocity: 0.85mm/s | ISO Zone: A | Temp: 75.0°F";
    
    parser.emit('input', { payload: consoleData }, null, null);
}