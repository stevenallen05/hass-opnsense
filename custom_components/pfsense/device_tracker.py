"""Support for tracking for pfSense devices."""
from __future__ import annotations

from homeassistant.components.device_tracker import SOURCE_TYPE_ROUTER
from homeassistant.components.device_tracker.config_entry import ScannerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)
from homeassistant.util import slugify

from . import CoordinatorEntityManager, PfSenseEntity

from .const import (
    DEVICE_TRACKER_COORDINATOR,
    DOMAIN,
)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
) -> None:
    """Set up device tracker for pfSense component."""
    def process_entities_callback(hass, config_entry):
        data = hass.data[DOMAIN][config_entry.entry_id]
        coordinator = data[DEVICE_TRACKER_COORDINATOR]
        state = coordinator.data

        entities = []
        for entry in state["arp_table"]:
            entity = PfSenseScannerEntity(
                config_entry,
                coordinator,
                entry.get("mac-address")
            )
            entities.append(entity)

        return entities
    cem = CoordinatorEntityManager(hass, hass.data[DOMAIN][config_entry.entry_id][DEVICE_TRACKER_COORDINATOR], config_entry, process_entities_callback, async_add_entities)
    cem.process_entities()


class PfSenseScannerEntity(PfSenseEntity, ScannerEntity):
    """Represent a scanned device."""

    def __init__(
        self,
        config_entry,
        coordinator: DataUpdateCoordinator,
        mac,
    ) -> None:
        """Set up the pfSense scanner entity."""
        self.config_entry = config_entry
        self.coordinator = coordinator
        self._mac = mac

        self._attr_unique_id = slugify(
            f"{self.pfsense_device_unique_id}_mac_{mac}")

    def _get_pfsense_arp_entry(self):
        state = self.coordinator.data
        for entry in state["arp_table"]:
            if entry.get("mac-address") == self._mac:
                return entry
              
    @property
    def source_type(self) -> str:
        """Return the source type, eg gps or router, of the device."""
        return SOURCE_TYPE_ROUTER

    @property
    def extra_state_attributes(self):
        entry = self._get_pfsense_arp_entry()
        if entry is None:
            return None

        attrs = {}
        for property in ["interface", "expires", "type"]:
            attrs[property] = entry.get(property)

        return attrs

    @property
    def ip_address(self) -> str | None:
        """Return the primary ip address of the device."""
        entry = self._get_pfsense_arp_entry()
        if entry is None:
            return STATE_UNKNOWN
        return entry.get("ip-address")

    @property
    def mac_address(self) -> str | None:
        """Return the mac address of the device."""
        return self._mac

    @property
    def hostname(self) -> str | None:
        """Return hostname of the device."""
        entry = self._get_pfsense_arp_entry()
        if entry is None:
            return STATE_UNKNOWN
        value = entry.get("hostname").strip("?")
        if len(value) > 0:
            return value
        return None

    @property
    def is_connected(self) -> bool:
        """Return true if the device is connected to the network."""
        entry = self._get_pfsense_arp_entry()
        if entry is None:
            return False
        # TODO: check "expires" here to add more honed in logic?
        # TODO: clear cache under certain scenarios?
        return True
