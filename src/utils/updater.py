"""Перевірка оновлень на GitHub Releases."""

from __future__ import annotations

import json
import logging
import urllib.request

from src.constants import APP_VERSION

logger = logging.getLogger(__name__)

GITHUB_REPO = "your-username/voicetype"
RELEASES_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def check_for_updates() -> dict[str, str] | None:
    """Перевіряє наявність нової версії на GitHub.

    Повертає dict з інформацією про оновлення або None.
    """
    try:
        req = urllib.request.Request(
            RELEASES_URL,
            headers={"Accept": "application/vnd.github.v3+json"},
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        latest_version = data.get("tag_name", "").lstrip("v")
        if not latest_version:
            return None

        if _compare_versions(latest_version, APP_VERSION) > 0:
            return {
                "version": latest_version,
                "current": APP_VERSION,
                "url": data.get("html_url", ""),
                "body": data.get("body", ""),
            }

        logger.debug("Поточна версія %s є найновішою.", APP_VERSION)
        return None

    except Exception as e:
        logger.debug("Не вдалося перевірити оновлення: %s", e)
        return None


def _compare_versions(v1: str, v2: str) -> int:
    """Порівнює дві версії у форматі semver.

    Повертає: >0 якщо v1 > v2, 0 якщо v1 == v2, <0 якщо v1 < v2.
    """
    parts1 = [int(x) for x in v1.split(".")]
    parts2 = [int(x) for x in v2.split(".")]

    # Доповнюємо нулями
    while len(parts1) < 3:
        parts1.append(0)
    while len(parts2) < 3:
        parts2.append(0)

    for a, b in zip(parts1, parts2):
        if a != b:
            return a - b
    return 0
