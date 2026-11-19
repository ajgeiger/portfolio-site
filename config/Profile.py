"""Who the site is about. Only facts taken from the resume belong here."""


class Profile:
    """Name, role, links and background shown across the site."""

    NAME = "Alex Geiger"
    ROLE = "Lead Applied AI Scientist"
    EMPLOYER = "Signature Aviation"
    ROLE_SINCE = "Jul 2026"
    SITE_TITLE = "Alex Geiger | Lead Applied AI Scientist"

    GITHUB_URL = "https://github.com/ajgeiger"
    KAGGLE_URL = "https://www.kaggle.com/alexgeiger"
    LINKEDIN_URL = "https://www.linkedin.com/in/ajgeiger"

    PLATFORM_AREAS = ("forecasting", "behavioral modeling", "NLP analysis", "dynamic pricing", "MLOps governance")
    DEGREE = "Master of Science in Applied Data Science"
    SCHOOL = "Syracuse University"

    RESUME_ASSET = "files/Alexander_Geiger_Resume.pdf"
    RESUME_FILE_NAME = "Alexander_Geiger_Resume.pdf"

    @classmethod
    def platform_areas(cls) -> str:
        """The platform areas as one readable phrase."""
        return ", ".join(cls.PLATFORM_AREAS[:-1]) + " and " + cls.PLATFORM_AREAS[-1]
