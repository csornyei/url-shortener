from unittest.mock import MagicMock

class MockCache:
    def __init__(self):
        self.cache_url = MagicMock()
        self.extend_url = MagicMock()
        self.retrieve_url = MagicMock()