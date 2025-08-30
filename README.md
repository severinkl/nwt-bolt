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