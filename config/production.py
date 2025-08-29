import os

# Production configuration
REDIS_HOST = os.getenv("REDIS_HOST", "192.168.1.100")  # Replace with your main controller's IP
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_CHANNEL = "scenario_updates"

# Define roles and their IDs
ROLES = {
    "firewall": 1,
    "main": 2,
    "switch": 3,
    "router": 4,
    "dns": 5,
    "server": 6
}