import re
from pathlib import Path

import dash
import pytest

from components.AppShell import AppShell
from config.Profile import Profile
from config.Resume import Resume
from pages.HomePage import HomePage
from pages.ProjectsPage import ProjectsPage
from pages.ResumePage import ResumePage
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


ASSETS = Path(__file__).resolve().parents[1] / "assets"

# Phrases that would say or suggest the site owner is looking for a job.
JOB_SEEKING = re.compile(
    r"open to (work|new|opportunit)|for hire|available for|looking for|seeking|hire me|work with me|"
    r"let'?s work|get in touch|reach out|new opportunit|next role|job search",
    re.IGNORECASE,
)
PHONE = re.compile(r"\(?\d{3}\)?[ .]\d{3}[ .]\d{4}")


@pytest.fixture
def site(registry):
    return PortfolioApp([HomePage(registry), ProjectsPage(registry), ResumePage(), *registry.pages()])


@pytest.fixture
def site_text(registry) -> str:
    pages = [HomePage(registry), ProjectsPage(registry), ResumePage(), *registry.pages()]
    shell = AppShell()
    return " ".join([text_of(page.layout()) for page in pages] + [text_of(shell.header()), text_of(shell.footer())])


def test_every_route_is_registered(site):
    paths = {page["path"] for page in dash.page_registry.values()}
    assert {"/", "/projects", "/resume", "/projects/news-topic-explorer"} <= paths
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
    assert active("/resume") == ["Resume"]


def test_footer_links_to_github_and_kaggle():
    links = hrefs_of(AppShell().footer())
    assert Profile.GITHUB_URL in links
    assert Profile.KAGGLE_URL in links


def test_resume_download_is_on_home_about_and_resume_page(registry):
    resume_href = dash.get_asset_url(Profile.RESUME_ASSET)
    home = HomePage(registry)
    assert resume_href in hrefs_of(home.hero())
    assert resume_href in hrefs_of(home.about())
    assert resume_href in hrefs_of(ResumePage().layout())
    assert (ASSETS / Profile.RESUME_ASSET).is_file()


def test_copy_uses_the_current_title_and_school(site_text):
    assert "Lead Applied AI Scientist" in site_text
    assert "Lead Data Scientist" not in site_text
    assert "Syracuse University" in site_text
    assert "ischool" not in site_text.lower()


def test_copy_never_suggests_job_seeking(site_text):
    assert JOB_SEEKING.search(site_text) is None


def test_copy_has_no_phone_email_or_long_dashes(site_text):
    assert PHONE.search(site_text) is None
    assert "@" not in site_text
    assert "\u2013" not in site_text and "\u2014" not in site_text


def test_resume_page_shows_the_full_resume_in_order():
    text = text_of(ResumePage().layout())
    expected = [Resume.NAME, Resume.SUMMARY]
    for employer in Resume.EXPERIENCE:
        expected.append(employer.name)
        for role in employer.roles:
            expected += [role.title, role.dates, *([role.note] if role.note else []), *role.bullets]
    for item in Resume.EDUCATION + Resume.CERTIFICATIONS + Resume.ACHIEVEMENTS:
        expected += [item.title, item.dates, *item.bullets]
    position = 0
    for piece in expected:
        position = text.find(piece, position)
        assert position >= 0, piece
