// Sensor Configuration Module for Multi-Port Monitoring
// Integrates with Flask backend API

// Use the API_BASE from index.html if it exists, otherwise define it
if (typeof API_BASE === 'undefined') {
    var API_BASE = 'http://localhost:5000';
}

// Equipment types matching the backend
const EQUIPMENT_TYPES = {
    "cooling_tower_motor": "Cooling Tower Motor",
    "centrifugal_pump": "Centrifugal Pump", 
    "reciprocating_compressor": "Reciprocating Compressor",
    "screw_compressor": "Screw Compressor",
    "scroll_compressor": "Scroll Compressor",
    "circulation_pump": "Circulation Pump",
    "fan_motor": "Fan Motor",
    "general_motor": "General Purpose Motor"
};

// Scan for available USB ports with sensors
async function scanForSensors() {
    try {
        showLoading('sensorConfigList', 'Scanning for sensors...');
        
        const response = await fetch(`${API_BASE}/api/scan_ports`);
        const data = await response.json();
        
        if (data.status === 'success' && data.ports.length > 0) {
            displayDetectedPorts(data.ports);
        } else {
            showNoSensorsFound();
        }
    } catch (error) {
        console.error('Error scanning sensors:', error);
        showError('sensorConfigList', 'Failed to scan for sensors');
    }
}

// Display detected ports
function displayDetectedPorts(ports) {
    const container = document.getElementById('sensorConfigList');
    container.innerHTML = '';
    
    ports.forEach(port => {
        const card = createSensorConfigCard(port);
        container.appendChild(card);
    });
}

// Create configuration card for a sensor port
function createSensorConfigCard(port) {
    const card = document.createElement('div');
    card.className = 'glass-card p-6';
    card.innerHTML = `
        <div class="flex justify-between items-start mb-4">
            <div>
                <h3 class="text-xl font-light text-gray-800">${port}</h3>
                <p class="text-sm text-gray-600">Address: 0x50</p>
            </div>
            <div class="status-indicator bg-green-500"></div>
        </div>
        
        <form id="config-${port}" class="space-y-4">
            <div>
                <label class="block text-sm font-light text-gray-700 mb-1">Equipment Name</label>
                <input type="text" name="equipment_name" class="input-field" 
                       placeholder="e.g., Cooling_Tower_1" required>
            </div>
            
            <div>
                <label class="block text-sm font-light text-gray-700 mb-1">Equipment Type</label>
                <select name="equipment_type" class="input-field" required>
                    ${Object.entries(EQUIPMENT_TYPES).map(([value, label]) => 
                        `<option value="${value}">${label}</option>`
                    ).join('')}
                </select>
            </div>
            
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <label class="block text-sm font-light text-gray-700 mb-1">HP</label>
                    <input type="number" name="hp" class="input-field" 
                           placeholder="50" min="3" max="50" required>
                </div>
                <div>
                    <label class="block text-sm font-light text-gray-700 mb-1">RPM</label>
                    <input type="number" name="rpm" class="input-field" 
                           placeholder="1800" value="1800" required>
                </div>
            </div>
            
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <label class="block text-sm font-light text-gray-700 mb-1">Voltage</label>
                    <select name="voltage" class="input-field" required>
                        <option value="208">208V</option>
                        <option value="230">230V</option>
                        <option value="460">460V</option>
                        <option value="480" selected>480V</option>
                    </select>
                </div>
                <div>
                    <label class="block text-sm font-light text-gray-700 mb-1">Phase</label>
                    <select name="phase" class="input-field" required>
                        <option value="1">Single Phase</option>
                        <option value="3" selected>Three Phase</option>
                    </select>
                </div>
            </div>
            
            <div>
                <label class="block text-sm font-light text-gray-700 mb-1">Mounting</label>
                <select name="mounting" class="input-field" required>
                    <option value="rigid">Rigid</option>
                    <option value="flexible">Flexible</option>
                </select>
            </div>
            
            <button type="submit" class="btn btn-primary w-full" 
                    onclick="saveSensorConfig('${port}', event)">
                💾 Save Configuration
            </button>
        </form>
    `;
    
    return card;
}

// Save sensor configuration
async function saveSensorConfig(port, event) {
    event.preventDefault();
    
    const form = document.getElementById(`config-${port}`);
    const formData = new FormData(form);
    
    const config = {
        port: port,
        equipment_name: formData.get('equipment_name'),
        equipment_type: formData.get('equipment_type'),
        hp: parseInt(formData.get('hp')),
        voltage: parseInt(formData.get('voltage')),
        phase: parseInt(formData.get('phase')),
        rpm: parseInt(formData.get('rpm')),
        mounting: formData.get('mounting')
    };
    
    try {
        const response = await fetch(`${API_BASE}/api/save_equipment_config`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            showNotification('Configuration saved successfully!', 'success');
            // Update the card to show saved state
            updateCardSavedState(port);
        } else {
            showNotification('Failed to save configuration', 'error');
        }
    } catch (error) {
        console.error('Error saving configuration:', error);
        showNotification('Error saving configuration', 'error');
    }
}

// Load existing configurations
async function loadSensorConfigurations() {
    try {
        const response = await fetch(`${API_BASE}/api/equipment_config`);
        const configs = await response.json();
        
        if (Object.keys(configs).length > 0) {
            displayExistingConfigs(configs);
        } else {
            // If no configs, scan for sensors
            await scanForSensors();
        }
    } catch (error) {
        console.error('Error loading configurations:', error);
        showError('sensorConfigList', 'Failed to load configurations');
    }
}

// Display existing configurations
function displayExistingConfigs(configs) {
    const container = document.getElementById('sensorConfigList');
    container.innerHTML = '';
    
    Object.entries(configs).forEach(([port, config]) => {
        const card = createConfiguredSensorCard(port, config);
        container.appendChild(card);
    });
}

// Create card for already configured sensor
function createConfiguredSensorCard(port, config) {
    const card = document.createElement('div');
    card.className = 'glass-card p-6';
    card.innerHTML = `
        <div class="flex justify-between items-start mb-4">
            <div>
                <h3 class="text-xl font-semibold text-gray-800">${config.equipment_name}</h3>
                <p class="text-sm text-gray-600">${port} • ${EQUIPMENT_TYPES[config.equipment_type]}</p>
            </div>
            <div class="flex items-center gap-2">
                <div class="status-indicator bg-green-500"></div>
                <span class="text-sm text-green-600">Configured</span>
            </div>
        </div>
        
        <div class="grid grid-cols-2 gap-4 text-sm">
            <div>
                <span class="text-gray-600">Power:</span>
                <span class="font-medium">${config.hp} HP</span>
            </div>
            <div>
                <span class="text-gray-600">Voltage:</span>
                <span class="font-medium">${config.voltage}V ${config.phase}φ</span>
            </div>
            <div>
                <span class="text-gray-600">RPM:</span>
                <span class="font-medium">${config.rpm}</span>
            </div>
            <div>
                <span class="text-gray-600">Mounting:</span>
                <span class="font-medium">${config.mounting}</span>
            </div>
        </div>
        
        <div class="mt-4 flex gap-2">
            <button onclick="editSensorConfig('${port}')" class="btn btn-secondary flex-1">
                ✏️ Edit
            </button>
            <button onclick="deleteSensorConfig('${port}')" class="btn btn-danger flex-1">
                🗑️ Remove
            </button>
        </div>
    `;
    
    return card;
}

// Helper functions
function showLoading(elementId, message) {
    const element = document.getElementById(elementId);
    element.innerHTML = `
        <div class="glass-card p-8 flex items-center justify-center min-h-64">
            <div class="text-center">
                <div class="spinner mx-auto mb-6"></div>
                <p class="text-gray-600 font-ultralight text-lg">${message}</p>
            </div>
        </div>
    `;
}

function showError(elementId, message) {
    const element = document.getElementById(elementId);
    element.innerHTML = `
        <div class="glass-card p-8 flex items-center justify-center min-h-64">
            <div class="text-center">
                <div class="text-red-500 text-4xl mb-4">⚠️</div>
                <p class="text-gray-600 font-light text-lg">${message}</p>
            </div>
        </div>
    `;
}

function showNoSensorsFound() {
    const element = document.getElementById('sensorConfigList');
    element.innerHTML = `
        <div class="glass-card p-8 flex items-center justify-center min-h-64">
            <div class="text-center">
                <div class="text-gray-400 text-4xl mb-4">🔌</div>
                <p class="text-gray-600 font-light text-lg mb-4">No sensors detected</p>
                <p class="text-gray-500 text-sm">Please connect USB-to-RS485 adapters with sensors</p>
            </div>
        </div>
    `;
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Initialize when sensor tab is shown
function initializeSensorConfig() {
    loadSensorConfigurations();
}