"""One entry in the projects registry."""

from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Project:
    """Everything the site needs to list a project and build its page.

    Attributes:
        slug: Short name used in the address, for example "news-topic-explorer".
        title: Display name.
        summary: One or two sentences for cards.
        question: The question the project answers.
        data: Where the data comes from, in plain words.
        approach: How the answer is produced, in plain words.
        tags: Short labels shown on cards.
        thumbnail: Image path inside the assets folder.
        repo_url: Link to the code.
        repo_label: Text for that link.
        build_page: Function that takes this project and returns its page object.
    """

    slug: str
    title: str
    summary: str
    question: str
    data: str
    approach: str
    tags: tuple[str, ...]
    thumbnail: str
    repo_url: str
    repo_label: str
    build_page: Callable = field(repr=False, compare=False)

    @property
    def route(self) -> str:
        return f"/projects/{self.slug}"
