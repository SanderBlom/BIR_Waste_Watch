"""Sensor platform for BIR Waste Watch integration."""

from __future__ import annotations

from datetime import date
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import BIRDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: BIRDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[SensorEntity] = []

    if coordinator.data:
        for waste_type in coordinator.data:
            entities.extend(
                [
                    BIRWasteDateSensor(coordinator, waste_type, config_entry),
                    BIRWasteDaysSensor(coordinator, waste_type, config_entry),
                ]
            )

    async_add_entities(entities)


class BIRSensorBase(CoordinatorEntity[BIRDataUpdateCoordinator], SensorEntity):
    """Base class for BIR sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: BIRDataUpdateCoordinator,
        waste_type: str,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._waste_type = waste_type
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=f"BIR {coordinator.address}",
            manufacturer=MANUFACTURER,
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self._waste_type in self.coordinator.data
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return {
            "waste_type": self._waste_type,
        }


class BIRWasteDateSensor(BIRSensorBase):
    """Sensor for waste collection date."""

    _attr_device_class = SensorDeviceClass.DATE
    _attr_icon = "mdi:calendar"

    def __init__(
        self,
        coordinator: BIRDataUpdateCoordinator,
        waste_type: str,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the date sensor."""
        super().__init__(coordinator, waste_type, config_entry)
        # Create human-readable name
        readable_name = waste_type.replace("_", " ").title()
        self._attr_unique_id = f"{config_entry.entry_id}_{waste_type}_date"
        self._attr_translation_key = "collection_date"
        self._attr_name = f"{readable_name} Collection Date"

    @property
    def native_value(self) -> date | None:
        """Return the collection date."""
        if self.coordinator.data and self._waste_type in self.coordinator.data:
            date_str = self.coordinator.data[self._waste_type].get("date")
            if date_str:
                return date.fromisoformat(date_str)
        return None


class BIRWasteDaysSensor(BIRSensorBase):
    """Sensor for days until waste collection."""

    _attr_icon = "mdi:calendar-clock"
    _attr_native_unit_of_measurement = "days"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: BIRDataUpdateCoordinator,
        waste_type: str,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the days until sensor."""
        super().__init__(coordinator, waste_type, config_entry)
        # Create human-readable name
        readable_name = waste_type.replace("_", " ").title()
        self._attr_unique_id = f"{config_entry.entry_id}_{waste_type}_days"
        self._attr_translation_key = "days_until_pickup"
        self._attr_name = f"{readable_name} Days Until Pickup"

    @property
    def native_value(self) -> int | None:
        """Return the number of days until collection."""
        if self.coordinator.data and self._waste_type in self.coordinator.data:
            return self.coordinator.data[self._waste_type].get("days_until")
        return None
