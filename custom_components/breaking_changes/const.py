"""Constants for the Breaking Changes integration."""

from datetime import timedelta
from homeassistant.const import Platform

DOMAIN = "breaking_changes"

PLATFORMS: list[Platform] = [Platform.SENSOR]

URL_BREAKING_CHANGES = "https://hachanges.entrypoint.xyz/v1/{version}"
URL_HA_PYPI = "https://pypi.org/pypi/homeassistant/json"

DEFAULT_NAME = "Potential breaking changes"

DEFAULT_SCAN_INTERVAL = timedelta(minutes=5)
MINIMUM_VERSION = "2021.3"
