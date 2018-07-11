from core.test_dependencies import *


def test_image_search():
    app_manager: AppManager = pytest.app_manager
    app_manager.launch_app()

    Screen.image_find('forward.png')
    Region(Point(0, 0), 200, 200).image_find('forward.png')

    app_manager.close_app()
