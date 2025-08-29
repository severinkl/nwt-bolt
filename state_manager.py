import redis
import json
import sys
import os
from config import REDIS_HOST, REDIS_PORT, REDIS_CHANNEL
import tkinter as tk
from PIL import Image, ImageTk


class StateManager:
    def __init__(self, role):
        self.role = role
        self.state = {
            "scenario": "",
            "step": 0
        }
        self.image_label = None

        try:
            self.redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                socket_connect_timeout=2
            )
            self.pubsub = self.redis_client.pubsub()
            self.pubsub.subscribe(REDIS_CHANNEL)
        except redis.ConnectionError as e:
            print(f"\nError: Could not connect to Redis at {REDIS_HOST}:{REDIS_PORT}")
            print("Please ensure that:")
            print("1. Redis server is installed and running")
            print("2. The Redis host and port are correct in config.py")
            print("3. There are no firewall rules blocking the connection")
            print("\nFor development, install and start Redis locally:")
            print("sudo apt-get install redis-server")
            print("sudo systemctl start redis-server")
            sys.exit(1)

        # Create window for image display if not main role
        if role != "main":
            self.setup_display_window()
            # Show initial role image
            self.update_display(f"images/devices/{role}.png")

    def setup_display_window(self):
        """Setup window for displaying network state images"""
        self.window = tk.Tk()
        self.window.title(f"Network State - {self.role.capitalize()}")

        # CH: Fullscreen
        self.window.attributes("-fullscreen", True)
        self.window.bind("<Escape>", lambda e: self.window.destroy())  # optional, for Escape

        self.window.after(3000, lambda: self.window.attributes("-fullscreen", True))
        self.window.after(3300, self.refresh_display_after_fullscreen)

        # CH: Create label for image
        self.image_label = tk.Label(self.window)
        self.image_label.pack(fill="both", expand=True, padx=10, pady=10)

    def refresh_display_after_fullscreen(self):
        """Re-display the image to ensure proper scaling after fullscreen is applied"""
        if self.state["scenario"]:
            self.handle_state_change()  # Trigger scenario image update
        else:
            self.update_display(f"images/devices/{self.role}.png")  # Role image


    def update_state(self, new_state):
        """Update local state and broadcast to other nodes"""
        self.state.update(new_state)
        try:
            self.broadcast_state()
            # Update own display immediately after state change
            self.handle_state_change()
        except redis.ConnectionError:
            print("Warning: Could not broadcast state update - Redis connection failed")

    def broadcast_state(self):
        """Broadcast state to all other nodes"""
        message = {
            "source_role": self.role,
            "state": self.state,
            "command": "update_state" if self.state["scenario"] else "show_role_image"
        }
        try:
            self.redis_client.publish(REDIS_CHANNEL, json.dumps(message))
        except redis.ConnectionError as e:
            raise e

    def listen_for_updates(self):
        """Listen for state updates from other nodes"""
        try:
            for message in self.pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    if data["source_role"] != self.role:  # Ignore own messages
                        if data.get("command") == "show_role_image":
                            self.update_display(f"images/devices/{self.role}.png")
                        else:
                            self.state = data["state"]
                            self.handle_state_change()
        except redis.ConnectionError:
            print("Error: Lost connection to Redis server")
            sys.exit(1)

    def handle_state_change(self):
        scenario = self.state["scenario"]
        step = self.state["step"]

        if scenario:
            if not hasattr(self, 'current_handler') or self.state["scenario"] != self.state.get("last_scenario"):
                self.current_handler = self.load_scenario(scenario)
                self.state["last_scenario"] = scenario

            result = self.current_handler.execute_step(step)

            # Handle different result types
            if isinstance(result, dict):
                if result["type"] == "text":
                    self.display_text(result["content"])
                    return
                elif result["type"] == "image_with_text":
                    self.display_image_with_text(result["image"], result["text"])
                    return
                elif result["type"] == "image":
                    image_path = result["content"]
                else:
                    image_path = self._get_default_image()
            else:
                # Backward compatibility for old string returns
                if result and result.startswith("TEXT:"):
                    text_content = result[5:]  # Remove "TEXT:" prefix
                    self.display_text(text_content)
                    return
                image_path = result

            if image_path == 'images/black.png':
                # set background to black as well
                if hasattr(self, 'window'):
                    self.window.configure(bg='black')
                if self.image_label:
                    self.image_label.configure(bg='black')
            else:
                # set background to default
                if hasattr(self, 'window'):
                    self.window.configure(bg='#ffffff')
                if self.image_label:
                    self.image_label.configure(bg='#ffffff')

            if image_path:
                self.update_display(image_path)

    def load_scenario(self, scenario_name):
        """Dynamically load scenario module"""
        # Check if it's a txt file scenario first
        txt_file_path = f"scenarios/{scenario_name}.txt"
        if os.path.exists(txt_file_path):
            from scenarios.scenario_parser import TxtScenario
            return TxtScenario(self.role, txt_file_path)
        else:
            # Fall back to Python module for backward compatibility
            try:
                module = __import__(f"scenarios.{scenario_name}", fromlist=["Scenario"])
                return module.Scenario(self.role)
            except ImportError:
                print(f"Error: Could not load scenario '{scenario_name}' as txt or Python file")
                return None

    def scale_image(self, image):
        if not hasattr(self, 'window') or not self.image_label:
            return image

        self.window.update_idletasks()
        label_width = self.image_label.winfo_width() or 800
        label_height = self.image_label.winfo_height() or 600

        width_ratio = label_width / image.width
        height_ratio = label_height / image.height
        scale_ratio = min(width_ratio, height_ratio)

        new_width = int(image.width * scale_ratio)
        new_height = int(image.height * scale_ratio)

        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def update_display(self, image_path):
        try:
            image = Image.open(image_path)

            if not hasattr(self, 'window') or not self.image_label:
                return

            image = self.scale_image(image)
            photo = ImageTk.PhotoImage(image)

            self.image_label.configure(image=photo)
            self.image_label.image = photo

            self.window.update()
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")

    def display_text(self, text_content):
        """Display text instead of an image"""
        if not hasattr(self, 'window') or not self.image_label:
            return

        try:
            # Clear any existing image
            self.image_label.configure(image="")
            self.image_label.image = None
            
            # Configure label for text display
            self.image_label.configure(
                text=text_content,
                font=('Helvetica', 36, 'bold'),
                foreground='#005097',
                background='#ffffff',
                wraplength=800,
                justify='center',
                anchor='center'
            )
            
            self.window.update()
        except Exception as e:
            print(f"Error displaying text: {e}")

    def display_image_with_text(self, image_path, text_content):
        """Display text above an image"""
        if not hasattr(self, 'window'):
            return
            
        try:
            # Clear the current image label
            self.image_label.configure(image="", text="")
            self.image_label.image = None
            
            # Create a frame to hold both text and image
            if hasattr(self, 'content_frame'):
                self.content_frame.destroy()
                
            self.content_frame = tk.Frame(self.window, bg='#ffffff')
            self.content_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Add text label at the top
            text_label = tk.Label(
                self.content_frame,
                text=text_content,
                font=('Helvetica', 36, 'bold'),
                foreground='#005097',
                background='#ffffff',
                wraplength=800,
                justify='center'
            )
            text_label.pack(pady=(0, 20))
            
            # Add image label below
            image_label = tk.Label(self.content_frame, bg='#ffffff')
            image_label.pack(fill="both", expand=True)
            
            # Load and display the image
            image = Image.open(image_path)
            image = self.scale_image(image)
            photo = ImageTk.PhotoImage(image)
            
            image_label.configure(image=photo)
            image_label.image = photo
            
            self.window.update()
            
        except Exception as e:
            print(f"Error displaying image with text: {e}")
            # Fallback to just showing the image
            self.update_display(image_path)

    def _get_default_image(self):
        """Return default image for the device role"""
        if self.role == "main":
            return "images/000_init.png"
        else:
            return f"images/devices/{self.role}.png"

    def run_display(self):
        if self.role != "main":
            try:
                self.window.mainloop()
            except Exception as e:
                print(f"Display error: {e}")
