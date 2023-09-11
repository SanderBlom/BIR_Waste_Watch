# Use the official Home Assistant image as the base image
FROM homeassistant/home-assistant:latest

# Copy the custom_component code into the container
COPY src/* /config/custom_components/BIR_Waste_Watch/
COPY src/translations/* /config/custom_components/BIR_Waste_Watch/translations/