import pytest
from core.helpers.app_manager import AppManager
from core.image_search.image_search import update_image_assets


def pytest_runtest_setup(item):
    # called before running each test in this directory
    print("> Setting up for: %s" % item.name)


@pytest.fixture(scope="session", autouse=True)
def load_app_manager(request):
    # called once at beginning
    app_manager: AppManager = AppManager('iexplore')
    update_image_assets(app_manager.get_image_assets())
    pytest.app_manager = app_manager

    def clear_app_manager():
        pytest.app_manager = None

    request.addfinalizer(clear_app_manager)
