/*
 * 소리잇다 — UNO Gateway
 *
 * PC(FastAPI) USB Serial 9600  ←→  UNO  ←→  Mega(SoftwareSerial 2,3) 점자
 *                                    ↓
 *                                 PN532 SPI NFC
 *
 * 프로토콜: docs/hardware-protocol.md
 * 라이브러리: SPI, SoftwareSerial, PN532, ArduinoJson (6.x)
 */

#include <SPI.h>
#include <SoftwareSerial.h>
#include <string.h>
#include <PN532_SPI.h>
#include <PN532.h>
#include <ArduinoJson.h>

// ── 핀 (기존 스케치와 동일) ─────────────────────────────
#define SS_PIN 10
#define NDEF_URI_MAX 200    // NDEF URI 최대 길이 (Type 2 태그)
#define MEGA_ACK_TIMEOUT_MS 60000UL

SoftwareSerial megaSerial(2, 3);  // RX=2, TX=3

PN532_SPI pn532spi(SPI, SS_PIN);
PN532 nfc(pn532spi);

// ── Mega 통신 (기존 제어 바이트 유지) ───────────────────
static const uint8_t MEGA_START_BRAILLE_NFC = 0b10000001;
static const uint8_t MEGA_END_JOB = 0b11111111;

// ── forward ─────────────────────────────────────────────
void respondOk(const String &jobId, bool brailleOk, bool nfcOk);
void respondFail(const String &jobId, const char *step, const String &msg);

bool waitMegaAck(unsigned long timeoutMs) {
  unsigned long start = millis();
  while (!megaSerial.available()) {
    if (millis() - start > timeoutMs) {
      return false;
    }
  }
  megaSerial.read();
  return true;
}

bool megaWriteControl(uint8_t value) {
  megaSerial.write(value);
  return waitMegaAck(MEGA_ACK_TIMEOUT_MS);
}

// 점자(UTF-8 바이트)를 Mega로 전송 — 바이트마다 ACK 대기 (기존 sendmessage 패턴)
bool sendBrailleToMega(const String &braille) {
  for (unsigned int i = 0; i < braille.length(); i++) {
    megaSerial.write((uint8_t)braille.charAt(i));
    if (!waitMegaAck(MEGA_ACK_TIMEOUT_MS)) {
      return false;
    }
    delay(10);
  }
  return true;
}

// ── NFC: NDEF URI (Type 2 — NTAG213/215, Mifare Ultralight) ──
// 스마트폰이 태그를 "웹 링크"로 인식하도록 표준 NDEF 형식으로 기록

struct UriPrefix {
  const char *prefix;
  uint8_t code;
};

static const UriPrefix URI_PREFIXES[] = {
  {"https://www.", 0x02},
  {"http://www.",  0x01},
  {"https://",     0x04},
  {"http://",      0x03},
};

bool buildNdefUriMessage(const String &url, uint8_t *out, size_t &outLen) {
  if (url.length() == 0 || url.length() > NDEF_URI_MAX) {
    return false;
  }

  uint8_t prefixCode = 0x00;
  String uriBody = url;

  for (size_t i = 0; i < sizeof(URI_PREFIXES) / sizeof(URI_PREFIXES[0]); i++) {
    const char *p = URI_PREFIXES[i].prefix;
    if (url.startsWith(p)) {
      prefixCode = URI_PREFIXES[i].code;
      uriBody = url.substring(strlen(p));
      break;
    }
  }

  if (uriBody.length() == 0) {
    return false;
  }

  const uint8_t payloadLen = 1 + uriBody.length();
  const uint8_t recordLen = 3 + payloadLen;  // hdr + typeLen + payloadLen + type + payload

  if (recordLen > 250) {
    return false;
  }

  outLen = 0;
  out[outLen++] = 0x03;           // NDEF Message TLV
  out[outLen++] = (uint8_t)recordLen;
  out[outLen++] = 0xD1;           // MB=1 ME=1 SR=1 TNF=Well Known
  out[outLen++] = 0x01;           // Type length ('U')
  out[outLen++] = payloadLen;
  out[outLen++] = 'U';            // URI Record
  out[outLen++] = prefixCode;
  for (unsigned int i = 0; i < uriBody.length(); i++) {
    out[outLen++] = (uint8_t)uriBody.charAt(i);
  }
  out[outLen++] = 0xFE;           // Terminator TLV

  return true;
}

bool nfcWriteNdefUri(const String &url, String &errMsg) {
  uint8_t ndefBuf[280];
  size_t ndefLen = 0;
  if (!buildNdefUriMessage(url, ndefBuf, ndefLen)) {
    errMsg = "Invalid or too long URL";
    return false;
  }

  uint8_t uid[7] = {0};
  uint8_t uidLength = 0;

  if (!nfc.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uidLength, 5000)) {
    errMsg = "No card found";
    return false;
  }

  // Capability Container (page 3) — NDEF 가능 태그 표시
  uint8_t ccPage[4];
  if (!nfc.mifareultralight_ReadPage(3, ccPage)) {
    errMsg = "Tag not Type 2 (use NTAG213/215)";
    return false;
  }

  if (ccPage[0] != 0xE1) {
    uint8_t newCC[4] = {0xE1, 0x10, 0x12, 0x00};  // NDEF v1.0, NTAG213 호환
    if (!nfc.mifareultralight_WritePage(3, newCC)) {
      errMsg = "Failed to write CC";
      return false;
    }
  }

  // NDEF 메시지 → page 4부터 4바이트씩 기록
  size_t offset = 0;
  uint8_t page = 4;
  while (offset < ndefLen) {
    uint8_t pageData[4];
    for (int i = 0; i < 4; i++) {
      pageData[i] = (offset < ndefLen) ? ndefBuf[offset++] : 0x00;
    }
    if (!nfc.mifareultralight_WritePage(page, pageData)) {
      errMsg = "NDEF write failed at page " + String(page);
      return false;
    }
    page++;
  }

  delay(500);
  return true;
}

// ── JSON JOB 처리 ───────────────────────────────────────
void handleLabelJob(JsonDocument &doc) {
  const char *cmd = doc["cmd"] | "";
  String jobId = doc["job_id"] | "";
  String braille = doc["braille"] | "";
  String nfcUrl = doc["nfc_url"] | "";
  String label = doc["label"] | "";

  if (strcmp(cmd, "label") != 0) {
    respondFail(jobId, "parse", "Unknown cmd");
    return;
  }

  bool brailleOk = false;
  bool nfcOk = false;

  // 1) Mega: 점자 출력 시작
  if (!megaWriteControl(MEGA_START_BRAILLE_NFC)) {
    respondFail(jobId, "braille", "Mega start timeout");
    return;
  }

  // 2) 점자 데이터 전송
  if (braille.length() == 0) {
    brailleOk = true;  // 점자 없음 — 스킵
  } else {
    brailleOk = sendBrailleToMega(braille);
    if (!brailleOk) {
      respondFail(jobId, "braille", "Mega data timeout");
      return;
    }
  }

  // 3) Mega: 구간 종료
  if (!megaWriteControl(MEGA_END_JOB)) {
    respondFail(jobId, "braille", "Mega end timeout");
    return;
  }

  // 4) NFC NDEF URI 기록
  String nfcErr;
  nfcOk = nfcWriteNdefUri(nfcUrl, nfcErr);
  if (!nfcOk) {
    respondFail(jobId, "nfc", nfcErr);
    return;
  }

  respondOk(jobId, brailleOk, nfcOk);
}

void respondOk(const String &jobId, bool brailleOk, bool nfcOk) {
  StaticJsonDocument<192> doc;
  doc["status"] = "ok";
  doc["job_id"] = jobId;
  doc["braille"] = brailleOk;
  doc["nfc"] = nfcOk;
  serializeJson(doc, Serial);
  Serial.println();
}

void respondFail(const String &jobId, const char *step, const String &msg) {
  StaticJsonDocument<256> doc;
  doc["status"] = "fail";
  doc["job_id"] = jobId;
  doc["step"] = step;
  doc["msg"] = msg;
  doc["braille"] = false;
  doc["nfc"] = false;
  serializeJson(doc, Serial);
  Serial.println();
}

// ── setup / loop ────────────────────────────────────────
void setup() {
  Serial.begin(9600);
  megaSerial.begin(9600);
  SPI.begin();

  nfc.begin();
  uint32_t version = nfc.getFirmwareVersion();
  if (!version) {
    Serial.println(F("{\"status\":\"fail\",\"step\":\"init\",\"msg\":\"PN532 not found\"}"));
    while (true) {
      delay(1000);
    }
  }

  // PC(/python) 연결 대기 — idle 시 조용히 (기존 "입력되지 않음" 제거)
  delay(300);
}

void loop() {
  if (!Serial.available()) {
    return;
  }

  String line = Serial.readStringUntil('\n');
  line.trim();
  if (line.length() == 0) {
    return;
  }

  StaticJsonDocument<768> doc;
  DeserializationError err = deserializeJson(doc, line);
  if (err) {
    respondFail("", "parse", String("JSON error: ") + err.c_str());
    return;
  }

  handleLabelJob(doc);
}
