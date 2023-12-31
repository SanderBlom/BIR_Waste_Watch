# BIR Waste Watch for Home Assistant

[![Latest Release](https://badgen.net/github/release/SanderBlom/BIR_Waste_Watch/releases)](https://github.com/SanderBlom/BIR_Waste_Watch/releases)
[![Validate with hassfest](https://github.com/SanderBlom/BIR_Waste_Watch/actions/workflows/hassfest.yml/badge.svg)](https://github.com/SanderBlom/BIR_Waste_Watch/actions/workflows/hassfest.yml)
[![HACS Action](https://github.com/SanderBlom/BIR_Waste_Watch/actions/workflows/hacs.yml/badge.svg)](https://github.com/SanderBlom/BIR_Waste_Watch/actions/workflows/hacs.yml)

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
    cp -r bir/ /config/custom_components/
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

