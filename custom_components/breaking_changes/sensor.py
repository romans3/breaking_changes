"""Sensor platform for Breaking Changes."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, DEFAULT_NAME
from .coordinator import BreakingChangesCoordinator


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Breaking Changes sensor from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: BreakingChangesCoordinator = data["coordinator"]

    async_add_entities(
        [
            BreakingChangesSensor(
                coordinator=coordinator,
                name=DEFAULT_NAME,
            )
        ]
    )


class BreakingChangesSensor(CoordinatorEntity[BreakingChangesCoordinator], SensorEntity):
    """Sensor that exposes potential breaking changes."""

    _attr_icon = "mdi:package-up"

    def __init__(self, coordinator: BreakingChangesCoordinator, name: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = f"{DOMAIN}_potential_breaking_changes"

    @property
    def native_value(self) -> int:
        """Return the number of potential breaking changes."""
        data = self.coordinator.data or {}
        changes = data.get("changes", [])
        return max(len(changes), 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        data = self.coordinator.data or {}
        return {
            "changes": data.get("changes", []),
            "versions": data.get("versions", []),
            "covered": list(data.get("covered", [])),
        }
