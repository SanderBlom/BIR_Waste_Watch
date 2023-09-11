import voluptuous as vol
from urllib.parse import urlparse, parse_qs
from homeassistant import config_entries

class TrashScheduleConfigFlow(config_entries.ConfigFlow, domain="BIR_Waste_Watch"):
    async def async_step_user(self, user_input=None):
        errors = {}
        
        if user_input is not None:
            url = user_input.get("url")
            parsed_url = urlparse(url)
            
            update_interval = user_input.get("update_interval", 0)
            
            if int(update_interval) < 8:
                errors["update_interval"] = "min_value_8_hours"
            
            # Check if the URL is from bir.no
            if parsed_url.netloc != "bir.no":
                errors["base"] = "invalid_url_domain"
            
            # Check if the URL contains rId and name parameters
            query_params = parse_qs(parsed_url.query)
            if "rId" not in query_params or "name" not in query_params:
                errors["base"] = "missing_parameters"
            
            if not errors:
                return self.async_create_entry(
                    title="Waste Collection Sensor",
                    data={"url": url, "update_interval": user_input["update_interval"]},
                )
        
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("url", default="https://bir.no/adressesoek/yourCustomUUIDandAddress"): str,
                    vol.Required("update_interval", default=8): vol.All(vol.Coerce(int)),
                }
            ),
            errors=errors

        )
