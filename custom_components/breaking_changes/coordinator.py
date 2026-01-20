"""DataUpdateCoordinator for Breaking Changes."""

from __future__ import annotations

import logging
from typing import Any

from awesomeversion import AwesomeVersion
from aiohttp import ClientSession
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DOMAIN,
    URL_BREAKING_CHANGES,
    URL_HA_PYPI,
    DEFAULT_SCAN_INTERVAL,
    MINIMUM_VERSION,
)

_LOGGER = logging.getLogger(__name__)


class BreakingChangesCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to fetch potential breaking changes."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self._session: ClientSession = hass.helpers.aiohttp_client.async_get_clientsession()

    async def _async_get_remote_version(self) -> AwesomeVersion:
        """Get latest Home Assistant version from PyPI."""
        try:
            async with self._session.get(URL_HA_PYPI, timeout=15) as resp:
                if resp.status != 200:
                    raise UpdateFailed(f"Error fetching HA version: {resp.status}")
                data = await resp.json()
        except Exception as err:
            raise UpdateFailed(f"Error fetching HA version: {err}") from err

        version_str = data.get("info", {}).get("version")
        if not version_str:
            raise UpdateFailed("Could not determine remote Home Assistant version")

        return AwesomeVersion(version_str)

    async def _async_get_breaking_changes_for_version(
        self,
        version: AwesomeVersion,
        integrations: list[str],
    ) -> list[dict[str, Any]]:
        """Fetch breaking changes for a specific version."""
        url = URL_BREAKING_CHANGES.format(version=str(version))
        _LOGGER.debug("Checking breaking changes for %s (%s)", version, url)

        try:
            async with self._session.get(url, timeout=15) as resp:
                if resp.status != 200:
                    _LOGGER.debug("No breaking changes for %s (status %s)", version, resp.status)
                    return []
                data = await resp.json()
        except Exception as err:
            _LOGGER.error("Error fetching breaking changes for %s: %s", version, err)
            return []

        changes: list[dict[str, Any]] = []
        for change in data or []:
            integration = change.get("integration")
            if integration in integrations:
                changes.append(
                    {
                        "title": change.get("title"),
                        "integration": integration,
                        "description": change.get("description"),
                    }
                )

        return changes

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from endpoints."""
        # Local version from HA itself
        current_version = AwesomeVersion(self.hass.config.version)
        remote_version = await self._async_get_remote_version()

        if current_version >= remote_version:
            _LOGGER.debug(
                "Current version %s >= remote version %s, skipping",
                current_version,
                remote_version,
            )
            return {
                "changes": [],
                "versions": [],
                "covered": [],
            }

        # Collect integrations
        integrations: list[str] = []
        for integration in self.hass.config.components or []:
            base = integration.split(".")[0]
            if base not in integrations:
                integrations.append(base)

        _LOGGER.debug("Loaded integrations: %s", integrations)

        c_split = [int(x) for x in str(current_version).split(".")]
        r_split = [int(x) for x in str(remote_version).split(".")]

        request_versions: list[AwesomeVersion] = []

        if c_split[0] < r_split[0]:
            for version in range(c_split[1] + 1, 13):
                request_versions.append(AwesomeVersion(f"{c_split[0]}.{version}"))
            for version in range(1, r_split[1] + 1):
                request_versions.append(AwesomeVersion(f"{r_split[0]}.{version}"))
        else:
            for version in range(c_split[1] + 1, r_split[1] + 1):
                request_versions.append(AwesomeVersion(f"{r_split[0]}.{version}"))

        minimum = AwesomeVersion(MINIMUM_VERSION)
        request_versions = [v for v in request_versions if v >= minimum]

        if not request_versions:
            _LOGGER.debug("No valid versions to check")
            return {
                "changes": [],
                "versions": [],
                "covered": [],
            }

        all_changes: list[dict[str, Any]] = []
        covered_versions: list[str] = []

        for version in request_versions:
            changes = await self._async_get_breaking_changes_for_version(
                version,
                integrations,
            )
            if changes:
                all_changes.extend(changes)
            covered_versions.append(str(version))

        return {
            "changes": all_changes,
            "versions": covered_versions,
            "covered": set(covered_versions),
        }
