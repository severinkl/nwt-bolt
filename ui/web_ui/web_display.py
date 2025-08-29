import webview
import sys

class WebDeviceDisplay:
    def __init__(self, state_manager):
        self.state_manager = state_manager

    class Api:
        def __init__(self, get_image_func):
            self.get_image_func = get_image_func

        def get_image(self):
            return self.get_image_func()

    def run(self):
        api = self.Api(self.state_manager.get_display_image_base64)
        try:
            self.window = webview.create_window(
                f"Display: {self.state_manager.role}",
                url="ui/web_ui/display.html",
                js_api=api,
                fullscreen=True
            )
            self.state_manager.set_webview(self.window)

            # Trigger Update, sobald Webview-Fenster läuft
            def on_webview_ready():
                self.state_manager.trigger_webview_update()

            webview.start(on_webview_ready, debug=False)
        except Exception as e:
            print(f"[ERROR] Webview failed to start: {e}")
            print("Try installing GTK webview: sudo apt-get install python3-gi gir1.2-webkit2-4.0")
            sys.exit(1)


