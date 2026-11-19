"""Start the portfolio website.

Usage:
    python build_cache.py   (once, or after the topic model is refit)
    python app.py
"""

from config.Settings import Settings
from pages.HomePage import HomePage
from pages.ProjectsPage import ProjectsPage
from portfolio.PortfolioApp import PortfolioApp
from portfolio.ProjectRegistry import ProjectRegistry

settings = Settings()
registry = ProjectRegistry.default(settings)
portfolio = PortfolioApp([HomePage(registry), ProjectsPage(registry), *registry.pages()])
server = portfolio.server

if __name__ == "__main__":
    portfolio.run(host=settings.host, port=settings.port)
