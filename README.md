# STM32-Custom-Bootloader
# STM32 Wireless OTA Firmware Update

A complete wireless Over-The-Air (OTA) firmware update system for the **STM32F103C8** microcontroller. The device connects to a WiFi network via the **ESP8266** module, downloads a firmware binary from a TCP server, stores it in **W25Q external SPI flash**, and automatically applies the update through a custom bootloader — no physical access or wired connection required after initial programming.

---

## Table of Contents

- [Features](#features)
- [System Architecture](#system-architecture)
- [OTA Update Flow](#ota-update-flow)
- [Hardware Requirements](#hardware-requirements)
- [Pin Connections](#pin-connections)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Getting Started](#getting-started)
- [Verification](#verification)
- [License](#license)

---

## Features

- **Fully wireless** — firmware updates delivered over WiFi, no Ethernet cable needed
- **External flash storage** — W25Q SPI flash offloads OTA image storage from the MCU's limited internal flash
- **Chunked transfer with ACK** — reliable 512-byte chunk protocol with per-chunk acknowledgment prevents data loss
- **Bootloader validation** — CRC check, magic number, and size validation before any write to internal flash
- **Automatic rollback** — if validation fails, bootloader clears the OTA flag and boots the existing application
- **Zero user intervention** — one button press triggers the full download-validate-flash-boot sequence
- **Debug logging** — real-time UART logs over a USB-to-TTL converter throughout the entire process

---

## System Architecture

```
                          WiFi (TCP)
  ┌─────────────────────────────────────────────────────┐
  │                                                     │
  │  ┌───────────────────────────────────────────────┐  │
  │  │               STM32F103C8                     │  │
  │  │                                               │  │
  │  │   ┌─────────────────┐   ┌─────────────────┐  │  │
  │  │   │   Application   │   │   Bootloader    │  │  │
  │  │   │  - OTA trigger  │   │  - Read W25Q    │  │  │
  │  │   │  - ESP8266 ctrl │   │  - Validate CRC │  │  │
  │  │   │  - W25Q write   │   │  - Flash MCU    │  │  │
  │  │   └────────┬────────┘   └────────┬────────┘  │  │
  │  │            │ UART2               │ SPI1       │  │
  │  └────────────┼─────────────────────┼────────────┘  │
  │               │                     │               │
  │        ┌──────▼──────┐       ┌──────▼──────┐        │
  │        │   ESP8266   │       │  W25Q Flash │        │
  │        │  WiFi Module│       │  (External) │        │
  │        └─────────────┘       └─────────────┘        │
  │                                                     │
  └──────────────────── TCP Server (PC) ────────────────┘
```

| Component       | Interface | Role                                                |
|-----------------|-----------|-----------------------------------------------------|
| ESP8266         | UART2     | WiFi connectivity, TCP client, firmware download    |
| W25Q SPI Flash  | SPI1      | Intermediate storage for downloaded OTA image       |
| Application     | —         | Orchestrates download, writes flash, triggers reboot|
| Bootloader      | —         | Validates OTA image, flashes MCU, boots new firmware|

---

## OTA Update Flow

```
  [Button Press]
       │
       ▼
  [Init ESP8266 + W25Q Flash]
       │
       ▼
  [Connect to WiFi AP]
       │
       ▼
  [TCP Connect → OTA Server]
       │
       ▼
  [Send "START" Command]
       │
       ▼
  [Receive 512B Chunk] ──► [Write to W25Q Flash] ──► [Send ACK]
       │◄────────────────────── repeat until complete ──────────┘
       │
       ▼
  [Set OTA Flag in Memory]
       │
       ▼
  [NVIC System Reset]
       │
       ▼
  ╔═══════════════════════════╗
  ║        BOOTLOADER         ║
  ╠═══════════════════════════╣
  ║  Detect OTA Flag          ║
  ║  Read Image from W25Q     ║
  ║  Validate Header + CRC    ║──► [Fail] → Clear flag → Boot existing app
  ║  Erase Internal Flash     ║
  ║  Write New Firmware       ║
  ║  Update App Header        ║
  ║  Jump to Application      ║
  ╚═══════════════════════════╝
       │
       ▼
  [Updated Application Running ✓]
```

---

## Hardware Requirements

| Component                | Notes                                              |
|--------------------------|----------------------------------------------------|
| STM32F103C8 (Blue Pill)  | Target microcontroller                             |
| ESP8266 WiFi Module      | With ESP-Adapter board recommended                 |
| W25Q SPI Flash           | W25Q16 / W25Q32 / W25Q64 — any capacity works     |
| USB-to-TTL Converter     | For UART1 debug output                             |
| ST-Link V2               | For initial bootloader + application flashing      |
| Push Button              | OTA trigger                                        |
| LED + 220Ω Resistor      | Application status indicator                       |

---

## Pin Connections

### ESP8266 → STM32 (UART2)

| ESP8266 Adapter | STM32F103C8    |
|-----------------|----------------|
| TX              | PA3 (UART2 RX) |
| RX              | PA2 (UART2 TX) |
| VCC             | 5V             |
| GND             | GND            |

> **Note:** The ESP8266 logic level is 3.3V. The adapter handles level conversion; do not connect the ESP8266 module directly to 5V.

### W25Q Flash → STM32 (SPI1)

| W25Q Pin | STM32F103C8       |
|----------|-------------------|
| CLK      | PA5 (SPI1 SCK)    |
| MISO     | PA6 (SPI1 MISO)   |
| MOSI     | PA7 (SPI1 MOSI)   |
| CS       | PB0 (GPIO Output) |
| VCC      | 3.3V              |
| GND      | GND               |

### Peripherals

| Component        | STM32F103C8          |
|------------------|----------------------|
| USB-TTL RX       | PA9 (UART1 TX)       |
| Push Button      | PA1 (EXTI, Pull-up)  |
| Button (other)   | GND                  |
| LED Anode (+)    | PA0 (GPIO Output)    |
| LED Cathode (–)  | GND via 220Ω         |

---

## Project Structure

```
├── Application/
│   ├── Core/Src/
│   │   └── main.c               # OTA trigger, main loop, UART printf routing
│   ├── Libs/
│   │   ├── ESP8266_STM32.c/.h   # WiFi + TCP OTA client driver
│   │   └── W25Qxx.c/.h          # W25Q SPI flash driver
│   └── Debug/
│       ├── app_final.py         # Generates ota_image.bin with header + CRC
│       └── server.py            # Python TCP server for OTA delivery
│
└── Bootloader/
    ├── Core/Src/
    │   └── main.c               # OTA validation, internal flash write, jump
    └── Libs/
        └── W25Qxx.c/.h          # W25Q SPI flash driver
```

---

## Configuration

### WiFi & Server (`Application/Libs/ESP8266_STM32.c`)

```c
#define WiFi_ssid    "your_network_ssid"
#define WiFi_pssd    "your_network_password"
#define SERVER_IP    "192.168.x.x"    // IP address of the PC running server.py
#define SERVER_PORT  5678
```

### UART Instance (`Application/Libs/ESP8266_STM32.h`)

```c
#define ESP_UART    huart2
```

### Flash Chip Size (`W25Qxx.c` — both Application and Bootloader)

```c
#define W25Q_SPI        hspi1
#define chipSizeinmb    32    // Match your chip: 16, 32, 64, etc.
```

### STM32CubeMX — SPI1

| Parameter    | Value              |
|--------------|--------------------|
| Mode         | Full-Duplex Master |
| Hardware NSS | Disabled           |
| Data Size    | 8 Bits             |
| First Bit    | MSB First          |
| CPOL         | Low                |
| CPHA         | 1 Edge             |
| Baud Rate    | ~1 Mbps            |

### STM32CubeMX — UART2

| Parameter   | Value    |
|-------------|----------|
| Baud Rate   | 115200   |
| Word Length | 8 Bits   |
| Parity      | None     |
| Stop Bits   | 1        |
| DMA RX      | Circular |

> The **Circular DMA** mode on UART2 RX is required to handle continuous incoming firmware data without CPU involvement.

---

## Getting Started

### 1. Flash the Bootloader

1. Open **STM32CubeProgrammer** and connect via ST-Link
2. Erase the entire flash memory
3. Flash the compiled bootloader ELF/HEX file

### 2. Flash the Application

1. Open the Application project in **STM32CubeIDE**
2. Create a debug configuration and set **Start Address** to `0x08004400`
3. Launch the debugger and run the application

### 3. Generate the OTA Binary

After building the updated application firmware:

```bash
cd Application/Debug/
python app_final.py
```

This produces `ota_image.bin` with the required OTA header, firmware size, and CRC.

### 4. Start the TCP Server

```bash
cd Application/Debug/
python server.py
```

The server listens for incoming connections and serves `ota_image.bin` in 512-byte chunks.

### 5. Trigger the OTA Update

Press the **push button** on the STM32 board. The process runs fully automatically:

1. ESP8266 initializes and connects to WiFi
2. TCP connection established to the server
3. Firmware downloaded chunk by chunk, written to W25Q flash
4. OTA flag set → MCU resets
5. Bootloader reads W25Q, validates CRC, flashes internal memory
6. Updated application boots ✅

---

## Verification

After the update completes, verify the new firmware is running:

**Via STM32CubeProgrammer:**
- Connect with ST-Link
- Navigate to *Memory & File Editing*
- Read the application header region in flash
- Confirm: magic number ✓, CRC ✓, version number incremented ✓

**Via Serial Terminal:**
- Connect USB-to-TTL to PA9
- Open terminal at **115200 baud**
- Real-time logs are printed throughout the entire OTA process

---
