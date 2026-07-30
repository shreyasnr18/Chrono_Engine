/*
  ChronoEngine Telemetry Hardware Node
  Baud Rate: 115200
*/

unsigned long sequence_id = 0;

void setup() {
  Serial.begin(115200);
  pinMode(A0, INPUT); // Voltage sensor pin
  pinMode(A1, INPUT); // Temperature sensor pin
}

void loop() {
  sequence_id++;

  // Read analog pins
  int raw_v = analogRead(A0);
  int raw_t = analogRead(A1);

  // Map 0-1023 ADC reading to 0-300V line voltage scale
  float voltage = (raw_v / 1023.0) * 300.0;
  
  // Map 0-1023 ADC reading to 20-100 C temperature scale
  float temperature = 25.0 + ((raw_t / 1023.0) * 75.0);

  // Output JSON payload string over Serial
  Serial.print("{\"sequence_id\":");
  Serial.print(sequence_id);
  Serial.print(",\"timestamp\":");
  Serial.print(millis() / 1000.0);
  Serial.print(",\"voltage\":");
  Serial.print(voltage, 2);
  Serial.print(",\"temperature_c\":");
  Serial.print(temperature, 2);
  Serial.print(",\"is_simulated_anomaly\":false}");
  Serial.println();

  delay(1000); // 1Hz sampling rate
}