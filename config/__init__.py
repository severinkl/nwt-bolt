import os

# Load the appropriate configuration
if os.getenv("ENV") == "production":
    from .production import *
else:
    from .default import *