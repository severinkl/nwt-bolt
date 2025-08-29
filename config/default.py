# Default configuration (development)
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_CHANNEL = "scenario_updates"

# Auto-progress configuration
AUTO_PROGRESS_TIMEOUT = 8000  # milliseconds

# Define roles and their IDs
ROLES = {
    "firewall": 1,
    "main": 2,
    "switch": 3,
    "router": 4,
    "dns": 5,
    "server": 6
}
