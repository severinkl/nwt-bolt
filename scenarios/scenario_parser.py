import os
from typing import Dict, List, Optional, Tuple

class ScenarioStep:
    def __init__(self, step: int, device: str, image: Optional[str] = None, 
                 wled: Optional[str] = None, time_sec: float = 5.0, desc: Optional[str] = None):
        self.step = step
        self.device = device
        self.image = image
        self.wled = wled
        self.time_sec = time_sec
        self.desc = desc

class TxtScenario:
    def __init__(self, role: str, txt_file_path: str):
        self.role = role
        self.txt_file_path = txt_file_path
        self.steps: Dict[int, List[ScenarioStep]] = {}
        self.maximum_steps = 0
        self.name = os.path.basename(txt_file_path).replace('.txt', '').replace('_', ' ').title()
        self.description = f"Scenario loaded from {txt_file_path}"
        
        self._parse_txt_file()
        # Add 1 to maximum_steps to account for 0-based indexing but 1-based display
        self.maximum_steps += 1

    def _parse_txt_file(self):
        """Parse the txt file and create scenario steps"""
        if not os.path.exists(self.txt_file_path):
            print(f"Warning: Scenario file {self.txt_file_path} not found")
            return

        with open(self.txt_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):  # Skip empty lines and comments
                continue

            try:
                parts = line.split(';')
                if len(parts) < 2:
                    print(f"Warning: Invalid line {line_num} in {self.txt_file_path}: {line}")
                    continue

                # Parse components
                step = int(parts[0]) if parts[0].strip() else 0
                device = parts[1].strip() if len(parts) > 1 else ""
                image = parts[2].strip() if len(parts) > 2 and parts[2].strip() else None
                wled = parts[3].strip() if len(parts) > 3 and parts[3].strip() else None
                time_sec = float(parts[4]) if len(parts) > 4 and parts[4].strip() else 5.0
                desc = parts[5].strip() if len(parts) > 5 and parts[5].strip() else None

                # Handle special values
                if image == "null":
                    image = None
                if wled == "null":
                    wled = None

                scenario_step = ScenarioStep(step, device, image, wled, time_sec, desc)

                # Group steps by step number
                if step not in self.steps:
                    self.steps[step] = []
                self.steps[step].append(scenario_step)

                # Update maximum steps
                self.maximum_steps = max(self.maximum_steps, step)

            except (ValueError, IndexError) as e:
                print(f"Error parsing line {line_num} in {self.txt_file_path}: {line} - {e}")

    def execute_step(self, step: int) -> Optional[str]:
        """Execute step based on role and return image path"""
        if step not in self.steps:
            return {"type": "image", "content": self._get_default_image()}

        # Find steps for this device/role
        device_steps = [s for s in self.steps[step] if s.device.lower() == self.role.lower()]
        
        if not device_steps:
            return {"type": "image", "content": self._get_default_image()}

        # Use the first matching step for this device
        scenario_step = device_steps[0]

        # Handle WLED commands if present
        if scenario_step.wled:
            self._handle_wled_command(scenario_step.wled)

        # Determine what to return based on image and description
        has_image = scenario_step.image and scenario_step.image.upper() != "TEXT"
        has_description = scenario_step.desc and scenario_step.desc.strip()
        
        if scenario_step.image:
            # Check if it's a text display request
            if scenario_step.image.upper() == "TEXT":
                return {"type": "text", "content": scenario_step.desc or "No description available"}
            
            # Has image - check if we also have description
            image_path = scenario_step.image
            if not image_path.startswith('images/'):
                image_path = f"images/{image_path}"
                
            if has_description:
                return {
                    "type": "image_with_text", 
                    "image": image_path,
                    "text": scenario_step.desc
                }
            else:
                return {"type": "image", "content": image_path}
        elif has_description:
            # Only description, no image
            return {"type": "text", "content": scenario_step.desc}
        
        return {"type": "image", "content": self._get_default_image()}

    def _handle_wled_command(self, wled_command: str):
        """Handle WLED commands like 'client>switch' or 'switch>client'"""
        try:
            from wled_controller import WledController
            
            # Parse direction from command
            if '>' in wled_command:
                source, target = wled_command.split('>')
                source = source.strip().lower()
                target = target.strip().lower()
                
                # Determine if this is reverse direction
                reverse = False
                if source == self.role.lower():
                    # This device is sending, so forward direction
                    reverse = False
                elif target == self.role.lower():
                    # This device is receiving, so reverse direction  
                    reverse = True
                else:
                    return  # Not relevant for this device

                # Map device connections to WLED controllers
                wled_mapping = {
                    ('client', 'switch'): WledController("192.168.50.21", 1),
                    ('switch', 'router'): WledController("192.168.50.21", 2),
                    ('router', 'firewall'): WledController("192.168.50.22", 2),
                    ('firewall', 'server'): WledController("192.168.50.22", 1),
                }

                # Find the appropriate WLED controller
                connection_key = (source, target) if not reverse else (target, source)
                if connection_key in wled_mapping:
                    controller = wled_mapping[connection_key]
                    controller.turn_on(reverse)
                    
        except ImportError:
            print("WLED controller not available")
        except Exception as e:
            print(f"Error handling WLED command '{wled_command}': {e}")

    def _get_default_image(self) -> str:
        """Return default image for the device role"""
        if self.role == "main":
            return "images/000_init.png"
        else:
            return f"images/devices/{self.role}.png"