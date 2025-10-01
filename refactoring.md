## Refactoring Plan: Moving Application Logic from SystemTray to NormcapApp

### **Phase 1: Foundation Setup**

#### **Subtask 1.1: Create NormcapApp skeleton class**
- **Goal**: Create a new `NormcapApp(QtWidgets.QApplication)` class with basic structure
- **What to do**:
  - [x] Create new file app.py with `NormcapApp` class inheriting from `QtWidgets.QApplication`
  - [x] Move the `Communicate` class from tray.py to the new app.py as it represents application-wide communication
  - [x] Add basic initialization accepting the same `args` parameter
  - [x] Update app.py to use `NormcapApp` instead of generic `QtWidgets.QApplication`
- **Why safe**: Only structural changes, no behavior changes
- **Testing**: Application should start and work exactly as before

#### **Subtask 1.2: Move singleton management to NormcapApp**
- **Goal**: Transfer single-instance logic from SystemTray to NormcapApp
- **What to do**:
  - [x] Move socket-related attributes (`_socket_name`, `_socket_out`, `_socket_in`, `_socket_server`) to NormcapApp
  - [x] Move methods: `_create_socket_server()`, `_ensure_single_instance()`, `_on_new_connection()`, `_on_ready_read()`
  - [x] Update socket message handling to trigger SystemTray methods through signals
  - [x] SystemTray should connect to NormcapApp's signal for "capture" requests
- **Why safe**: Singleton logic is independent of tray functionality
- **Testing**: Single instance behavior should work the same, new instances should trigger capture

### **Phase 2: Move Core Application State**

#### **Subtask 2.1: Move settings and core state to NormcapApp**
- **Goal**: Transfer application-wide state management
- **What to do**:
  - [x] Move `settings`, `screens`, `installed_languages` to NormcapApp
  - [x] Move CLI argument processing (`cli_mode`, handler names, `reset` logic)
  - [x] Move constants (`_EXIT_DELAY`, `_UPDATE_CHECK_INTERVAL`)
  - [x] Update SystemTray to receive these via constructor or property access
  - [x] Move `_testing_language_manager` flag to NormcapApp
- **Why safe**: Only moving data, not changing how it's used
- **Testing**: All settings and preferences should work as before

#### **Subtask 2.2: Move window management to NormcapApp**
- **Goal**: Transfer window lifecycle management
- **What to do**:
  - [x] Move `windows` dictionary to NormcapApp
  - [x] Move methods: `_show_windows()`, `_close_windows()`, `_create_window()`, `_create_menu_button()`, `_create_layout()`
  - [x] Move screenshot handling: `_take_screenshots()`
  - [x] SystemTray should request window operations through NormcapApp methods
  - [x] Keep tray-specific UI (context menu) in SystemTray
- **Why safe**: Window management is logically separate from tray icon
- **Testing**: Screenshot capture and window display should work normally

### **Phase 3: Move Business Logic**

#### **Subtask 3.1: Move OCR detection pipeline to NormcapApp**
- **Goal**: Transfer core OCR and text detection functionality
- **What to do**:
  - [x] Move methods: `_schedule_detection()`, `_trigger_detect()`
  - [x] Move clipboard operations: `_copy_to_clipboard()`, `_print_to_stdout_and_exit()`
  - [x] Move notification handling: `_send_notification()`
  - [x] SystemTray should connect to NormcapApp signals for region selection and trigger detection through app
- **Why safe**: Detection logic is pure business logic, independent of tray
- **Testing**: Text detection, clipboard copying, and notifications should work identically

#### **Subtask 3.2: Move language and update management to NormcapApp**
- **Goal**: Transfer language management and update checking
- **What to do**:
  - [x] Move methods: `_delayed_init()`, `_sanitize_language_setting()`, `_update_installed_languages()`
  - [x] Move language manager: `_open_language_manager()`
  - [x] Move update checker: `_add_update_checker()`, `_update_time_of_last_update_check()`
  - [x] Move URL handling: `_open_url_and_hide()`
  - [x] Update signal connections to flow through NormcapApp
- **Why safe**: These are application-wide features, not tray-specific
- **Testing**: Language switching, language manager, and update checks should function normally

### **Phase 4: Move System Integration**

#### **Subtask 4.1: Move DBus and permissions handling to NormcapApp**
- **Goal**: Transfer system-level integration
- **What to do**:
  - [x] Move DBus service: `dbus_service`, `_get_dbus_service()`, `_handle_action_activate()`
  - [x] Move permissions handling: `show_permissions_info()`
  - [x] Move introduction dialog: `show_introduction()`
  - [x] Keep these accessible to SystemTray through NormcapApp reference
- **Why safe**: System integration is application-level, not tray-specific
- **Testing**: DBus activation, permissions prompts, and introduction should work as before

#### **Subtask 4.2: Move application lifecycle management to NormcapApp**
- **Goal**: Transfer exit and lifecycle control
- **What to do**:
  - [x] Move methods: `_minimize_or_exit_application()`, `_exit_application()`, `hide()`
  - [x] Move timers: `delayed_exit_timer`, `delayed_init_timer`
  - [x] Move application exit logic and cleanup
  - [ ] SystemTray should request app exit through NormcapApp methods
  - [x] Override QApplication's exit behavior in NormcapApp
- **Why safe**: Application lifecycle is naturally QApplication's responsibility
- **Testing**: Exit behavior, timers, and cleanup should work identically

### **Phase 5: Clean Up SystemTray**

#### **Subtask 5.1: Refactor SystemTray to UI-only component**
- **Goal**: Make SystemTray focus only on tray icon and menu
- **What to do**:
  - [x] Keep only tray icon management: `_set_tray_icon_normal()`, `_set_tray_icon_done()`, icon enum
  - [x] Keep only tray menu: `_populate_context_menu_entries()`, `_handle_tray_click()`, `_apply_setting_change()`
  - [x] Keep only tray-specific timers: `reset_tray_icon_timer`
  - [x] Update signal connections to communicate with NormcapApp
  - [x] Remove all non-tray logic from SystemTray
- **Why safe**: Clearly separates UI concerns from business logic
- **Testing**: Tray icon, context menu, and tray interactions should work normally

#### **Subtask 5.2: Final cleanup and optimization**
- **Goal**: Optimize the new structure and clean up imports
- **What to do**:
  - [ ] Review and optimize signal connections between NormcapApp and SystemTray
  - [ ] Clean up imports in both files
  - [ ] Update documentation and docstrings
  - [ ] Ensure proper error handling across the boundary
  - [ ] Add type hints where needed
- **Why safe**: Only cleanup and optimization, no functional changes
- **Testing**: Full application functionality test, especially edge cases and error conditions

### **Key Benefits of This Approach:**

1. **Incremental**: Each subtask is small and testable
2. **Reversible**: Changes can be backed out easily if issues arise
3. **Logical**: Follows natural separation of concerns (UI vs business logic vs system integration)
4. **Maintainable**: Results in cleaner, more maintainable code architecture
5. **Testable**: Each phase maintains working application state

### **Testing Strategy for Each Subtask:**
- Run the application after each subtask
- Test main user flows: capture text, tray interactions, settings changes
- Verify edge cases: single instance, permissions, error conditions
- Check that no regressions are introduced

This plan should result in a clean separation where `NormcapApp` handles all application logic, state, and system integration, while `SystemTray` focuses solely on tray icon presentation and user interactions.
