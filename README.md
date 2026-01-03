# BIR Waste Watch for Home Assistant

[![Latest Release](https://badgen.net/github/release/SanderBlom/BIR_Waste_Watch/releases)](https://github.com/SanderBlom/BIR_Waste_Watch/releases)
[![Validate with hassfest](https://github.com/SanderBlom/BIR_Waste_Watch/actions/workflows/hassfest.yml/badge.svg)](https://github.com/SanderBlom/BIR_Waste_Watch/actions/workflows/hassfest.yml)
[![HACS Action](https://github.com/SanderBlom/BIR_Waste_Watch/actions/workflows/hacs.yml/badge.svg)](https://github.com/SanderBlom/BIR_Waste_Watch/actions/workflows/hacs.yml)

![](/assets/logo.png)
This is not an official integration from BIR!

This Home Assistant extension dynamically generates sensors for waste collection schedules based on your address. It fetches the data from BIRs API to find the appropriate dates for waste pickup and creates sensors accordingly.

## 🌟 Features

- 🔍 **Easy address search**: Just type your address and select from the results - no need to copy URLs
- 📍 **Dynamic sensors**: Automatically creates sensors for each waste type (e.g., Mixed Waste, Paper & Plastic, Food Waste, Glass & Metal)
- 🔄 **Change address anytime**: Update your address through the integration's configuration
- 🎛 **Simple UI setup**: Everything is configured through Home Assistant's interface

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

Setting up BIR Waste Watch is easy with the built-in address search:

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for **BIR Waste Watch** and click to add
3. Enter your address in the search field (e.g., "Lillehatten 330")
4. Select your address from the list of matching results
5. Done! Sensors will be created for each waste type at your address

![Address Search](/assets/config_flow.png)

## Changing Your Address

If you move or need to change your address:

1. Go to **Settings** → **Devices & Services**
2. Find **BIR Waste Watch** and click on it
3. Click the **Configure** button (gear icon ⚙️)
4. Enter your new address and search
5. Select the correct address from the results
6. The integration will automatically update with your new address

