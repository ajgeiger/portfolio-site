"""Create the Dash app, register every page and wrap them in the shared shell."""

from pathlib import Path

import dash
from dash import Dash, Input, Output

from components.AppShell import AppShell
from config.Profile import Profile
from pages.AbstractPage import AbstractPage

ASSETS_FOLDER = Path(__file__).resolve().parents[1] / "assets"


class PortfolioApp:
    """A multi page Dash website. Each page brings its own layout and callbacks."""

    TITLE = Profile.SITE_TITLE

    def __init__(self, pages: list[AbstractPage]):
        self.pages = pages
        self.shell = AppShell()
        self.app = Dash(
            __name__,
            use_pages=True,
            pages_folder="",
            assets_folder=str(ASSETS_FOLDER),
            title=self.TITLE,
            suppress_callback_exceptions=True,
        )
        for order, page in enumerate(pages):
            dash.register_page(
                page.module_name,
                path=page.path,
                name=page.name,
                title=f"{page.title} | {Profile.NAME}",
                description=page.description,
                order=order,
                layout=page.layout(),
            )
            page.register_callbacks(self.app)
        self.app.layout = self.shell.layout()
        self.register_shell_callbacks()

    def register_shell_callbacks(self) -> None:
        @self.app.callback(Output(AppShell.NAV_ID, "children"), Input(AppShell.LOCATION_ID, "pathname"))
        def highlight_current_page(pathname):
            return self.shell.links(pathname or "/")

    @property
    def server(self):
        return self.app.server

    def run(self, host: str, port: int, debug: bool = False) -> None:
        self.app.run(host=host, port=port, debug=debug)
