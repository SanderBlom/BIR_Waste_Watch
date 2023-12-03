# BIR Waste Watch for Home Assistant
:warning: This is not an official integration from BIR!
![](/assets/logo.png)
This Home Assistant extension dynamically generates sensors for waste collection schedules based on your address. It scrapes the BIR.no website to find the appropriate dates for waste pickup and creates sensors accordingly.

## 🌟 Features

- 📍 Dynamically creates sensors based on the available waste types (e.g., Mixed Waste, Paper & Plastic or Food Waste) for your address.
- 🎛 Easy setup through Home Assistant's UI.

## 📝 Prerequisites

- Home Assistant instance up and running.
- Your garbage is picked up by BIR and your address is listed in BIR.no's database.

## 📦 Installation

1. **Download the latest release [here](https://github.com/SanderBlom/BIR_Waste_Watch/releases).**

2. **Extract the zip and copy the files to the custom_components folder.**

    ```bash
    cp -r BIR_Waste_Watch/ /config/custom_components/
    ```

3. **Restart Home Assistant**

    Restart your Home Assistant instance to pick up the new files.

4. **Add Integration**

    - Go to Home Assistant's UI.
    - Navigate to **Settings**.
    - Go to **Devices and Services**.
    - Click **Add Integration**.
    - Search for **BIR Waste Watch** and click to add.

5. **Configuration**

During the setup phase, you'll need to provide a URL from BIR.no

1. Go to [bir.no](https://bir.no/).
2. Enter your address in the search field.
3. Once you can see the dates, copy the URL from the address bar(should looks something similar to this: `https://bir.no/adressesoek/?rId=c2435f0f-2e4b-4908-86cf-bafbd3a2cf61&name=Lillehatten%20330,%20Bergen`).
4. Paste this URL into the setup phase of the integration in Home Assistant's UI.

## Tips: Changing Dates to 'Days Until Pickup'

If you'd like to display the remaining days until the next pickup instead of the dates, you can create a [template sensor](https://www.home-assistant.io/integrations/template/) in Home Assistant.

Here's an example:

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
      days_until_paper_and_plastic_waste:
        friendly_name: "Days Until Paper & Plastic Waste"
        value_template: >-
          {% set pick_up_date = as_timestamp(states('sensor.paper_and_plastic_waste')) %}
          {% set current_date = as_timestamp(now().strftime('%Y-%m-%d')) %}
          {% set days_remaining = ((pick_up_date - current_date) / 86400) | int %}
          {% if days_remaining >= 0 %}
            {{ days_remaining }}
          {% else %}
            unknown
          {% endif %}


```
