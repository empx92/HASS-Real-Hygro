"""Config flow for Real Hygro."""
from __future__ import annotations

import re
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import *

_DURATION_HMS = re.compile(r"^\d{2}:\d{2}:\d{2}$")
_DURATION_MS = re.compile(r"^\d{2}:\d{2}$")


def _base_schema(defaults: dict[str, Any]) -> vol.Schema:
    text = selector.TextSelector()
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults[CONF_NAME]): text,
            vol.Required(CONF_HUMIDITY_SENSOR, default=defaults[CONF_HUMIDITY_SENSOR]): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["sensor"], multiple=False)
            ),
            vol.Required(CONF_SWITCH_ENTITY, default=defaults[CONF_SWITCH_ENTITY]): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["switch"], multiple=False)
            ),
            vol.Required(CONF_TARGET_HUMIDITY, default=str(defaults[CONF_TARGET_HUMIDITY])): text,
            vol.Required(CONF_DRY_TOLERANCE, default=str(defaults[CONF_DRY_TOLERANCE])): text,
            vol.Required(CONF_WET_TOLERANCE, default=str(defaults[CONF_WET_TOLERANCE])): text,
            vol.Required(CONF_MIN_HUMIDITY, default=str(defaults[CONF_MIN_HUMIDITY])): text,
            vol.Required(CONF_MAX_HUMIDITY, default=str(defaults[CONF_MAX_HUMIDITY])): text,
            vol.Required(CONF_MIN_RUNTIME, default=defaults[CONF_MIN_RUNTIME]): text,
            vol.Required(CONF_AUTOMATIC_ENABLED, default=defaults[CONF_AUTOMATIC_ENABLED]): selector.BooleanSelector(),
            vol.Required(CONF_RISE_TIME, default=defaults[CONF_RISE_TIME]): text,
            vol.Required(CONF_RISE_PERCENT, default=str(defaults[CONF_RISE_PERCENT])): text,
        }
    )


def _to_int(value: str, min_v: int, max_v: int, key: str, errors: dict[str, str]) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        errors[key] = "not_a_number"
        return min_v
    if number < min_v or number > max_v:
        errors[key] = "out_of_range"
    return number


def _to_float(value: str, min_v: float, max_v: float, key: str, errors: dict[str, str]) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        errors[key] = "not_a_number"
        return min_v
    if number < min_v or number > max_v:
        errors[key] = "out_of_range"
    return number


def _normalize(data: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    errors: dict[str, str] = {}
    normalized = dict(data)

    if not str(data[CONF_NAME]).strip():
        errors[CONF_NAME] = "name_required"
    normalized[CONF_NAME] = str(data[CONF_NAME]).strip()

    normalized[CONF_TARGET_HUMIDITY] = _to_int(data[CONF_TARGET_HUMIDITY], 1, 100, CONF_TARGET_HUMIDITY, errors)
    normalized[CONF_DRY_TOLERANCE] = _to_int(data[CONF_DRY_TOLERANCE], 0, 20, CONF_DRY_TOLERANCE, errors)
    normalized[CONF_WET_TOLERANCE] = _to_int(data[CONF_WET_TOLERANCE], 0, 20, CONF_WET_TOLERANCE, errors)
    normalized[CONF_MIN_HUMIDITY] = _to_int(data[CONF_MIN_HUMIDITY], 1, 100, CONF_MIN_HUMIDITY, errors)
    normalized[CONF_MAX_HUMIDITY] = _to_int(data[CONF_MAX_HUMIDITY], 1, 100, CONF_MAX_HUMIDITY, errors)
    normalized[CONF_RISE_PERCENT] = _to_float(data[CONF_RISE_PERCENT], 0.1, 30, CONF_RISE_PERCENT, errors)

    if not _DURATION_HMS.match(str(data[CONF_MIN_RUNTIME])):
        errors[CONF_MIN_RUNTIME] = "invalid_hms"
    if not _DURATION_MS.match(str(data[CONF_RISE_TIME])):
        errors[CONF_RISE_TIME] = "invalid_ms"

    if normalized[CONF_MIN_HUMIDITY] >= normalized[CONF_MAX_HUMIDITY]:
        errors[CONF_MIN_HUMIDITY] = "min_max_invalid"
        errors[CONF_MAX_HUMIDITY] = "min_max_invalid"

    return normalized, errors


class RealHygroConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        defaults = {
            CONF_NAME: DEFAULT_NAME,
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
        errors = {}
        if user_input is not None:
            normalized, errors = _normalize(user_input)
            if not errors:
                return self.async_create_entry(title=normalized[CONF_NAME], data=normalized)
            defaults.update(user_input)

        return self.async_show_form(step_id="user", data_schema=_base_schema(defaults), errors=errors)

    @staticmethod
    @config_entries.callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return RealHygroOptionsFlow(config_entry)


class RealHygroOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        defaults = dict(self.config_entry.data)
        errors = {}
        if user_input is not None:
            normalized, errors = _normalize(user_input)
            if not errors:
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    title=normalized[CONF_NAME],
                    data=normalized,
                )
                await self.hass.config_entries.async_reload(self.config_entry.entry_id)
                return self.async_create_entry(title="", data={})
            defaults.update(user_input)

        return self.async_show_form(step_id="init", data_schema=_base_schema(defaults), errors=errors)
