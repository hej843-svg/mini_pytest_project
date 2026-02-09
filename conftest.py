import pytest
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import logging
import importlib.metadata

# Load qareport plugin
import qareport

# Directly register all hook functions from qareport plugin
def pytest_addoption(parser):
    qareport.pytest_addoption(parser)

def pytest_configure(config):
    qareport.pytest_configure(config)

def pytest_sessionstart(session):
    qareport.pytest_sessionstart(session)

def pytest_collection_modifyitems(session, config, items):
    qareport.pytest_collection_modifyitems(session, config, items)

def pytest_runtest_logreport(report):
    qareport.pytest_runtest_logreport(report)

def pytest_sessionfinish(session, exitstatus):
    qareport.pytest_sessionfinish(session, exitstatus)

log = logging.getLogger()

@pytest.fixture(scope="session", autouse=True)
def packages_logging():
    # Get list of installed packages
    installed_packages = {pkg.metadata["Name"]: pkg.version for pkg in importlib.metadata.distributions()}

    # Record in log file
    for package, version in installed_packages.items():
        log.info(f"{package}=={version}")

@pytest.fixture
def test_name(request):
    """Return test function name with 'test_' removed from currently running test"""
    test_id = request.node.name.replace("test_", "")
    log.info(f"==================================== test start : {test_id} ====================================")
    
    # Set test_id in qareport
    qareport.set_test_id(test_id)
    
    return test_id