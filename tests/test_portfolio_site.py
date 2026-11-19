import dash
import pytest

from components.AppShell import AppShell
from config.Profile import Profile
from pages.HomePage import HomePage
from pages.ProjectsPage import ProjectsPage
from portfolio.PortfolioApp import PortfolioApp
from portfolio.ProjectRegistry import ProjectRegistry
from tests.conftest import make_project


def text_of(component) -> str:
    """Every string inside a Dash component tree, joined with spaces."""
    if isinstance(component, str):
        return component
    if isinstance(component, (list, tuple)):
        return " ".join(text_of(child) for child in component)
    children = getattr(component, "children", None)
    return text_of(children) if children is not None else ""


def hrefs_of(component) -> list[str]:
    if isinstance(component, (list, tuple)):
        return [href for child in component for href in hrefs_of(child)]
    found = [component.href] if getattr(component, "href", None) else []
    children = getattr(component, "children", None)
    return found + (hrefs_of(children) if children is not None and not isinstance(children, str) else [])


@pytest.fixture
def site(registry):
    return PortfolioApp([HomePage(registry), ProjectsPage(registry), *registry.pages()])


def test_every_route_is_registered(site):
    paths = {page["path"] for page in dash.page_registry.values()}
    assert {"/", "/projects", "/projects/news-topic-explorer"} <= paths
    assert site.app.title == Profile.SITE_TITLE


def test_registry_rejects_duplicate_slugs(data_source):
    with pytest.raises(ValueError):
        ProjectRegistry([make_project(data_source), make_project(data_source)])


def test_registry_builds_each_page_once(registry, project):
    assert registry.page(project) is registry.page(project)
    assert [page.project for page in registry.pages()] == [project]


def test_a_new_project_shows_up_on_home_and_projects(data_source):
    registry = ProjectRegistry([make_project(data_source), make_project(data_source, "second-project")])
    for page in (HomePage(registry), ProjectsPage(registry)):
        links = hrefs_of(page.layout())
        assert "/projects/news-topic-explorer" in links
        assert "/projects/second-project" in links


def test_home_page_uses_only_profile_facts(registry):
    text = text_of(HomePage(registry).layout())
    assert "Signature Aviation" in text
    assert "Syracuse University" in text
    assert Profile.ROLE in text
    links = hrefs_of(HomePage(registry).layout())
    assert Profile.GITHUB_URL in links
    assert Profile.KAGGLE_URL in links


def test_navigation_marks_the_current_section():
    shell = AppShell()

    def active(pathname):
        return [link.children for link in shell.links(pathname) if "is-active" in link.className]

    assert active("/") == ["Home"]
    assert active("/projects") == ["Projects"]
    assert active("/projects/news-topic-explorer") == ["Projects"]


def test_footer_links_to_github_and_kaggle():
    links = hrefs_of(AppShell().footer())
    assert Profile.GITHUB_URL in links
    assert Profile.KAGGLE_URL in links
