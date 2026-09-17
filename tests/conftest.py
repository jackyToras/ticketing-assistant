import os

# Set before application imports so tests never use the developer's normal database.
os.environ["DATABASE_URL"] = "sqlite:///./test_support_assistant.db"
