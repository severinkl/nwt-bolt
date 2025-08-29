import redis
import webview
import json
import sys
import os
from config import REDIS_HOST, REDIS_PORT, REDIS_CHANNEL
from PIL import Image, ImageDraw, ImageFont
import base64
from io import BytesIO

class StateManager:
    def __init__(self, role, display_mode="web"):
        self.role = role
        self.display_mode = display_mode
        self.state = {
            "scenario": "",
            "step": 0
        }
        self.current_handler = None

        try:
            self.redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                socket_connect_timeout=2
            )
            self.pubsub = self.redis_client.pubsub()
            self.pubsub.subscribe(REDIS_CHANNEL)
        except redis.ConnectionError:
            print(f"[ERROR] Redis-Verbindung fehlgeschlagen ({REDIS_HOST}:{REDIS_PORT})")
            sys.exit(1)

    def update_state(self, new_state):
        self.state.update(new_state)
        try:
            self.broadcast_state()
            self.handle_state_change()
        except redis.ConnectionError:
            print("[WARN] Redis: Status konnte nicht gesendet werden")

    def broadcast_state(self):
        message = {
            "source_role": self.role,
            "state": self.state,
            "command": "update_state" if self.state["scenario"] else "show_role_image"
        }
        self.redis_client.publish(REDIS_CHANNEL, json.dumps(message))

    def listen_for_updates(self):
        try:
            for message in self.pubsub.listen():
                if message["type"] != "message":
                    continue
                data = json.loads(message["data"])
                if data["source_role"] == self.role:
                    continue
                if data.get("command") == "show_role_image":
                    self.state = {"scenario": "", "step": 0}
                    self.current_handler = None
                    self.trigger_webview_update()
                else:
                    self.state = data["state"]
                    self.handle_state_change()
        except redis.ConnectionError:
            print("[ERROR] Redis-Verbindung verloren")
            sys.exit(1)

    def trigger_webview_update(self):
        if hasattr(self, 'webview_window'):
            try:
                self.webview_window.evaluate_js('updateImage()')
            except Exception as e:
                print(f"[WARN] JS-Update fehlgeschlagen: {e}")


    def handle_state_change(self):
        scenario = self.state["scenario"]
        step = self.state["step"]

        if scenario:
            if not self.current_handler or scenario != self.state.get("last_scenario"):
                self.current_handler = self.load_scenario(scenario)
                self.state["last_scenario"] = scenario

            result = self.current_handler.execute_step(step)
            
            # Store the result for web display
            self.current_display_content = result

        self.trigger_webview_update()


    def load_scenario(self, scenario_name):
        """Load scenario from text file or fall back to Python module"""
        txt_file_path = f"scenarios/{scenario_name}.txt"
        if os.path.exists(txt_file_path):
            from scenarios.scenario_parser import TxtScenario
            return TxtScenario(self.role, txt_file_path)
        else:
            # Fall back to Python module for legacy scenarios
            try:
                module = __import__(f"scenarios.{scenario_name}", fromlist=["Scenario"])
                return module.Scenario(self.role)
            except ImportError:
                print(f"Error: Could not load scenario '{scenario_name}'. Please ensure the scenario file exists as either {scenario_name}.txt or {scenario_name}.py")
                return None

    def scale_image(self, image, width, height):
        width_ratio = width / image.width
        height_ratio = height / image.height
        scale_ratio = min(width_ratio, height_ratio)
        new_size = (int(image.width * scale_ratio), int(image.height * scale_ratio))
        return image.resize(new_size, Image.Resampling.LANCZOS)

    def run_display(self):
        if self.role == "main":
            return

        if self.display_mode == "web":
            try:
                from ui.web_ui.web_display import WebDeviceDisplay
                WebDeviceDisplay(self).run()
            except Exception as e:
                print(f"[ERROR] Webview Display: {e}")

    def set_webview(self, webview_window):
        self.webview_window = webview_window

    def get_display_image_base64(self):
        if hasattr(self, 'current_display_content') and self.current_display_content:
            content = self.current_display_content
        else:
            if self.state["scenario"] and self.current_handler:
                content = self.current_handler.execute_step(self.state["step"])
            else:
                content = {"type": "image", "content": f"images/devices/{self.role}.png"}

        # Handle different content types
        if isinstance(content, dict):
            if content["type"] == "text":
                return self.create_text_image_base64(content["content"])
            elif content["type"] == "image_with_text":
                return self.create_image_with_text_base64(content["image"], content["text"])
            elif content["type"] == "image":
                image_path = content["content"]
            else:
                image_path = f"images/devices/{self.role}.png"
        else:
            # Backward compatibility for old string returns
            if content and content.startswith("TEXT:"):
                text_content = content[5:]  # Remove "TEXT:" prefix
                return self.create_text_image_base64(text_content)
            image_path = content or f"images/devices/{self.role}.png"

        try:
            img = Image.open(image_path)
            img = self.scale_image(img, 1280, 720)
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            return f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode('utf-8')}"
        except Exception as e:
            print(f"[ERROR] Image to Base64 failed: {e}")
            return ""

    def get_max_steps(self):
        if self.current_handler:
            return getattr(self.current_handler, "maximum_steps", 1)
        return 1

    def create_text_image_base64(self, text_content):
        """Create a base64 image from text content"""
        try:
            # Create a white image
            img_width, img_height = 1280, 720
            img = Image.new('RGB', (img_width, img_height), color='white')
            draw = ImageDraw.Draw(img)
            
            # Text color (FHSTP blue)
            text_color = '#005097'
            
            # Prepare text lines
            original_lines = text_content.split('\n')
            
            # Try different font sizes to fit content
            font_sizes = [48, 36, 28, 24, 20, 16]
            font = None
            wrapped_lines = []
            
            for font_size in font_sizes:
                # Try to use a nice font, fall back to default if not available
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
                except:
                    try:
                        font = ImageFont.truetype("arial.ttf", font_size)
                    except:
                        font = ImageFont.load_default()
                
                # Wrap text to fit width
                wrapped_lines = []
                max_width = img_width - 80  # Leave 40px margin on each side
                
                for line in original_lines:
                    if not line.strip():
                        wrapped_lines.append("")
                        continue
                        
                    # Check if line fits
                    bbox = draw.textbbox((0, 0), line, font=font)
                    line_width = bbox[2] - bbox[0]
                    
                    if line_width <= max_width:
                        wrapped_lines.append(line)
                    else:
                        # Wrap long lines
                        words = line.split()
                        current_line = ""
                        
                        for word in words:
                            test_line = current_line + (" " if current_line else "") + word
                            bbox = draw.textbbox((0, 0), test_line, font=font)
                            test_width = bbox[2] - bbox[0]
                            
                            if test_width <= max_width:
                                current_line = test_line
                            else:
                                if current_line:
                                    wrapped_lines.append(current_line)
                                current_line = word
                        
                        if current_line:
                            wrapped_lines.append(current_line)
                
                # Check if all lines fit vertically
                line_height = font_size + 10
                total_height = len(wrapped_lines) * line_height
                max_height = img_height - 80  # Leave 40px margin top and bottom
                
                if total_height <= max_height:
                    break  # This font size works
            
            # If no font size worked, use the smallest and truncate
            if total_height > max_height:
                max_lines = int(max_height / line_height)
                wrapped_lines = wrapped_lines[:max_lines]
                if len(original_lines) > max_lines:
                    wrapped_lines[-1] = wrapped_lines[-1][:50] + "..."
            
            # Calculate text positioning for center alignment
            line_height = (font.size if hasattr(font, 'size') else 24) + 10
            total_height = len(wrapped_lines) * line_height
            start_y = (img_height - total_height) // 2
            
            for i, line in enumerate(wrapped_lines):
                if line.strip():  # Skip empty lines
                    # Get text bounding box for centering
                    bbox = draw.textbbox((0, 0), line, font=font)
                    text_width = bbox[2] - bbox[0]
                    x = (img_width - text_width) // 2
                    y = start_y + i * line_height
                    
                    draw.text((x, y), line, fill=text_color, font=font)
            
            # Convert to base64
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            return f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode('utf-8')}"
            
        except Exception as e:
            print(f"[ERROR] Text to image conversion failed: {e}")
            # Return a simple fallback
            return ""

    def create_image_with_text_base64(self, image_path, text_content):
        """Create a base64 image with text above an image"""
        try:
            # Load the original image
            original_img = Image.open(image_path)
            
            # Create canvas with extra space for text
            canvas_width = 1280
            canvas_height = 720
            text_height = 150  # Space reserved for text
            
            # Scale the original image to fit in the remaining space
            available_height = canvas_height - text_height
            img_scale_ratio = min(canvas_width / original_img.width, available_height / original_img.height)
            scaled_img_width = int(original_img.width * img_scale_ratio)
            scaled_img_height = int(original_img.height * img_scale_ratio)
            scaled_img = original_img.resize((scaled_img_width, scaled_img_height), Image.Resampling.LANCZOS)
            
            # Create the final canvas
            canvas = Image.new('RGB', (canvas_width, canvas_height), color='white')
            draw = ImageDraw.Draw(canvas)
            
            # Add text at the top
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
            except:
                try:
                    font = ImageFont.truetype("arial.ttf", 36)
                except:
                    font = ImageFont.load_default()
            
            # Text color (FHSTP blue)
            text_color = '#005097'
            
            # Calculate text positioning for center alignment
            lines = text_content.split('\n')
            line_height = 40
            total_text_height = len(lines) * line_height
            start_y = (text_height - total_text_height) // 2
            
            for i, line in enumerate(lines):
                if line.strip():  # Skip empty lines
                    # Get text bounding box for centering
                    bbox = draw.textbbox((0, 0), line, font=font)
                    text_width = bbox[2] - bbox[0]
                    x = (canvas_width - text_width) // 2
                    y = start_y + i * line_height
                    
                    draw.text((x, y), line, fill=text_color, font=font)
            
            # Add the scaled image below the text
            img_x = (canvas_width - scaled_img_width) // 2
            img_y = text_height + (available_height - scaled_img_height) // 2
            canvas.paste(scaled_img, (img_x, img_y))
            
            # Convert to base64
            buffered = BytesIO()
            canvas.save(buffered, format="PNG")
            return f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode('utf-8')}"
            
        except Exception as e:
            print(f"[ERROR] Image with text conversion failed: {e}")
            # Fallback to just the image
            try:
                img = Image.open(image_path)
                img = self.scale_image(img, 1280, 720)
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                return f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode('utf-8')}"
            except:
                return ""
