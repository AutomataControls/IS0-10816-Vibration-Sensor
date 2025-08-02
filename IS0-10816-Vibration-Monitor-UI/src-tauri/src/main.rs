// AutomataNexus Universal Vibration Monitor
// Professional Industrial Monitoring Desktop Application
// (c) 2025 AutomataNexus AI & AutomataControls

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}