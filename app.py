"""Start the portfolio website.

Usage:
    python build_cache.py   (once, or after the topic model is refit)
    python app.py

The Ask page calls the rag-chatbot service at CHATBOT_API_URL (default http://127.0.0.1:8070).
"""

from rag_chatbot_client import ChatbotClient

from config.Settings import Settings
from pages.AskPage import AskPage
from pages.HomePage import HomePage
from pages.ProjectsPage import ProjectsPage
from pages.ResumePage import ResumePage
from portfolio.PortfolioApp import PortfolioApp
from portfolio.ProjectRegistry import ProjectRegistry

settings = Settings()
registry = ProjectRegistry.default(settings)
chatbot = ChatbotClient(settings.chatbot_api_url, settings.chatbot_api_key, settings.chatbot_timeout_seconds)
portfolio = PortfolioApp(
    [HomePage(registry), ProjectsPage(registry), ResumePage(), AskPage(chatbot), *registry.pages()]
)
server = portfolio.server

if __name__ == "__main__":
    portfolio.run(host=settings.host, port=settings.port)
