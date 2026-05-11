"""Config flow for Real Hygro."""
from __future__ import annotations

import re
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    CONF_AUTOMATIC_ENABLED,
    CONF_DRY_TOLERANCE,
    CONF_HUMIDITY_SENSOR,
    CONF_MAX_HUMIDITY,
    CONF_MIN_HUMIDITY,
    CONF_MIN_RUNTIME,
    CONF_RISE_PERCENT,
    CONF_RISE_TIME,
    CONF_SWITCH_ENTITY,
    CONF_TARGET_HUMIDITY,
    CONF_WET_TOLERANCE,
    DEFAULT_AUTOMATIC_ENABLED,
    DEFAULT_DRY_TOLERANCE,
    DEFAULT_MAX_HUMIDITY,
    DEFAULT_MIN_HUMIDITY,
    DEFAULT_MIN_RUNTIME,
    DEFAULT_RISE_PERCENT,
    DEFAULT_RISE_TIME,
    DEFAULT_TARGET_HUMIDITY,
    DEFAULT_WET_TOLERANCE,
    DOMAIN,
)

_DURATION_HMS = re.compile(r"^\d{2}:\d{2}:\d{2}$")
_DURATION_MS = re.compile(r"^\d{2}:\d{2}$")


def _base_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_HUMIDITY_SENSOR, default=defaults[CONF_HUMIDITY_SENSOR]): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["sensor"], multiple=False)
            ),
            vol.Required(CONF_SWITCH_ENTITY, default=defaults[CONF_SWITCH_ENTITY]): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["switch"], multiple=False)
            ),
            vol.Required(CONF_TARGET_HUMIDITY, default=defaults[CONF_TARGET_HUMIDITY]): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
            vol.Required(CONF_DRY_TOLERANCE, default=defaults[CONF_DRY_TOLERANCE]): vol.All(vol.Coerce(int), vol.Range(min=0, max=20)),
            vol.Required(CONF_WET_TOLERANCE, default=defaults[CONF_WET_TOLERANCE]): vol.All(vol.Coerce(int), vol.Range(min=0, max=20)),
            vol.Required(CONF_MIN_HUMIDITY, default=defaults[CONF_MIN_HUMIDITY]): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
            vol.Required(CONF_MAX_HUMIDITY, default=defaults[CONF_MAX_HUMIDITY]): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
            vol.Required(CONF_MIN_RUNTIME, default=defaults[CONF_MIN_RUNTIME]): selector.TextSelector(),
            vol.Required(CONF_AUTOMATIC_ENABLED, default=defaults[CONF_AUTOMATIC_ENABLED]): selector.BooleanSelector(),
            vol.Required(CONF_RISE_TIME, default=defaults[CONF_RISE_TIME]): selector.TextSelector(),
            vol.Required(CONF_RISE_PERCENT, default=defaults[CONF_RISE_PERCENT]): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=30)),
        }
    )


def _validate_cross_fields(data: dict[str, Any]) -> dict[str, str]:
    errors: dict[str, str] = {}
    if not _DURATION_HMS.match(data[CONF_MIN_RUNTIME]):
        errors[CONF_MIN_RUNTIME] = "invalid_hms"
    if not _DURATION_MS.match(data[CONF_RISE_TIME]):
        errors[CONF_RISE_TIME] = "invalid_ms"
    if data[CONF_MIN_HUMIDITY] >= data[CONF_MAX_HUMIDITY]:
        errors[CONF_MIN_HUMIDITY] = "min_max_invalid"
        errors[CONF_MAX_HUMIDITY] = "min_max_invalid"
    return errors


class RealHygroConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Real Hygro."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        defaults = {
            CONF_HUMIDITY_SENSOR: "",
            CONF_SWITCH_ENTITY: "",
            CONF_TARGET_HUMIDITY: DEFAULT_TARGET_HUMIDITY,
            CONF_DRY_TOLERANCE: DEFAULT_DRY_TOLERANCE,
            CONF_WET_TOLERANCE: DEFAULT_WET_TOLERANCE,
            CONF_MIN_HUMIDITY: DEFAULT_MIN_HUMIDITY,
            CONF_MAX_HUMIDITY: DEFAULT_MAX_HUMIDITY,
            CONF_MIN_RUNTIME: DEFAULT_MIN_RUNTIME,
            CONF_AUTOMATIC_ENABLED: DEFAULT_AUTOMATIC_ENABLED,
            CONF_RISE_TIME: DEFAULT_RISE_TIME,
            CONF_RISE_PERCENT: DEFAULT_RISE_PERCENT,
        }
        errors: dict[str, str] = {}

        if user_input is not None:
            errors = _validate_cross_fields(user_input)
            if not errors:
                return self.async_create_entry(title="Luftentfeuchter", data=user_input)
            defaults.update(user_input)

        return self.async_show_form(step_id="user", data_schema=_base_schema(defaults), errors=errors)

    @staticmethod
    @config_entries.callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return RealHygroOptionsFlow(config_entry)


class RealHygroOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Real Hygro."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        defaults = dict(self.config_entry.data)
        errors: dict[str, str] = {}

        if user_input is not None:
            errors = _validate_cross_fields(user_input)
            if not errors:
                self.hass.config_entries.async_update_entry(self.config_entry, data=user_input)
                await self.hass.config_entries.async_reload(self.config_entry.entry_id)
                return self.async_create_entry(title="", data={})
            defaults.update(user_input)

        return self.async_show_form(step_id="init", data_schema=_base_schema(defaults), errors=errors)
