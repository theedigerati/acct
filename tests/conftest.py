import pytest

pytest_plugins = [
    "tests.fixtures.setup",
    "tests.fixtures.data.organisation",
    "tests.fixtures.data.user",
    "tests.fixtures.data.team",
    "tests.fixtures.data.inventory",
    "tests.fixtures.data.general",
    "tests.fixtures.data.accounting",
    "tests.fixtures.data.sales",
    "tests.fixtures.data.purchase",
]


def pytest_collection_modifyitems(items):
    for item in items:
        if "e2e" in item.nodeid:
            item.add_marker(pytest.mark.e2e)
