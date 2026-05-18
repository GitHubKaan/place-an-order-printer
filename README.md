# place-an-order-printer

The Place An Order Printer Service is a system designed to process and print orders received via the Place An Order API.

<img src="assets/logo/pao_logo_white_v1.png" width="200px"/>

> [!CAUTION]
> © 2026 Kâan Turan, acting under Place An Order and Turanics. All rights reserved. Unauthorized use, copying, modification, distribution, or reproduction of this software and its associated files is strictly prohibited. Warranty claims shall be deemed void if the official tamper-evident seals are removed, damaged, or altered. In such cases, Place An Order reserves the right to refuse repair or servicing of the device.

> [!NOTE]
> Place An Order printer devices are custom-built and/or modified exclusively by Place An Order. All systems and firmware used on these devices are encrypted and proprietary. Issuance of a valid ```DEVICE_TOKEN``` can only be performed by authorized Place An Order personnel.

## Hardware
The device is based on a modified Epson TM-T20III platform and has been custom-engineered for exclusive operation within the Place An Order infrastructure. An integrated Raspberry Pi Zero W provides the embedded control system and securely stores a unique ```DEVICE_TOKEN``` assigned to the respective hospitality business. To ensure system integrity and prevent unauthorized modification, external service interfaces including USB Type-B and RS-232 have been permanently removed. The internal connection between the Raspberry Pi Zero W and the printer controller is fixed and non-removable. A dedicated step-down power module integrated into the 24V power input supplies regulated 5V power to the embedded system. All internal components are mechanically secured using permanent mounting hardware. An optional Ethernet interface may be included depending on deployment requirements.

## Guarantee of functionality
- Requires a stable internet connection.
- Clean with a dry cloth only.
- Avoid exposure to heat, steam, and water
- Use only power supplies listed in the user instruction

## Setup
- <a href="https://www.python.org/downloads/" target="_blank">Python</a> is required
- <a href="https://pypi.org/project/pip/" target="_blank">Pip</a> is required
- <a href="https://wiki.ubuntuusers.de/Makefile/" target="_blank">Makefile</a> is required<br/>

1. Clone the `installer.example.sh`, rename the file to `installer.sh` and fill in the config block at the top of the file.
2. Copy the installer script to the Raspberry Pi Zero W
3. SSH into the Raspberry Pi Zero W and run the installer using:
```bash
chmod +x installer.sh && sudo bash installer.sh
```
4. Reboot:
```bash
sudo shutdown -r now
```

## Environment
For local development, create a `.env.dev` and a `.env.prod` file inside the root directory using _.env.example_ as a template.

- `.env.dev` (development environment on ```make dev```)
- `.env.prod` (production environment on ```make prod```)

## Run application
Run in development mode: ```make dev```<br/>
Run in production mode: ```make prod```

## Automatic updates
When installed through `installer.sh`, the device is configured to check the repository periodically and automatically apply new commits.
A systemd timer runs the update helper, pulls the latest code, updates dependencies, and restarts the `printservice` automatically.

To trigger an update immediately:
```bash
sudo systemctl start printservice-update.service
```

## Tamper-evident Seal
The official Place An Order tamper-evident seal should look like this:<br/>
<img src="assets/pao_tamper_evident_seal.png" alt="pao tamper evident seal" width="200px"/>