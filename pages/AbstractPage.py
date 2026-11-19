"""The contract for a page in the portfolio app."""

from abc import ABC, abstractmethod

from dash import Dash


class AbstractPage(ABC):
    """A page knows its address, its layout and its own callbacks.

    Site pages (home, projects) are listed in app.py. Project pages extend
    AbstractProjectPage and come from the ProjectRegistry.
    """

    path = "/"
    name = "Page"
    title = "Page"
    description = ""

    @property
    def module_name(self) -> str:
        """A unique name Dash uses to register the page."""
        return f"pages.{type(self).__name__}"

    @abstractmethod
    def layout(self):
        """Return the page layout."""

    @abstractmethod
    def register_callbacks(self, app: Dash) -> None:
        """Attach the page's callbacks to the app."""
