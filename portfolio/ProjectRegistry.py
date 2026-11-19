"""The list of projects on the site. Add a project here and it appears everywhere."""

from config.Profile import Profile
from config.Settings import Settings
from data.forecast.ForecastCache import ForecastCache
from data.HeadlineRadarDataSource import HeadlineRadarDataSource
from pages.AbstractProjectPage import AbstractProjectPage
from pages.PriceForecastPage import PriceForecastPage
from pages.TopicExplorerPage import TopicExplorerPage
from portfolio.Project import Project


class ProjectRegistry:
    """Hold every project entry and build each project's page once.

    To add a project: write one page class that extends AbstractProjectPage,
    then add one Project entry in default_projects. The home page, the
    projects index and the routes all pick it up.
    """

    def __init__(self, projects: list[Project]):
        slugs = [project.slug for project in projects]
        if len(slugs) != len(set(slugs)):
            raise ValueError("Every project needs a unique slug.")
        self.projects = projects
        self._pages = {}

    @classmethod
    def default(cls, settings: Settings) -> "ProjectRegistry":
        return cls(cls.default_projects(settings))

    @staticmethod
    def default_projects(settings: Settings) -> list[Project]:
        return [
            Project(
                slug="news-topic-explorer",
                title="News Topic Explorer",
                summary=(
                    "What is the news talking about, and how much coverage does each theme get? An interactive "
                    "walk from 41 thousand articles down to the actual headlines, built on my own topic model."
                ),
                question="What is the news talking about, and how much coverage does each theme get?",
                data=(
                    "Headlines and summaries collected by Headline Radar, my news pipeline, from the GDELT "
                    "global news feed and publisher RSS feeds, stored in SQLite."
                ),
                approach=(
                    "A BERTopic style model I wrote from scratch: MiniLM sentence embeddings, UMAP, HDBSCAN "
                    "and c-TF-IDF keywords. Topics are merged into a tree by keyword similarity so the corpus "
                    "can be read top down. The app only reads the fitted results; nothing is retrained."
                ),
                tags=("Topic modeling", "NLP", "Plotly Dash", "Python"),
                thumbnail="images/news-topic-explorer.png",
                repo_url=Profile.GITHUB_URL,
                repo_label="Code on GitHub",
                build_page=lambda project: TopicExplorerPage(project, HeadlineRadarDataSource(settings), settings),
            ),
            Project(
                slug="natural-gas-price-forecast",
                title="Natural Gas Price Forecast",
                summary=(
                    "A Chronos-2 forecast of natural gas futures in production, scored every trading morning beside "
                    "a gradient boosting challenger, selected through rolling backtests of four model families."
                ),
                question="Can a model forecast natural gas futures better than repeating the last price?",
                data=(
                    "Public data only: the daily high of the front-month natural gas futures contract (Yahoo "
                    "Finance NG=F), weather in major gas-demand cities from Open-Meteo, and EIA weekly storage, "
                    "loaded into SQLite."
                ),
                approach=(
                    "Chronos-2, gradient boosting, Greykite and a naive baseline, backtested on the same rolling "
                    "dates with no look-ahead. The winner is promoted only when it beats naive by at least 1%, then "
                    "registered in MLflow and scored each trading morning beside the challenger."
                ),
                tags=("Forecasting", "Time series", "MLflow", "Plotly Dash"),
                thumbnail="images/natural-gas-price-forecast.png",
                repo_url="https://github.com/ajgeiger/natural-gas-forecasting",
                repo_label="Code on GitHub",
                build_page=lambda project: PriceForecastPage(project, ForecastCache(settings)),
            ),
        ]

    def page(self, project: Project) -> AbstractProjectPage:
        if project.slug not in self._pages:
            self._pages[project.slug] = project.build_page(project)
        return self._pages[project.slug]

    def pages(self) -> list[AbstractProjectPage]:
        return [self.page(project) for project in self.projects]
