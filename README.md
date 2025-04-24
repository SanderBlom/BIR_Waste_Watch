# BIR Waste Watch for Home Assistant

[![Latest Release](https://badgen.net/github/release/SanderBlom/BIR_Waste_Watch/releases)](https://github.com/SanderBlom/BIR_Waste_Watch/releases)
[![Validate with hassfest](https://github.com/SanderBlom/BIR_Waste_Watch/actions/workflows/hassfest.yml/badge.svg)](https://github.com/SanderBlom/BIR_Waste_Watch/actions/workflows/hassfest.yml)
[![HACS Action](https://github.com/SanderBlom/BIR_Waste_Watch/actions/workflows/hacs.yml/badge.svg)](https://github.com/SanderBlom/BIR_Waste_Watch/actions/workflows/hacs.yml)

![](/assets/logo.png)
This is not an official integration from BIR!

This Home Assistant extension dynamically generates sensors for waste collection schedules based on your address. It fetches the data from BIRs API to find the appropriate dates for waste pickup and creates sensors accordingly.

## 🌟 Features

- 📍 Dynamically creates sensors based on the available waste types (e.g., Mixed Waste, Paper & Plastic, Food Waste or Glass & Metal) for your address.
- 🎛 Easy setup through Home Assistant's UI.

## 📝 Prerequisites

- Home Assistant instance up and running.
- Your garbage is picked up by BIR and your address is listed in BIR.no's database.

## 📦 Installation

### Option 1: HACS
- Follow [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=sanderblom&repository=690180198&category=integration) and install it
- Restart Home Assistant

  *or*
- Go to `HACS` -> `Integrations`,
- Select `+`,
- Search for `BIR Waste Watch` and install it,
- Restart Home Assistant
- Go to `Devices & services` and click add integration and search for `BIR Waste Watch`
- Follow the configuration guide bellow

### Option 2: Manual

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

## Configuration 

During the setup phase, you'll need to provide a URL from BIR.no

1. Go to [bir.no](https://bir.no/).
2. Enter your address in the search field and click on your address.
3. Once you can see the dates, copy the URL from the address bar(should looks something similar to this: `https://bir.no/adressesoek/?rId=c2435f0f-2e4b-4908-86cf-bafbd3a2cf61&name=Lillehatten%20330,%20Bergen`).
4. Paste this URL into the setup phase of the integration in Home Assistant's UI.

