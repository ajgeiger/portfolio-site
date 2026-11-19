"""The contract for a page in the portfolio app."""

from abc import ABC, abstractmethod

from dash import Dash


class AbstractPage(ABC):
    """A page knows its address, its layout and its own callbacks.

    To add a page, subclass this, then list the new page in PortfolioApp.
    The shared header picks up its name automatically.
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
