"""The link that downloads the resume PDF."""

import dash
from dash import html

from config.Profile import Profile


class ResumeLink:
    """Build a download link for the resume, styled as a button or as plain text."""

    LABEL = "Download resume (PDF)"

    def build(self, class_name: str = "button") -> html.A:
        return html.A(
            self.LABEL,
            href=dash.get_asset_url(Profile.RESUME_ASSET),
            download=Profile.RESUME_FILE_NAME,
            target="_blank",
            rel="noopener",
            className=class_name,
        )
