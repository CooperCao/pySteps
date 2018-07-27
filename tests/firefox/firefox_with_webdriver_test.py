from core.test_dependencies import *


# Example of test that might throw errors that we want to ignore
# https://docs.pytest.org/en/2.9.0/skipping.html
@pytest.mark.xfail(raises=ZeroDivisionError)
def test_raises():
    return 9 / 0


# Example of test with debug
# https://docs.pytest.org/en/2.9.0/usage.html?highlight=pdb
def test_with_debug():
    # pytest.set_trace()
    pass


# Firefox without selenium example
def test_image_search():
    app_manager: AppManager = pytest.app_manager
    app_manager.launch_app('-foreground -new-instance -private')

    found_coord = Screen.image_find('reload.png')
    assert isinstance(found_coord, Point)

    Region(Point(0, 0), 500, 500).image_find('reload.png')

    app_manager.close_app()
