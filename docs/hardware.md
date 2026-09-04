# Hardware Notes

Target gateway board: Waveshare ESP32-S3-LCD-1.47.

The Waveshare wiki lists the board as an ESP32-S3R8 with 16 MB flash, 8 MB PSRAM, 2.4 GHz Wi-Fi/BLE, USB serial, TF card slot, RGB LED, and a 1.47 inch 172 x 320 ST7789 LCD. The LCD pin map used by the firmware is:

| LCD signal | ESP32-S3 GPIO |
| --- | --- |
| MOSI | GPIO45 |
| SCLK | GPIO40 |
| CS | GPIO42 |
| DC | GPIO41 |
| RST | GPIO39 |
| BL | GPIO48 |

The onboard RGB LED is GPIO38. This first firmware does not require it.

The ESP32-S3-LCD-1.47B variant uses GPIO46 for the display backlight, so change `TFT_BL` in `firmware/ragnar_espnow_gateway/platformio.ini` if using the B board.

