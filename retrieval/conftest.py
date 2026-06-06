import time
import pytest

@pytest.fixture(autouse=True)
def rate_limit_pause():
    yield
    time.sleep(3) 