"""
Scenario Loader Utility

This module provides utilities for loading and validating scenario files.
It supports both the new text-based format and legacy Python scenarios.
"""

import os
import glob
from typing import List, Tuple, Dict, Any
from scenarios.scenario_parser import TxtScenario

class ScenarioLoader:
    """Utility class for loading and managing scenarios"""
    
    @staticmethod
    def get_available_scenarios() -> List[Tuple[str, str]]:
        """
        Get list of available scenarios from both txt and py files
        Returns list of tuples: (display_name, scenario_id)
        """
        scenarios = []
        scenarios_dir = "scenarios"
        
        if not os.path.exists(scenarios_dir):
            return scenarios
        
        # Load text-based scenarios (preferred)
        txt_files = glob.glob(os.path.join(scenarios_dir, "*.txt"))
        for txt_file in txt_files:
            filename = os.path.basename(txt_file)
            scenario_id = filename.replace('.txt', '')
            
            # Skip if it's a backup or temp file
            if scenario_id.endswith('_backup') or scenario_id.startswith('.'):
                continue
                
            display_name = scenario_id.replace('_', ' ').title()
            scenarios.append((display_name, scenario_id))
        
        # Load legacy Python scenarios (for backward compatibility)
        py_files = glob.glob(os.path.join(scenarios_dir, "*.py"))
        for py_file in py_files:
            filename = os.path.basename(py_file)
            scenario_id = filename.replace('.py', '')
            
            # Skip base scenario and __init__ files
            if scenario_id in ['base_scenario', '__init__'] or scenario_id.startswith('.'):
                continue
                
            # Skip if we already have a txt version
            txt_equivalent = os.path.join(scenarios_dir, f"{scenario_id}.txt")
            if os.path.exists(txt_equivalent):
                continue
                
            display_name = f"{scenario_id.replace('_', ' ').title()} (Legacy)"
            scenarios.append((display_name, scenario_id))
        
        return sorted(scenarios)
    
    @staticmethod
    def validate_scenario_file(file_path: str) -> Dict[str, Any]:
        """
        Validate a scenario text file and return validation results
        Returns dict with 'valid', 'errors', 'warnings', 'step_count'
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'step_count': 0,
            'devices': set()
        }
        
        if not os.path.exists(file_path):
            result['valid'] = False
            result['errors'].append(f"File not found: {file_path}")
            return result
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            steps_found = set()
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Parse line
                parts = [part.strip() for part in line.split(';')]
                
                if len(parts) < 2:
                    result['warnings'].append(f"Line {line_num}: Insufficient parameters")
                    continue
                
                try:
                    step = int(parts[0]) if parts[0] else 0
                    device = parts[1] if parts[1] else ""
                    
                    if not device:
                        result['errors'].append(f"Line {line_num}: Missing device name")
                        continue
                    
                    steps_found.add(step)
                    result['devices'].add(device.lower())
                    
                    # Validate time_sec if provided
                    if len(parts) > 4 and parts[4]:
                        try:
                            float(parts[4])
                        except ValueError:
                            result['warnings'].append(f"Line {line_num}: Invalid time_sec value '{parts[4]}'")
                    
                except ValueError as e:
                    result['errors'].append(f"Line {line_num}: Invalid step number '{parts[0]}'")
            
            result['step_count'] = len(steps_found)
            
            if result['step_count'] == 0:
                result['errors'].append("No valid steps found in scenario")
            
            if result['errors']:
                result['valid'] = False
                
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"Error reading file: {str(e)}")
        
        return result
    
    @staticmethod
    def create_scenario_template(file_path: str, scenario_name: str) -> bool:
        """Create a template scenario file"""
        template = f"""# {scenario_name} Scenario
# Format: step;device;image(opt);wled(opt);time_sec(default=5);desc(opt);

# Initial state
0;main;000_init.png;;;{scenario_name} initialization;
0;client;devices/client.png;;;Client ready;
0;switch;devices/switch.png;;;Switch ready;
0;router;devices/router.png;;;Router ready;
0;firewall;devices/firewall.png;;;Firewall ready;
0;server;devices/server.png;;;Server ready;

# Example steps
1;client;example/step1.png;client>switch;3;Client sends packet;
2;switch;example/step2.png;switch>router;3;Switch forwards packet;
3;router;example/step3.png;router>firewall;3;Router forwards packet;
4;firewall;example/step4.png;firewall>server;3;Firewall allows packet;
5;server;example/step5.png;;;Server processes request;

# Add more steps as needed...
"""
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(template)
            return True
        except Exception as e:
            print(f"Error creating template: {e}")
            return False