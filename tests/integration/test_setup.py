"""Full config-entry setup/teardown smoke test.

Unlike the coordinator tests (which drive the state machine directly), this
runs the real ``config_entries.async_setup`` path end-to-end, including
``_async_register_card``. That path used to be broken by #19 (duplicate static
route on concurrent setup) and #20 (blocking ``open()`` of manifest.json); both
are now fixed, so this is a real passing gate. The card registration calls
``add_extra_js_url``, so it depends on the ``card_frontend`` fixture (which
provides ``http`` + the frontend data store — see the integration conftest).

This drives the real config-entry setup, which imports ``config_flow``; that
module uses ``ConfigFlowResult`` (HA 2024.4+), so the test is skipped on older
cores where the integration's config flow can't be imported at all. The #19/#20
regressions themselves are gated by ``test_card_registration.py``, which runs on
every supported core.
"""
from __future__ import annotations

import homeassistant.config_entries as _config_entries
import pytest
from homeassistant.const import CONF_NAME
from homeassistant.core import State
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    mock_restore_cache_with_extra_data,
)

from custom_components.wake_alarm.const import (
    CONF_LIGHT_ENTITIES,
    CONF_MEDIA_PLAYER_ENTITIES,
    CONF_NOTIFY_TARGET_STANDARD,
    CONF_NOTIFY_TARGET_URGENT,
    CONF_SLUG,
    DOMAIN,
)

_HAS_CONFIG_FLOW_RESULT = hasattr(_config_entries, "ConfigFlowResult")


@pytest.mark.skipif(
    not _HAS_CONFIG_FLOW_RESULT,
    reason="integration config_flow requires ConfigFlowResult (HA 2024.4+)",
)
async def test_full_entry_setup_and_unload(hass, card_frontend) -> None:
    """The entry sets up its platforms and unloads cleanly."""
    # card_frontend provides http + the add_extra_js_url data store the card
    # registration needs (the real frontend component can't run under PHACC).
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        unique_id="smoke",
        data={
            CONF_NAME: "Smoke",
            CONF_SLUG: "smoke",
            CONF_LIGHT_ENTITIES: ["light.bedroom"],
            CONF_MEDIA_PLAYER_ENTITIES: ["media_player.bedroom"],
            CONF_NOTIFY_TARGET_STANDARD: "notify.mobile",
            CONF_NOTIFY_TARGET_URGENT: "notify.mobile",
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    assert coordinator is not None
    # The enable switch should have been created by the switch platform.
    assert hass.states.get("switch.smoke_enabled") is not None
    # Light ramp mode defaults to the colour-temperature ramp (#65).
    assert hass.states.get("select.smoke_light_mode").state == "color_temp"
    assert hass.states.get("text.smoke_light_color").state == "#FF3C00"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


@pytest.mark.skipif(
    not _HAS_CONFIG_FLOW_RESULT,
    reason="integration config_flow requires ConfigFlowResult (HA 2024.4+)",
)
async def test_light_mode_and_color_restored(hass, card_frontend) -> None:
    """The light mode and colour survive a restart (#65)."""
    mock_restore_cache_with_extra_data(
        hass,
        [
            (State("select.smoke_light_mode", "color"), {}),
            (
                State("text.smoke_light_color", "#00FF00"),
                {"native_value": "#00FF00", "native_min": 7, "native_max": 7},
            ),
        ],
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        unique_id="smoke",
        data={
            CONF_NAME: "Smoke",
            CONF_SLUG: "smoke",
            CONF_LIGHT_ENTITIES: ["light.bedroom"],
            CONF_MEDIA_PLAYER_ENTITIES: [],
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("select.smoke_light_mode").state == "color"
    assert hass.states.get("text.smoke_light_color").state == "#00FF00"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


@pytest.mark.parametrize(
    ("language", "mode_name", "color_name"),
    [
        pytest.param("en", "Light mode", "Light color", id="en-us-spelling"),
        pytest.param("en-GB", "Light mode", "Light colour", id="en-gb-spelling"),
    ],
)
async def test_light_color_translations(
    hass, language: str, mode_name: str, color_name: str
) -> None:
    """en is US English; en-GB overrides only the "colour" strings (#65)."""
    from homeassistant.helpers.translation import async_get_translations

    strings = await async_get_translations(hass, language, "entity", [DOMAIN])
    prefix = f"component.{DOMAIN}.entity"
    # Light mode has no en-GB override, so it falls back to en.
    assert strings[f"{prefix}.select.light_mode.name"] == mode_name
    assert strings[f"{prefix}.text.light_color.name"] == color_name
