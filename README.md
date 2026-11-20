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
- Home Assistant 2026.3 or newer (Python 3.14.2+).
- Your garbage is picked up by BIR and your address is listed in BIR.no's database.

## 📦 Installation

On Home Assistant 2026.11 or newer, install BIR Waste Watch from the built-in Marketplace:

1. Go to **Settings → Marketplace** and search for **BIR Waste Watch**.
2. Select **Install** and follow the [configuration guide](#configuration). New installs do not require a restart.

On Home Assistant 2026.3–2026.10, install **BIR Waste Watch** through HACS, restart Home Assistant, then add it under **Settings → Devices & services → Add integration**.

## Configuration 

Setting up BIR Waste Watch is easy with the built-in address search:

1. Enter your address in the search field (e.g., "Lillehatten 330").
2. Select your address from the list of matching results.
3. Done! Sensors will be created for each waste type at your address.

![Address Search](/assets/config_flow.png)

## Changing Your Address

If you move or need to change your address:

1. Go to **Settings** → **Devices & Services**
2. Find **BIR Waste Watch** and click on it
3. Click the **Configure** button (gear icon ⚙️)
4. Enter your new address and search
5. Select the correct address from the results
6. The integration will automatically update with your new address
