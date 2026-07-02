# Python ↔ Arduino UNO 프로토콜

약국 PC에서 FastAPI가 UNO(USB 시리얼)로 **점자 + NFC 출력 JOB**을 보냅니다.

## Python → UNO (요청, UTF-8 JSON + `\n`)

```json
{"cmd":"label","job_id":"a1b2c3","braille":"⠁⠃...","nfc_url":"https://example.com/medicine/MFDS-123","label":"타이레놀"}
```

## UNO → Python (응답, UTF-8 JSON + `\n`)

성공:

```json
{"status":"ok","job_id":"a1b2c3","braille":true,"nfc":true}
```

실패:

```json
{"status":"fail","job_id":"a1b2c3","step":"nfc","msg":"No card found"}
```

## UNO 내부 순서 (권장)

1. JSON 수신
2. Mega(SoftwareSerial)로 `braille` UTF-8 전송 → 바이트마다 ACK
3. PN532로 `nfc_url` **NDEF URI** 기록 (NTAG213/215 등 Type 2 태그)
4. JSON 응답 한 줄 전송

펌웨어: [`firmware/uno_gateway/uno_gateway.ino`](../firmware/uno_gateway/uno_gateway.ino)

## 시리얼 포트 확인

| OS | 확인 방법 | .env 예시 |
|----|-----------|-----------|
| macOS | `ls /dev/cu.usb*` | `ARDUINO_PORT=/dev/cu.usbmodem1101` |
| Windows | 장치 관리자 → COM 포트 | `ARDUINO_PORT=COM5` |
| Linux | `ls /dev/ttyACM*` | `ARDUINO_PORT=/dev/ttyACM0` |

아두이노 IDE **시리얼 모니터를 닫은 뒤** Python이 같은 포트를 사용해야 합니다.

## NFC 태그

- **권장:** NTAG213 / NTAG215 (ISO14443A Type 2)
- **형식:** NDEF URI — 스마트폰에서 태그 대면 `nfc_url` 링크가 바로 열림
- Mifare Classic 1K만 있는 태그는 Type 2 쓰기 미지원 → NTAG 태그 사용
