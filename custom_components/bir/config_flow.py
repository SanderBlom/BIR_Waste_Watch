import voluptuous as vol
from urllib.parse import urlparse, parse_qs
from homeassistant import config_entries

class TrashScheduleConfigFlow(config_entries.ConfigFlow, domain="BIR_Waste_Watch"):
    async def async_step_user(self, user_input=None):
        errors = {}
        
        if user_input is not None:
            url = user_input.get("url")
            parsed_url = urlparse(url)
            
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
                    data={"url": url},
                )
        
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("url", default=""): str,
                }
            ),
            errors=errors

        )
