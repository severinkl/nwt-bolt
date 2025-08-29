from config.device_roles import DEVICE_ROLE_MAP
import sys
import socket
import threading

from ui.web_ui.selector import WebScenarioSelector
from ui.web_ui.web_display import WebDeviceDisplay

from state_manager_web import StateManager


def main():
    allowed_roles = set(DEVICE_ROLE_MAP.values())

    if len(sys.argv) == 2:
        role = sys.argv[1].lower()
        if role not in allowed_roles:
            print(f"[ERROR] Ungültige Rolle '{role}'. Erlaubte Rollen: {sorted(allowed_roles)}")
            sys.exit(1)
    else:
        hostname = socket.gethostname().lower()
        role = DEVICE_ROLE_MAP.get(hostname)
        if not role:
            print(f"[ERROR] Kein Eintrag für Hostname '{hostname}' gefunden.")
            sys.exit(1)
        print(f"[INFO] Starte automatisch mit Rolle '{role}' für Hostname '{hostname}'")

    state_manager = StateManager(role, display_mode="web")

    # Start listening for state updates in a separate thread
    listener_thread = threading.Thread(
        target=state_manager.listen_for_updates,
        daemon=True
    )
    listener_thread.start()

    # Only show UI for main role
    if role == "main":
        selector = WebScenarioSelector(state_manager)
        selector.run()
    else:
        display = WebDeviceDisplay(state_manager)
        display.run()

if __name__ == "__main__":
    main()