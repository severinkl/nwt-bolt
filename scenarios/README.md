# Scenario System Documentation

## Overview

The scenario system supports two formats:
1. **Text-based scenarios** (`.txt` files) - **Recommended**
2. **Python-based scenarios** (`.py` files) - Legacy support

## Text-Based Scenario Format

### File Structure
Each line in a `.txt` scenario file follows this format:
```
step;device;image(opt);wled(opt);time_sec(default=5);desc(opt);
```

### Parameters

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `step` | Yes | Sequential step number | `1`, `2`, `15` |
| `device` | Yes | Target device name | `client`, `switch`, `router`, `firewall`, `server`, `dns`, `main` |
| `image` | No | Image filename (relative to `images/`) | `http/start.png`, `null` |
| `wled` | No | WLED command for LED control | `client>switch`, `switch>router`, `null` |
| `time_sec` | No | Duration in seconds (default: 5.0) | `2.5`, `10`, `3` |
| `desc` | No | Description text for the step | `Client sends HTTP request` |

### Special Values
- Use `null` for optional parameters you want to explicitly skip
- Empty fields are treated as defaults or ignored
- Use `TEXT` as image value to display only text (requires desc parameter)

### Example Scenario File

```txt
# My Network Scenario
# Format: step;device;image(opt);wled(opt);time_sec(default=5);desc(opt);

# Initial state
0;main;000_init.png;;;Scenario starting;
0;client;devices/client.png;;;Client ready;

# Step 1: Client action
1;client;http/request.png;client>switch;3;Client sends HTTP request;
1;main;descriptions/step1.png;;;Step 1: HTTP request initiated;

# Step 2: Switch processing
2;switch;http/processing.png;switch>router;2;Switch forwards packet;
2;main;descriptions/step2.png;;;Step 2: Packet forwarded;

# Text-only step
3;client;TEXT;;;Connection established successfully!;

# Final step
10;main;999_finish.png;;;Scenario completed;
```

### Device Names
Supported device names:
- `client` - Client computer/browser
- `switch` - Network switch
- `router` - Network router  
- `firewall` - Security firewall
- `server` - Web/application server
- `dns` - DNS server
- `main` - Main controller (scenario overview)

### WLED Commands
Format: `source>target`
- `client>switch` - Light path from client to switch
- `switch>router` - Light path from switch to router
- `router>firewall` - Light path from router to firewall
- `firewall>server` - Light path from firewall to server

## Image Organization

Place scenario images in the `images/` directory:
```
images/
├── devices/           # Default device images
│   ├── client.png
│   ├── switch.png
│   └── ...
├── http/             # HTTP scenario images
│   ├── request.png
│   └── ...
├── descriptions/     # Step description images
│   ├── step1.png
│   └── ...
└── 000_init.png     # Default initialization image
```

## Creating New Scenarios

### Method 1: Manual Creation
1. Create a new `.txt` file in the `scenarios/` directory
2. Follow the format specification above
3. Add images to appropriate subdirectories in `images/`
4. Test the scenario using the simulator

### Method 2: Using Template Generator
```python
from scenarios.scenario_loader import ScenarioLoader
from scenarios.scenario_parser import TxtScenario

# Create template
ScenarioLoader.create_scenario_template(
    "scenarios/my_new_scenario.txt", 
    "My New Scenario"
)
```

### Method 3: Converting from Python (Legacy)
```python
from scenarios.scenario_converter import ScenarioConverter

# Analyze existing Python scenario
analysis = ScenarioConverter.analyze_python_scenario("scenarios/old_scenario.py")
print(analysis)

# Create conversion template
ScenarioConverter.convert_python_to_txt(
    "scenarios/old_scenario.py",
    "scenarios/new_scenario.txt"
)
```

## Validation

Validate scenario files before deployment:

```python
from scenarios.scenario_loader import ScenarioLoader

result = ScenarioLoader.validate_scenario_file("scenarios/my_scenario.txt")
if result['valid']:
    print(f"Scenario valid! {result['step_count']} steps found")
else:
    print("Validation errors:")
    for error in result['errors']:
        print(f"  - {error}")
```

## Best Practices

1. **Use descriptive step numbers** - Don't skip numbers unnecessarily
2. **Group related actions** - Multiple devices can act in the same step
3. **Provide descriptions** - Help users understand what's happening
4. **Test thoroughly** - Verify all devices show correct content
5. **Use consistent naming** - Follow existing image naming conventions
6. **Document complex scenarios** - Add comments explaining the flow

## Migration from Python Scenarios

When migrating from Python scenarios:

1. **Analyze the structure** using `scenario_converter.py`
2. **Map Python methods to text steps** - Each `step_X` method becomes step X
3. **Extract image paths** - Convert hardcoded paths to the text format
4. **Handle role-specific logic** - Create separate lines for each device
5. **Test extensively** - Ensure behavior matches the original

## Troubleshooting

### Common Issues

1. **Images not loading**
   - Check image paths are relative to `images/` directory
   - Verify image files exist
   - Ensure proper file permissions

2. **WLED not working**
   - Verify WLED controller configuration
   - Check network connectivity to WLED devices
   - Ensure proper device mapping in `wled_controller.py`

3. **Steps not executing**
   - Check step numbers are sequential
   - Verify device names match exactly
   - Look for parsing errors in console output

4. **Timing issues**
   - Adjust `time_sec` values for better flow
   - Consider network latency for WLED commands
   - Test with different auto-progress speeds