# UNO Gateway 펌웨어

PC(FastAPI) ↔ Arduino UNO ↔ Mega(점자) + PN532(NFC)

- 프로토콜: [`docs/hardware-protocol.md`](../../docs/hardware-protocol.md)
- 스케치: [`uno_gateway.ino`](uno_gateway.ino)

## Arduino IDE 라이브러리

| 라이브러리 | 설치 |
|-----------|------|
| **ArduinoJson** (6.x) | 라이브러리 매니저 → "ArduinoJson" |
| **PN532** (Adafruit/Seeed) | 기존과 동일 — `PN532_SPI.h`, `PN532.h` |

## 보드·포트

- 보드: **Arduino UNO**
- PC ↔ UNO: USB 9600 baud
- UNO ↔ Mega: SoftwareSerial pin **2(RX), 3(TX)**, 9600 baud
- PN532: SPI SS=**10** (기존과 동일)

## 수정 전 → 후

| | 수정 전 (`split()`) | 수정 후 (`uno_gateway.ino`) |
|--|---------------------|------------------------------|
| PC 입력 | `cold` 같은 키워드 + 비트 문자열 | JSON 한 줄 |
| NFC | 4개 영문 문장 하드코딩 | `nfc_url` 필드 (앱 URL) |
| PC 응답 | 없음 | `{"status":"ok",...}` |
| idle | "입력되지 않음" 반복 | 조용히 대기 |

## 업로드 후 Python 연동

`.env`:

```env
HARDWARE_MODE=arduino
ARDUINO_PORT=/dev/cu.usbmodem1101   # Mac — ls /dev/cu.usb*
ARDUINO_BAUD=9600
```

**시리얼 모니터를 닫은 뒤** FastAPI를 실행하세요.

## NFC (NDEF URI)

- `nfc_url`을 **NDEF URI** 표준 형식으로 기록합니다.
- **NTAG213 / NTAG215** 등 Type 2 태그 권장 (Mifare Classic 전용 태그는 미지원).
- 스마트폰으로 태그를 대면 `/medicine/{id}` 페이지가 **링크로 열립니다**.

## Mega 측

점자는 JSON의 `braille` 문자열을 **UTF-8 바이트**로 Mega에 보냅니다.  
Mega 펌웨어가 예전 8비트 `sendmessage` 프로토콜이면, Mega도 UTF-8 수신에 맞게 맞추거나 Python/UNO에서 비트 변환을 추가해야 합니다.
