import webview
from config import AUTO_PROGRESS_TIMEOUT
import os

class WebScenarioSelector:
    
    def __init__(self, state_manager):
        self.state_manager = state_manager

    class Api:
        PROJECT_PATH = "/opt/sepnwt/nwt-packet-visualization"

        def __init__(self, state_manager):
            self.state_manager = state_manager
            self.logo_clicks = 0

        def get_max_steps(self):
            return self.state_manager.get_max_steps()

        def start_scenario(self, scenario_id):
            self.state_manager.update_state({"scenario": scenario_id, "step": 0})
            return True
        
        def exit_scenario(self):
            self.state_manager.update_state({"scenario": "", "step": 0})
            return True

        def next_step(self):
            step = self.state_manager.state["step"] + 1
            self.state_manager.update_state({"step": step})
            return step

        def previous_step(self):
            step = max(0, self.state_manager.state["step"] - 1)
            self.state_manager.update_state({"step": step})
            return step
        
        def get_auto_timeout(self):
            return AUTO_PROGRESS_TIMEOUT

        def get_status(self):
            return self.state_manager.state

        def get_image(self):
            return self.state_manager.get_display_image_base64()

        def logo_clicked(self):
            self.logo_clicks += 1
            if self.logo_clicks >= 5:
                self.logo_clicks = 0
                return True
            return False
        
        def check_pin(self, pin):
            return pin == self.ADMIN_PIN
        
        @property
        def ADMIN_PIN(self):
            pin = os.getenv("ADMIN_PIN")
            if not pin:
                raise ValueError("ADMIN_PIN environment variable not set. Please set ADMIN_PIN=your_pin_here")
            return pin
        
        def get_device_list(self):
            from config.rpi_status_config import RPI_HOSTS
            result = [{"name": name} for name in RPI_HOSTS.keys()]
            return result
        
        def get_device_roles(self):
            from config.device_roles import DEVICE_ROLE_MAP
            return DEVICE_ROLE_MAP
        
        def get_single_device_status(self, name):
            from config.rpi_status_config import RPI_HOSTS
            from config.device_roles import DEVICE_ROLE_MAP
            from platform import system
            import subprocess

            ip = RPI_HOSTS.get(name)
            if not ip:
                return {"name": name, "status": "❓", "role": "no role"}

            # 1. Ping prüfen
            param = "-n" if system().lower() == "windows" else "-c"
            try:
                ping_result = subprocess.call(
                    ["ping", param, "1", ip],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=2
                )
                status = "✅" if ping_result == 0 else "❌"
            except Exception:
                status = "❌"

            # 2. Wenn nicht erreichbar → keine Rolle prüfen
            if status != "✅":
                return {"name": name, "status": status, "role": "no role"}

            # 3. Wenn erreichbar → Rolle prüfen via SSH
            try:
                ps_cmd = [
                    "ssh", "-o", "StrictHostKeyChecking=accept-new",
                    f"rpi@{ip}",
                    "ps -eo args | grep '[m]ain_web.py' | grep -v 'ssh'"
                ]
                output = subprocess.check_output(ps_cmd, stderr=subprocess.DEVNULL, timeout=3).decode().strip()

                if not output:
                    return {"name": name, "status": status, "role": "no role"}

                parts = output.split()
                if len(parts) > 2:
                    return {"name": name, "status": status, "role": parts[2].lower()}

                # Kein arg → Hostname verwenden
                hostname = subprocess.check_output(
                    ["ssh", f"rpi@{ip}", "hostname"],
                    stderr=subprocess.DEVNULL,
                    timeout=2
                ).decode().strip().lower()

                return {"name": name, "status": status, "role": DEVICE_ROLE_MAP.get(hostname, "no role")}

            except Exception:
                return {"name": name, "status": status, "role": "no role"}

        def get_all_device_statuses(self):
            from config.rpi_status_config import RPI_HOSTS
            import concurrent.futures

            def check(name):
                return self.get_single_device_status(name)

            results = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
                futures = {executor.submit(check, name): name for name in RPI_HOSTS}
                for future in concurrent.futures.as_completed(futures):
                    try:
                        results.append(future.result())
                    except Exception:
                        results.append({"name": futures[future], "status": "❌", "role": "no role"})
            return results
        
        def remote_reboot(self, name):
            return self._run_ssh_cmd(name, ["sudo", "reboot"])

        def remote_shutdown(self, name):
            return self._run_ssh_cmd(name, ["sudo", "shutdown", "now"])

        def remote_exit(self, name):
            return self._run_ssh_cmd(name, ["pkill", "-f", "main_web.py"])

        def remote_start(self, name, device_type):
            from config.rpi_status_config import RPI_HOSTS
            ip = RPI_HOSTS.get(name)
            if not ip:
                return False

            cmd = f"cd {self.PROJECT_PATH} && python3 main_web.py {device_type}"
            return self._run_ssh_cmd(name, cmd, shell=True) 

        def _run_ssh_cmd(self, name, cmd, shell=False):
            from config.rpi_status_config import RPI_HOSTS
            import subprocess

            ip = RPI_HOSTS.get(name)
            if not ip:
                return False

            if shell:
                ssh_cmd = f'ssh rpi@{ip} "{cmd}"'
            else:
                ssh_cmd = ["ssh", f"rpi@{ip}"] + cmd

            try:
                if shell:
                    subprocess.run(ssh_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
                else:
                    subprocess.run(ssh_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
                return True
            except Exception as e:
                print(f"SSH ERROR: {e}")
                return False


        

    def run(self):
        api = self.Api(self.state_manager)
        try:
            webview.create_window(
                "Packet Visualizer",
                url="ui/web_ui/index.html",
                js_api=api,
                fullscreen=True
            )
            webview.start(debug=False)  # Disable debug to reduce Qt issues
        except Exception as e:
            print(f"[ERROR] Webview failed to start: {e}")
            print("Try installing GTK webview: sudo apt-get install python3-gi gir1.2-webkit2-4.0")
            sys.exit(1)
