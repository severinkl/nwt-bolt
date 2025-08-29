"""
Scenario Converter Utility

This module helps convert legacy Python scenarios to the new text-based format.
"""

import os
import inspect
from typing import Dict, List, Optional

class ScenarioConverter:
    """Convert Python scenarios to text format"""
    
    @staticmethod
    def convert_python_to_txt(python_file_path: str, output_file_path: str) -> bool:
        """
        Convert a Python scenario file to text format
        This is a helper for manual conversion - automatic conversion is complex
        due to the varied structure of Python scenarios.
        """
        
        if not os.path.exists(python_file_path):
            print(f"Error: Python file not found: {python_file_path}")
            return False
        
        try:
            # Load the Python module
            module_name = os.path.basename(python_file_path).replace('.py', '')
            spec = importlib.util.spec_from_file_location(module_name, python_file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if not hasattr(module, 'Scenario'):
                print(f"Error: No Scenario class found in {python_file_path}")
                return False
            
            scenario_class = module.Scenario
            
            # Create template with basic info
            template = f"""# {getattr(scenario_class, 'name', 'Converted Scenario')}
# {getattr(scenario_class, 'description', 'Converted from Python scenario')}
# Format: step;device;image(opt);wled(opt);time_sec(default=5);desc(opt);

# MANUAL CONVERSION REQUIRED
# This is a template - you need to manually convert the Python logic
# Original maximum_steps: {getattr(scenario_class, 'maximum_steps', 'unknown')}

# Add your scenario steps here following the format:
# step;device;image;wled;time_sec;description;

0;main;000_init.png;;;Scenario initialization;
# Add more steps...
"""
            
            with open(output_file_path, 'w', encoding='utf-8') as f:
                f.write(template)
            
            print(f"Template created at {output_file_path}")
            print("Manual conversion required - please fill in the actual scenario steps")
            return True
            
        except Exception as e:
            print(f"Error converting scenario: {e}")
            return False
    
    @staticmethod
    def analyze_python_scenario(python_file_path: str) -> Dict:
        """
        Analyze a Python scenario to help with manual conversion
        Returns information about the scenario structure
        """
        
        analysis = {
            'name': 'Unknown',
            'description': 'No description',
            'maximum_steps': 0,
            'methods': [],
            'roles': [],
            'step_methods': []
        }
        
        try:
            with open(python_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract basic info using simple string parsing
            lines = content.split('\n')
            
            for line in lines:
                line = line.strip()
                
                if 'name =' in line and '"' in line:
                    analysis['name'] = line.split('"')[1]
                elif 'description =' in line and '"' in line:
                    analysis['description'] = line.split('"')[1]
                elif 'maximum_steps =' in line:
                    try:
                        analysis['maximum_steps'] = int(line.split('=')[1].strip())
                    except:
                        pass
                elif line.startswith('def step_'):
                    step_num = line.split('step_')[1].split('(')[0]
                    analysis['step_methods'].append(f"step_{step_num}")
                elif line.startswith('def handle_'):
                    role = line.split('handle_')[1].split('(')[0]
                    if role not in analysis['roles']:
                        analysis['roles'].append(role)
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing scenario: {e}")
            return analysis

def main():
    """Command line utility for converting scenarios"""
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python scenario_converter.py <input.py> <output.txt>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    converter = ScenarioConverter()
    
    # First analyze the scenario
    print("Analyzing Python scenario...")
    analysis = converter.analyze_python_scenario(input_file)
    
    print(f"Scenario Name: {analysis['name']}")
    print(f"Description: {analysis['description']}")
    print(f"Maximum Steps: {analysis['maximum_steps']}")
    print(f"Roles Found: {', '.join(analysis['roles'])}")
    print(f"Step Methods: {', '.join(analysis['step_methods'])}")
    
    # Create template
    print(f"\nCreating template at {output_file}...")
    if converter.convert_python_to_txt(input_file, output_file):
        print("Template created successfully!")
        print("Please manually convert the Python logic to text format.")
    else:
        print("Failed to create template.")

if __name__ == "__main__":
    main()