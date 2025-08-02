# Changelog

## [2.1.0] - 2025-08-02

### Added
- Support for equipment name-based identification (e.g., "Cooling_Tower_1")
- Auto-detection of equipment type from equipment names
- Better handling of new multi-port monitor output format
- Support for parsing both old sensor address format and new equipment name format

### Changed
- Enhanced console output parser to handle new format: `[OK] 10:01:35 | Cooling_Tower_1 | RMS: 0.0246g | Velocity: 1.28mm/s | ISO Zone: A | Temp: 77.0°F`
- Improved equipment type detection from names (cooling_tower, pump, compressor, fan)
- Generate pseudo-address from equipment name when no address is provided

### Fixed
- Parser now correctly handles equipment names without sensor addresses
- ISO zone parsing improved to handle both "Zone: A" and "ISO Zone: A" formats

## [2.0.2] - Previous version
- Initial release with industrial vibration monitoring support