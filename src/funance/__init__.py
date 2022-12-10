"""The application factory"""

from .app import Funance


def create_app():
    """Application factory"""
    app_ = Funance()

    # set configuration
    # app_.config.from_mapping(
    #     FOO='bar'
    # )
    # app_.config.from_pyfile('my_config.py', silent=True)

    return app_
