#define BOOT_PIN  25
#define NRST_PIN  27

#define RED_LED   16
#define BLUE_LED  5
#define GREEN_LED 19

#define BUF_SIZE  2

typedef enum {
  STATE_OFF       = 0x30,
  STATE_BOOTMODE  = 0x31,
  STATE_RESET     = 0x32,

  STATE_RED       = 0x33,
  STATE_BLUE      = 0x34,
  STATE_GREEN     = 0x35,
} State;

uint8_t command[BUF_SIZE];
uint8_t idx = 0;

static void printBuffer(uint8_t* buf) {
    for (uint8_t i = 0; i < BUF_SIZE; i++) {
        Serial.print(buf[i], HEX);
        buf[i] = '\0';
    }
    Serial.println();
}

void setup() {
  Serial.begin(115200);
  Serial.println("Master flasher started.");

  pinMode(BOOT_PIN, OUTPUT);
  pinMode(NRST_PIN, OUTPUT);

  pinMode(RED_LED, OUTPUT);
  pinMode(BLUE_LED, OUTPUT);
  pinMode(GREEN_LED, OUTPUT);

  digitalWrite(BOOT_PIN, HIGH);
  digitalWrite(NRST_PIN, HIGH);

  digitalWrite(RED_LED, LOW);
  digitalWrite(BLUE_LED, LOW);
  digitalWrite(GREEN_LED, LOW);
}

void loop() {
  while (Serial.available()) {
    uint8_t byte = Serial.read();

    switch (byte) {
      /* POWER is LOW, BOOT don't care */
      /* Ideally I want to completely cut power here but I canot drive the target from the host so perhaps we should use the RESET line instead. */
      case STATE_OFF:
        digitalWrite(RED_LED, LOW);
        digitalWrite(BLUE_LED, LOW);
        digitalWrite(GREEN_LED, LOW);
        break;

      /* BOOT is LOW, POWER is HIGH */
      case STATE_BOOTMODE:
        digitalWrite(BOOT_PIN, LOW);
        delay(100);
        digitalWrite(NRST_PIN, LOW);
        delay(100);
        digitalWrite(NRST_PIN, HIGH);
        break;

      /* POWER is LOW, BOOT is HIGH, POWER is HIGH - power cycle as reset */
      case STATE_RESET:
        digitalWrite(BOOT_PIN, HIGH);
        delay(100);
        digitalWrite(NRST_PIN, LOW);
        delay(100);
        digitalWrite(NRST_PIN, HIGH);
        break;

      case STATE_RED:
        digitalWrite(RED_LED, HIGH);
        digitalWrite(BLUE_LED, LOW);
        digitalWrite(GREEN_LED, LOW);
        break;
      case STATE_BLUE:
        digitalWrite(RED_LED, LOW);
        digitalWrite(BLUE_LED, HIGH);
        digitalWrite(GREEN_LED, LOW);
        break;
      case STATE_GREEN:
        digitalWrite(RED_LED, LOW);
        digitalWrite(BLUE_LED, LOW);
        digitalWrite(GREEN_LED, HIGH);
        break;

      default:
        break;
    }

    // This is interesting if I want to fill a longer buffer but we will be working with a single byte right now
    // if ((byte == 0x0A) || (idx >= sizeof(command) - 1)) {
    //   printBuffer(command);
    //   idx = 0;
    // } else {
    //   command[idx] = byte;
    //   idx++;
    // }
  }
}
