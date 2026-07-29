// ==========================================
// CHRONOENGINE LEVEL 2: Bi-Directional DSP Pipeline
// Features: O(1) Ring Buffer + Serial Command Listener for LED Feedback
// ==========================================

const int LED_PIN = 13; // Built-in Arduino LED for hardware feedback
char incomingCommand = 'N'; // Default state: Normal

class ISensor {
public:
  virtual ~ISensor() {}
  virtual float read_raw() = 0; 
};

class AnalogAntennaSensor : public ISensor {
private:
  uint8_t pin;
public:
  AnalogAntennaSensor(uint8_t target_pin) {
    pin = target_pin;
    pinMode(pin, INPUT);
    pinMode(LED_PIN, OUTPUT);
  }
  float read_raw() override {
    return (float)analogRead(pin);
  }
};

template <typename T, int Capacity>
class RingBuffer {
private:
  T buffer[Capacity];
  int head, tail, size;
  T sum;
public:
  RingBuffer() {
    head = 0; tail = 0; size = 0; sum = 0;
    for(int i = 0; i < Capacity; i++) buffer[i] = 0;
  }
  void push(T value) {
    if (size < Capacity) {
      sum += value;
      buffer[tail] = value;
      tail = (tail + 1) % Capacity;
      size++;
    } else {
      sum -= buffer[head];
      sum += value;
      buffer[head] = value;
      head = (head + 1) % Capacity;
      buffer[tail] = value;
      tail = (tail + 1) % Capacity;
    }
  }
  float get_average() {
    if (size == 0) return 0.0f;
    return (float)sum / (float)size;
  }
};

AnalogAntennaSensor mySensor(A0);
RingBuffer<float, 10> dspFilter; 
unsigned long sample_counter = 0;

void setup() {
  Serial.begin(115200);
  delay(500);
}

void loop() {
  // 1. Check if Python sent a bi-directional feedback command back to the hardware
  if (Serial.available() > 0) {
    incomingCommand = Serial.read();
  }

  // 2. Hardware actuation based on command feedback from Python analytics
  if (incomingCommand == 'A') {
    // Fast blink warning state if anomaly/high error detected
    digitalWrite(LED_PIN, HIGH);
    delay(50);
    digitalWrite(LED_PIN, LOW);
    delay(50);
  } else {
    // Stable slow pulse for normal state
    digitalWrite(LED_PIN, HIGH);
    delay(200);
    digitalWrite(LED_PIN, LOW);
    delay(200);
  }

  float raw = mySensor.read_raw();
  dspFilter.push(raw);
  float filtered = dspFilter.get_average();
  float variance = raw - filtered;

  sample_counter++;
  
  // Datasheet Telemetry Frame
  Serial.print("{\"ts\":");
  Serial.print(millis());
  Serial.print(",\"id\":");
  Serial.print(sample_counter);
  Serial.print(",\"raw\":");
  Serial.print(raw, 2);
  Serial.print(",\"filt\":");
  Serial.print(filtered, 2);
  Serial.print(",\"var\":");
  Serial.print(variance, 2);
  Serial.println("}");
}