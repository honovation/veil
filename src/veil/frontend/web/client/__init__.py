######## export begin
from .browser import start_website_and_browser

__all__ = [
    # from browser
    start_website_and_browser.__name__
]
######## export end

def init():
    from sandal.component import init_component

    init_component(__name__)

init()