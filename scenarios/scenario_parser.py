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
        
        # Extract name from filename
        filename = os.path.basename(txt_file_path)
        self.name = filename.replace('.txt', '').replace('_', ' ').title()
        self.description = f"Scenario loaded from {filename}"
        
        self._parse_txt_file()

    def _parse_txt_file(self):
        """Parse the txt file and create scenario steps"""
        if not os.path.exists(self.txt_file_path):
            print(f"Warning: Scenario file {self.txt_file_path} not found")
            return

        with open(self.txt_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # First pass: collect all valid steps
        valid_steps = set()

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue

            try:
                # Split by semicolon and handle empty fields
                parts = [part.strip() for part in line.split(';')]
                
                # Ensure we have at least step and device
                if len(parts) < 2:
                    print(f"Warning: Invalid line {line_num} in {self.txt_file_path}: {line}")
                    continue

                # Parse required fields
                step = int(parts[0]) if parts[0] else 0
                device = parts[1] if parts[1] else ""
                
                if not device:
                    print(f"Warning: Missing device on line {line_num}: {line}")
                    continue

                # Parse optional fields with defaults
                image = parts[2] if len(parts) > 2 and parts[2] and parts[2].lower() != 'null' else None
                wled = parts[3] if len(parts) > 3 and parts[3] and parts[3].lower() != 'null' else None
                
                # Handle time_sec with default
                time_sec = 5.0
                if len(parts) > 4 and parts[4]:
                    try:
                        time_sec = float(parts[4])
                    except ValueError:
                        print(f"Warning: Invalid time_sec on line {line_num}, using default 5.0")
                
                desc = parts[5] if len(parts) > 5 and parts[5] else None

                # Create scenario step
                scenario_step = ScenarioStep(step, device, image, wled, time_sec, desc)

                # Group steps by step number
                if step not in self.steps:
                    self.steps[step] = []
                self.steps[step].append(scenario_step)

                # Mark this step as valid
                valid_steps.add(step)

            except (ValueError, IndexError) as e:
                print(f"Error parsing line {line_num} in {self.txt_file_path}: {line} - {e}")

        # Create ordered list of valid steps for navigation
        self.valid_steps = sorted(valid_steps)
        self.maximum_steps = len(self.valid_steps)
        # Ensure we have at least one step
        if self.maximum_steps == 0:
            self.maximum_steps = 1
            self.valid_steps = [0]

    def get_actual_step_number(self, navigation_step: int) -> int:
        """Convert navigation step (0-based index) to actual step number"""
        if navigation_step < 0 or navigation_step >= len(self.valid_steps):
            return 0
        return self.valid_steps[navigation_step]

    def get_navigation_step(self, actual_step: int) -> int:
        """Convert actual step number to navigation step (0-based index)"""
        try:
            return self.valid_steps.index(actual_step)
        except ValueError:
            return 0

    def execute_step(self, step: int) -> Optional[Dict]:
        """Execute step based on role and return display content"""
        # Convert navigation step to actual step number
        actual_step = self.get_actual_step_number(step)
        
        # Handle step 0 or steps not in our scenario
        if actual_step not in self.steps:
            return self._get_default_display()

        # Find steps for this device/role
        device_steps = [s for s in self.steps[actual_step] 
                       if s.device.lower() == self.role.lower() or s.device.lower() == 'all']
        
        # Special handling for main role - show descriptions if no main image specified
        if not device_steps and self.role.lower() == 'main':
            # Look for any step with a description in this step number
            steps_with_desc = [s for s in self.steps[actual_step] if s.desc and s.desc.strip()]
            if steps_with_desc:
                # Use the first description found
                desc_step = steps_with_desc[0]
                return {
                    "type": "text",
                    "content": desc_step.desc
                }
            else:
                # No description found and no main image - show nothing
                return {
                    "type": "empty"
                }
        
        if not device_steps:
            # For non-main roles, show default display
            if self.role.lower() != 'main':
                return self._get_default_display()
            else:
                # For main role with no content, show nothing
                return {
                    "type": "empty"
                }

        # Use the first matching step for this device
        scenario_step = device_steps[0]

        # Handle WLED commands if present
        if scenario_step.wled:
            self._handle_wled_command(scenario_step.wled)

        # Check if main role will show this step's description
        # If so, don't show description on the original device
        if self.role.lower() != 'main':
            main_steps = [s for s in self.steps[actual_step] if s.device.lower() == 'main']
            if not main_steps:
                # Main has no image for this step, so it will show our description
                # We should not show the description on this device
                steps_with_desc = [s for s in self.steps[actual_step] if s.desc and s.desc.strip()]
                if steps_with_desc and scenario_step.desc:
                    # Create a copy without description to avoid showing it twice
                    scenario_step = ScenarioStep(
                        scenario_step.step,
                        scenario_step.device,
                        scenario_step.image,
                        scenario_step.wled,
                        scenario_step.time_sec,
                        None  # Remove description
                    )
        
        # Determine what to return based on content
        return self._create_display_content(scenario_step)

    def _create_display_content(self, scenario_step: ScenarioStep) -> Dict:
        """Create appropriate display content based on scenario step"""
        has_image = scenario_step.image and scenario_step.image.upper() != "TEXT"
        has_description = scenario_step.desc and scenario_step.desc.strip()
        
        # Handle special text-only display
        if scenario_step.image and scenario_step.image.upper() == "TEXT":
            return {
                "type": "text", 
                "content": scenario_step.desc or "No description available"
            }
        
        # Handle image with optional description
        if has_image:
            image_path = scenario_step.image
            
            # Ensure proper image path
            if not image_path.startswith('images/'):
                image_path = f"images/{image_path}"
                
            if has_description:
                return {
                    "type": "image_with_text", 
                    "image": image_path,
                    "text": scenario_step.desc
                }
            else:
                return {
                    "type": "image", 
                    "content": image_path
                }
        
        # Handle description-only display
        elif has_description:
            return {
                "type": "text", 
                "content": scenario_step.desc
            }
        
        # Fallback to default display
        return self._get_default_display()

    def _handle_wled_command(self, wled_command: str):
        """Handle WLED commands like 'client>switch' or 'switch>client'"""
        try:
            from wled_controller import WledController
            
            # Parse direction from command
            if '>' in wled_command:
                source, target = wled_command.split('>', 1)
                source = source.strip().lower()
                target = target.strip().lower()
                
                # Determine if this device should handle the command
                if source != self.role.lower() and target != self.role.lower():
                    return  # Not relevant for this device

                # Determine direction
                reverse = target == self.role.lower()

                # Map device connections to WLED controllers
                wled_mapping = {
                    ('client', 'switch'): WledController("192.168.50.21", 1),
                    ('switch', 'router'): WledController("192.168.50.21", 2),
                    ('router', 'firewall'): WledController("192.168.50.22", 2),
                    ('firewall', 'server'): WledController("192.168.50.22", 1),
                    ('router', 'dns'): WledController("192.168.50.23", 1),
                    ('dns', 'router'): WledController("192.168.50.23", 1),
                }

                # Find the appropriate WLED controller
                connection_key = (source, target)
                if connection_key in wled_mapping:
                    controller = wled_mapping[connection_key]
                    controller.turn_on(reverse)
                    print(f"WLED: {source} -> {target} (reverse: {reverse})")
                    
        except ImportError:
            print("WLED controller not available")
        except Exception as e:
            print(f"Error handling WLED command '{wled_command}': {e}")

    def _get_default_display(self) -> Dict:
        """Return default display content for the device role"""
        if self.role == "main":
            return {"type": "image", "content": "images/000_init.png"}
        else:
            return {"type": "image", "content": f"images/devices/{self.role}.png"}

    def get_step_info(self, step: int) -> Optional[ScenarioStep]:
        """Get step information for debugging/logging purposes"""
        actual_step = self.get_actual_step_number(step)
        if actual_step in self.steps:
            device_steps = [s for s in self.steps[actual_step] 
                           if s.device.lower() == self.role.lower()]
            return device_steps[0] if device_steps else None
        return None