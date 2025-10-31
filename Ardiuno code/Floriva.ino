#include "RichShieldDHT.h"
#include "RichShieldTM1637.h"
#include "RichShieldLED.h"
#include "RichShieldVoltageSensor.h"

// --- TM1637 display ---
#define CLK 10
#define DIO 11
TM1637 disp(CLK, DIO);

// --- LED pins ---
#define LED1 7
#define LED2 6
#define LED3 5
#define LED4 4
LED led(LED1, LED2, LED3, LED4);

// --- LDR & Potentiometer ---
#define LDR_PIN A1       // Light sensor pin
#define POT_PIN A0       // Potentiometer pin

// --- Voltage sensor ---
#define VOL_SENSOR_PIN A3
VoltageSensor voltage(VOL_SENSOR_PIN);

// --- DHT ---
DHT dht;

// --- Timing for display ---
unsigned long lastUpdate = 0;
int displayMode = 0; // 0=temp, 1=hum, 2=voltage

void setup() {
  Serial.begin(9600);
  disp.init();
  dht.begin();
  pinMode(LDR_PIN, INPUT);
  pinMode(POT_PIN, INPUT);

  // Ensure LED pins are set
  pinMode(LED1, OUTPUT);
  pinMode(LED2, OUTPUT);
  pinMode(LED3, OUTPUT);
  pinMode(LED4, OUTPUT);
}

void loop() {
  unsigned long currentMillis = millis();

  if (currentMillis - lastUpdate > 5000) {
    lastUpdate = currentMillis;

    if (displayMode == 0) { // Temperature
      float t = dht.readTemperature();
      if (isnan(t)) displayError();
      else displayTemperature((int8_t)t);
      displayMode = 1;
    }
    else if (displayMode == 1) { // Humidity
      float h = dht.readHumidity();
      if (isnan(h)) displayError();
      else displayHumidity((int8_t)h);
      displayMode = 2;
    }
    else if (displayMode == 2) { // Voltage
      float v = voltage.read();
      if (!isnan(v)) displayVoltage(v);
      else displayError();
      displayMode = 0;
    }
  }

  // --- Read sensors ---
  int LDRValue = analogRead(LDR_PIN);
  int PotValue = analogRead(POT_PIN);

  // --- Determine light status and control LEDs ---
  String lightStatus;
  if (LDRValue < PotValue) {
    lightStatus = "ON";
    led.on(1); led.on(2); led.on(3); led.on(4);
  } else {
    lightStatus = "OFF";
    led.off(1); led.off(2); led.off(3); led.off(4);
  }

  // --- Read DHT & Voltage ---
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  float volt = voltage.read();

  // --- Send CSV data for database ---
  if (!isnan(temperature) && !isnan(humidity) && !isnan(volt)) {
    Serial.print(temperature); Serial.print(",");
    Serial.print(humidity); Serial.print(",");
    Serial.print(volt); Serial.print(",");
    Serial.println(lightStatus); // for DB
  }

  delay(1000); 
}

// --- Display functions ---
void displayTemperature(int8_t temperature) {
  int8_t temp[4];
  if (temperature < 0) {
    temp[0] = INDEX_NEGATIVE_SIGN;
    temperature = abs(temperature);
  } else if (temperature < 100) temp[0] = INDEX_BLANK;
  else temp[0] = temperature / 100;

  temperature %= 100;
  temp[1] = temperature / 10;
  temp[2] = temperature % 10;
  temp[3] = 12; // 'C'
  disp.display(temp);
}

void displayHumidity(int8_t humi) {
  int8_t temp[4];
  if (humi < 100) temp[0] = INDEX_BLANK;
  else temp[0] = humi / 100;
  humi %= 100;
  temp[1] = humi / 10;
  temp[2] = humi % 10;
  temp[3] = 18; // 'H'
  disp.display(temp);
}

void displayVoltage(float voltageValue) {
  int displayVal = (int)(voltageValue * 10);
  int8_t temp[4];
  temp[0] = displayVal / 1000;
  displayVal %= 1000;
  temp[1] = displayVal / 100;
  displayVal %= 100;
  temp[2] = displayVal / 10;
  temp[3] = displayVal % 10;
  disp.display(temp);
}

void displayError() {
  disp.display(3, 14); // 'E'
}
