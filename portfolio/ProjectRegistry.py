"""The list of projects on the site. Add a project here and it appears everywhere."""

from config.Profile import Profile
from config.Settings import Settings
from data.HeadlineRadarDataSource import HeadlineRadarDataSource
from pages.AbstractProjectPage import AbstractProjectPage
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
        ]

    def page(self, project: Project) -> AbstractProjectPage:
        if project.slug not in self._pages:
            self._pages[project.slug] = project.build_page(project)
        return self._pages[project.slug]

    def pages(self) -> list[AbstractProjectPage]:
        return [self.page(project) for project in self.projects]
