System requirements:

```

```


# Network Scenario Simulator

A distributed network scenario simulator that demonstrates various networking concepts through visual state changes.

## Setup

1. Install dependencies:
```bash
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install python3-tk
sudo apt-get install redis-server
sudo systemctl start redis-server
sudo apt install python3-gi gir1.2-webkit2-4.0
pip install -r requirements.txt
```

## Configuration

The system configuration is managed through the `config` directory:

- `config/default.py`: Development configuration
- `config/production.py`: Production configuration

To use production settings, set the environment variable:
```bash
export ENV=production
```

### Admin Access

The admin panel is protected by a PIN. You can set a custom PIN using an environment variable:
```bash
export ADMIN_PIN=your_secure_pin_here
```

If no ADMIN_PIN is set, the system will use the default PIN "1234" and show a security warning in the console. For production use, always set a custom PIN.

### Admin Access

To enable admin panel access, set the admin PIN environment variable:
```bash
export ADMIN_PIN=your_secure_pin_here
```

Without this environment variable, the admin panel will not be accessible and will show an error message when attempting to access it.

Key configuration options:
- `REDIS_HOST`: Redis server host (default: localhost)
- `REDIS_PORT`: Redis server port (default: 6379)
- `REDIS_CHANNEL`: Redis pub/sub channel name (default: scenario_updates)
- `AUTO_PROGRESS_TIMEOUT`: Time in milliseconds between auto-progress steps (default: 5000)
- `ADMIN_PIN`: PIN code for accessing the admin panel (required for admin access)
- `ADMIN_PIN`: PIN code for accessing the admin panel (required for admin access)

## Running Components

Start each component in a separate terminal:

1. Main Controller:
```bash
python main.py main
```

2. Router:
```bash
python main.py router
```

3. Switch:
```bash
python main.py switch
```

4. Firewall:
```bash
python main.py firewall
```

## Project Structure

### Images

Place custom images in the `images` directory following this structure:
```
images/
├── fhstp_logo.png              # Default logo
├── scenario_1/            
│   ├── firewall_normal.png
│   ├── firewall_blocked.png
│   └── ...
├── scenario_2/
│   ├── firewall_dns_query.png
│   └── ...
└── scenario_3/
    ├── firewall_stream_start.png
    └── ...
```

### Scenarios

Scenarios can be defined in two ways:

#### 1. Text File Scenarios (Recommended)
Create `.txt` files in the `scenarios` directory with the following format:
```
step;device;image(opt);wled(opt);time_sec(default=5);desc(opt);
```

Example:
```
1;client;start.png;client>switch;2.5;Client sends packet to switch;
2;switch;packet_received.png;null;5;Switch processes packet;
```

- `step`: Step number (integer)
- `device`: Target device (client, switch, router, firewall, server, dns, main)
- `image`: Image file path (optional, relative to images/ directory)
- `wled`: WLED command for LED control (optional, format: source>target or "null")
- `time_sec`: Duration in seconds (optional, default: 5)
- `desc`: Description text (optional)

#### 2. Python File Scenarios (Legacy)
Python scenarios are still supported for backward compatibility. When you add a new scenario, ensure to extend the scenario buttons in the scenario selector:
```
scenarios = [
            ("DNS and HTTPS (ORF) Level 1", "dns_https_level_1"),
            ("DNS and HTTPS (ORF) Level 2", "dns_https_level_2"),
            ("DNS and HTTPS (ORF) Level 3", "dns_https_level_3")
        ]
```

### Debugging

Test redis channel:

On the main bind and set protected mode in the `/etc/redis/redis.conf`:

```
bind * -::*
protected-mode no:
```

on the other you can test the redis channel with the redis-cli:

```
redis-cli
127.0.0.1:6379> SUBSCRIBE scenario_updates
```
### Testing

...

## Scenario System

The scenario system supports two formats:
1. **Text-based scenarios** (`.txt` files) - **Recommended**
2. **Python-based scenarios** (`.py` files) - Legacy support

### Text-Based Scenario Format

#### File Structure
Each line in a `.txt` scenario file follows this format:
```
step;device;image(opt);wled(opt);time_sec(default=5);desc(opt);
```

#### Parameters

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `step` | Yes | Sequential step number | `1`, `2`, `15` |
| `device` | Yes | Target device name | `client`, `switch`, `router`, `firewall`, `server`, `dns`, `main` |
| `image` | No | Image filename (relative to `images/`) | `http/start.png`, `null` |
| `wled` | No | WLED command for LED control | `client>switch`, `switch>router`, `null` |
| `time_sec` | No | Duration in seconds (default: 5.0) | `2.5`, `10`, `3` |
| `desc` | No | Description text for the step | `Client sends HTTP request` |

#### Special Values
- Use `null` for optional parameters you want to explicitly skip
- Empty fields are treated as defaults or ignored
- Use `TEXT` as image value to display only text (requires desc parameter)

#### Example Scenario File

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

#### Device Names
Supported device names:
- `client` - Client computer/browser
- `switch` - Network switch
- `router` - Network router  
- `firewall` - Security firewall
- `server` - Web/application server
- `dns` - DNS server
- `main` - Main controller (scenario overview)

#### WLED Commands
Format: `source>target`
- `client>switch` - Light path from client to switch
- `switch>router` - Light path from switch to router
- `router>firewall` - Light path from router to firewall
- `firewall>server` - Light path from firewall to server

### Image Organization

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

### Creating New Scenarios

#### Method 1: Manual Creation
1. Create a new `.txt` file in the `scenarios/` directory
2. Follow the format specification above
3. Add images to appropriate subdirectories in `images/`
4. Test the scenario using the simulator

#### Method 2: Using Template Generator
```python
from scenarios.scenario_loader import ScenarioLoader
from scenarios.scenario_parser import TxtScenario

# Create template
ScenarioLoader.create_scenario_template(
    "scenarios/my_new_scenario.txt", 
    "My New Scenario"
)
```

#### Method 3: Converting from Python (Legacy)
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

### Validation

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

### Best Practices

1. **Use descriptive step numbers** - Don't skip numbers unnecessarily
2. **Group related actions** - Multiple devices can act in the same step
3. **Provide descriptions** - Help users understand what's happening
4. **Test thoroughly** - Verify all devices show correct content
5. **Use consistent naming** - Follow existing image naming conventions
6. **Document complex scenarios** - Add comments explaining the flow

### Migration from Python Scenarios

When migrating from Python scenarios:

1. **Analyze the structure** using `scenario_converter.py`
2. **Map Python methods to text steps** - Each `step_X` method becomes step X
3. **Extract image paths** - Convert hardcoded paths to the text format
4. **Handle role-specific logic** - Create separate lines for each device
5. **Test extensively** - Ensure behavior matches the original

### Troubleshooting

#### Common Issues

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