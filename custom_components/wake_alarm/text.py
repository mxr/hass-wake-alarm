"""Wake Alarm text entity: the light colour used in colour mode."""
from __future__ import annotations

from homeassistant.components.text import RestoreText
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEFAULT_LIGHT_COLOR, LIGHT_COLOR_PATTERN
from .entity import WakeAlarmEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([WakeAlarmLightColorText(entry)])


class WakeAlarmLightColorText(WakeAlarmEntity, RestoreText):
    """Hex colour (#RRGGBB); HA has no colour entity type."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "light_color"
    _attr_pattern = LIGHT_COLOR_PATTERN
    _attr_native_min = 7
    _attr_native_max = 7

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry, key="light_color", platform="text")
        self._attr_native_value = DEFAULT_LIGHT_COLOR

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_text_data()
        if last is not None and last.native_value is not None:
            self._attr_native_value = last.native_value

    async def async_set_value(self, value: str) -> None:
        self._attr_native_value = value
        self.async_write_ha_state()
