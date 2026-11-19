"""Start the portfolio app.

Usage:
    python build_cache.py   (once, or after the topic model is refit)
    python app.py
"""

from config.Settings import Settings
from data.HeadlineRadarDataSource import HeadlineRadarDataSource
from pages.TopicExplorerPage import TopicExplorerPage
from portfolio.PortfolioApp import PortfolioApp

settings = Settings()
portfolio = PortfolioApp([TopicExplorerPage(HeadlineRadarDataSource(settings), settings)])
server = portfolio.server

if __name__ == "__main__":
    portfolio.run(host=settings.host, port=settings.port)
