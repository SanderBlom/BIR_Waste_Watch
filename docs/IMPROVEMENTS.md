# BIR Waste Watch - Improvement Analysis

Analysis performed: January 2, 2026

---

## 🔴 Priority 1: Critical Bugs

### 1. Duplicate `return True` statement in `__init__.py`
- **Location**: Lines 64-67
- **Issue**: Two consecutive `return True` statements - the second is unreachable dead code
- **Impact**: Minor (no runtime issue), but poor code quality
- **Branch**: `fix/duplicate-return-statement`

### 2. Sensors don't dynamically update when new waste types appear
- **Location**: `sensor.py` - `async_setup_entry`
- **Issue**: Only creates sensors for waste types present at startup. If the API returns new waste types later, no sensors are created for them
- **Impact**: Missing data after config changes
- **Branch**: `fix/dynamic-sensor-creation`

---

## 🟠 Priority 2: Reliability & Robustness

### 3. No timeout on API requests
- **Location**: `coordinator.py` - `_login` and `_fetch_pickup_dates`
- **Issue**: `aiohttp` requests have no explicit timeout. A hanging API could block the event loop
- **Fix**: Add `timeout=aiohttp.ClientTimeout(total=30)`
- **Branch**: `fix/api-request-timeouts`

### 4. `_process_pickup_data` uses `datetime.today()` instead of coordinator's update time
- **Location**: `coordinator.py` - `_process_pickup_data`
- **Issue**: Can cause inconsistencies if processing spans midnight
- **Fix**: Should use a consistent timestamp passed from the calling method
- **Branch**: `fix/consistent-datetime-handling`

---

## 🟡 Priority 3: Home Assistant Best Practices

### 5. Sensors should use proper device classes
- **Location**: `sensor.py` - `BIRWasteDateSensor`
- **Issue**: Should use `device_class=SensorDeviceClass.DATE`
- **Impact**: Enables better frontend display and statistics
- **Branch**: `fix/sensor-device-class`

### 6. Translation files are inconsistent
- **Location**: `strings.json` and `translations/en.json`
- **Issue**: Different content between files, `en.json` is missing entity translations and `cannot_connect` error
- **Branch**: `fix/sync-translations`

### 7. Missing options flow for reconfiguration
- **Location**: `config_flow.py`
- **Issue**: Users can't update the URL without removing and re-adding the integration
- **Fix**: Add `async_step_reconfigure` or options flow
- **Branch**: `feature/reconfigure-flow`

### 8. No diagnostics support
- **Location**: Missing `diagnostics.py`
- **Issue**: No easy way to debug issues via HA's diagnostics download
- **Fix**: Add diagnostics platform with redacted sensitive data
- **Branch**: `feature/diagnostics-support`

---

## 🟢 Priority 4: Code Quality & Maintainability

### 9. Hard-coded magic numbers
- **Location**: `coordinator.py` - `timedelta(days=95)`
- **Issue**: Magic number for lookup window
- **Fix**: Move to `const.py` as `PICKUP_LOOKUP_DAYS`
- **Branch**: `fix/extract-magic-numbers`

### 10. Unused constants in `const.py`
- **Location**: `const.py`
- **Issue**: `SENSOR_TYPE_DATE`, `SENSOR_TYPE_DAYS`, `ATTR_*` constants are defined but never used
- **Branch**: `fix/remove-unused-constants`

### 11. Missing Norwegian translation
- **Location**: `translations/`
- **Issue**: This is a Norwegian service but lacks native language support
- **Branch**: `feature/norwegian-translation`

### 12. Consider calendar platform
- **Issue**: Waste pickup dates are calendar events by nature. HA's calendar integration would provide a better UX
- **Branch**: `feature/calendar-platform`

---

## 📋 Implementation Progress

| # | Task | Branch | Status |
|---|------|--------|--------|
| 1 | Fix duplicate `return True` | `fix/duplicate-return-statement` | ✅ Done |
| 2 | Dynamic sensor creation | `fix/dynamic-sensor-creation` | ⬜ Todo |
| 3 | Add API request timeouts | `fix/api-request-timeouts` | ✅ Done |
| 4 | Consistent datetime handling | `fix/consistent-datetime-handling` | ✅ Done |
| 5 | Add sensor device class | `fix/sensor-device-class` | ✅ Done |
| 6 | Sync translation files | `fix/sync-translations` | ✅ Done |
| 7 | Add reconfigure flow | `feature/reconfigure-flow` | ⬜ Todo |
| 8 | Add diagnostics support | `feature/diagnostics-support` | ⬜ Todo |
| 9 | Extract magic numbers | `fix/extract-magic-numbers` | ✅ Done |
| 10 | Remove unused constants | `fix/remove-unused-constants` | ✅ Done |
| 11 | Norwegian translation | `feature/norwegian-translation` | ✅ Done |
| 12 | Calendar platform | `feature/calendar-platform` | ⬜ Todo |
