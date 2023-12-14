# BIR Waste Watch for Home Assistant

[![Latest Release](https://badgen.net/github/release/SanderBlom/BIR_Waste_Watch/releases)](https://github.com/SanderBlom/BIR_Waste_Watch/releases)
[![Validate with hassfest](https://github.com/SanderBlom/BIR_Waste_Watch/actions/workflows/hassfest.yml/badge.svg)](https://github.com/SanderBlom/BIR_Waste_Watch/actions/workflows/hassfest.yml)
[![HACS Action](https://github.com/SanderBlom/BIR_Waste_Watch/actions/workflows/hacs.yml/badge.svg)](https://github.com/SanderBlom/BIR_Waste_Watch/actions/workflows/hacs.yml)

⚠️ This is not an official integration from BIR!
![](/assets/logo.png)

This Home Assistant extension dynamically generates sensors for waste collection schedules based on your address, scraping the BIR.no website for accurate pickup dates.

## 🌟 Features

- 📍 Dynamically creates sensors for various waste types (e.g., Mixed Waste, Paper & Plastic, Food Waste) based on your address.
- 🎛 Easy setup through Home Assistant's UI.


## Tips: Changing Dates to 'Days Until Pickup'

To display the days until the next waste pickup, use a template sensor in Home Assistant. Here's an example configuration for mixed waste:

```yaml
# configuration.yaml
sensor:
  - platform: template
    sensors:
      days_until_mixed_waste:
        friendly_name: "Days Until Mixed Waste"
        value_template: >-
          {% set pick_up_date = as_timestamp(states('sensor.mixed_waste')) %}
          {% set current_date = as_timestamp(now().strftime('%Y-%m-%d')) %}
          {% set days_remaining = ((pick_up_date - current_date) / 86400) | int %}
          {% if days_remaining >= 0 %}
            {{ days_remaining }}
          {% else %}
            unknown
          {% endif %}
```
