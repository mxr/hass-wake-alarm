"""Wake Alarm select entity: light ramp mode (colour temperature or colour)."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import LIGHT_MODE_COLOR, LIGHT_MODE_COLOR_TEMP
from .entity import WakeAlarmEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([WakeAlarmLightModeSelect(entry)])


class WakeAlarmLightModeSelect(WakeAlarmEntity, SelectEntity, RestoreEntity):
    """Ramp the Kelvin range (default) or a fixed colour (#65)."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "light_mode"
    _attr_options = [LIGHT_MODE_COLOR_TEMP, LIGHT_MODE_COLOR]

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry, key="light_mode", platform="select")
        self._attr_current_option = LIGHT_MODE_COLOR_TEMP

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None and last_state.state in self._attr_options:
            self._attr_current_option = last_state.state

    async def async_select_option(self, option: str) -> None:
        self._attr_current_option = option
        self.async_write_ha_state()
