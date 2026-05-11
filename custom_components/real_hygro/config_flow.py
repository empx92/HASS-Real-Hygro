"""Config flow for Real Hygro."""
from __future__ import annotations

import re
from datetime import timedelta

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


def _validate_hms(value: str) -> str:
    if not _DURATION_HMS.match(value):
        raise vol.Invalid("Format muss hh:mm:ss sein")
    return value


def _validate_ms(value: str) -> str:
    if not _DURATION_MS.match(value):
        raise vol.Invalid("Format muss mm:ss sein")
    return value


class RealHygroConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Real Hygro."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="Luftentfeuchter", data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_HUMIDITY_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["sensor"]) 
                ),
                vol.Required(CONF_SWITCH_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["switch"])
                ),
                vol.Required(CONF_TARGET_HUMIDITY, default=DEFAULT_TARGET_HUMIDITY): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
                vol.Required(CONF_DRY_TOLERANCE, default=DEFAULT_DRY_TOLERANCE): vol.All(vol.Coerce(int), vol.Range(min=0, max=20)),
                vol.Required(CONF_WET_TOLERANCE, default=DEFAULT_WET_TOLERANCE): vol.All(vol.Coerce(int), vol.Range(min=0, max=20)),
                vol.Required(CONF_MIN_HUMIDITY, default=DEFAULT_MIN_HUMIDITY): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
                vol.Required(CONF_MAX_HUMIDITY, default=DEFAULT_MAX_HUMIDITY): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
                vol.Required(CONF_MIN_RUNTIME, default=DEFAULT_MIN_RUNTIME): vol.All(str, _validate_hms),
                vol.Required(CONF_AUTOMATIC_ENABLED, default=DEFAULT_AUTOMATIC_ENABLED): selector.BooleanSelector(),
                vol.Required(CONF_RISE_TIME, default=DEFAULT_RISE_TIME): vol.All(str, _validate_ms),
                vol.Required(CONF_RISE_PERCENT, default=DEFAULT_RISE_PERCENT): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=30)),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema)
