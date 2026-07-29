// =======================================================================================================
// CHRONOENGINE LEVEL 0: Deterministic Event Engine
// Hardware: Arduino Uno (ATmega328P) + AVR Timer1 ISR
// DSA: O(log N) Min-Heap Priority Queue
// this code is designed to run on Arduino Uno and uses Timer1 to trigger an interrupt every 50 microseconds. It manages tasks using a min-heap priority queue, allowing for deterministic scheduling of tasks based on their execution time. The HeartbeatTask class represents a task that logs telemetry data at specified intervals.
// =======================================================================================================

class Task {
public:
  int id;
  unsigned long execution_time; 
  volatile bool task_completed; 
  volatile unsigned long actual_time;

  Task(int _id) { 
    id = _id; 
    execution_time = 0; 
    task_completed = false;
  }
  
  virtual void hardware_action() = 0; 
  virtual void log_telemetry() = 0; 
};

class HeartbeatTask : public Task {
public:
  unsigned long interval; 
  HeartbeatTask(int _id, unsigned long _interval) : Task(_id) { interval = _interval; }

  void hardware_action() override {
    actual_time = micros(); 
    execution_time = execution_time + interval; 
    task_completed = true; 
  }

  void log_telemetry() override {
    if (task_completed) {
      Serial.print("{\"id\":");
      Serial.print(id);
      Serial.print(",\"expected\":");
      Serial.print(execution_time - interval); 
      Serial.print(",\"actual\":");
      Serial.print(actual_time);
      Serial.println("}");
      task_completed = false; 
    }
  }
};

class TaskQueue {
private:
  Task* heap[10]; 
  int count = 0;

  void heapifyUp(int index) {
    while (index > 0) {
      int parent = (index - 1) / 2;
      if (heap[index]->execution_time < heap[parent]->execution_time) {
        Task* temp = heap[index]; heap[index] = heap[parent]; heap[parent] = temp;
        index = parent;
      } else { break; }
    }
  }

  void heapifyDown(int index) {
    while (true) {
      int left = 2 * index + 1; 
      int right = 2 * index + 2; 
      int smallest = index;
      if (left < count && heap[left]->execution_time < heap[smallest]->execution_time) smallest = left;
      if (right < count && heap[right]->execution_time < heap[smallest]->execution_time) smallest = right;
      if (smallest != index) {
        Task* temp = heap[index]; heap[index] = heap[smallest]; heap[smallest] = temp;
        index = smallest;
      } else { break; }
    }
  }

public:
  void push(Task* task) { 
    if (count >= 10) return; 
    heap[count] = task; 
    heapifyUp(count); 
    count++; 
  }
  
  Task* pop() {
    if (count == 0) return nullptr;
    Task* topTask = heap[0]; 
    heap[0] = heap[count - 1]; 
    count--; 
    heapifyDown(0);
    return topTask;
  }

  Task* peek() { 
    if (count == 0) return nullptr; 
    return heap[0]; 
  }
  
  bool isEmpty() { return count == 0; }
};

TaskQueue engineQueue;
HeartbeatTask task1(1, 1000000UL); 
HeartbeatTask task2(2, 500000UL);  

// Hardware Interrupt Vector triggered every 50 microseconds via AVR Timer1
ISR(TIMER1_COMPA_vect) {
  if (!engineQueue.isEmpty()) {
    Task* nextTask = engineQueue.peek(); 
    if (micros() >= nextTask->execution_time) {
      nextTask->hardware_action(); 
      engineQueue.pop(); 
      engineQueue.push(nextTask); 
    }
  }
}

void setup() {
  Serial.begin(115200); 
  delay(500);
  
  task1.execution_time = micros() + 1000000UL; 
  task2.execution_time = micros() + 500000UL;  
  engineQueue.push(&task1);
  engineQueue.push(&task2);

  // Raw AVR Hardware Configuration for Timer1
  noInterrupts(); 
  TCCR1A = 0; 
  TCCR1B = 0; 
  TCNT1  = 0; 
  OCR1A = 99; // 50 microsecond match target at 2MHz timer frequency
  TCCR1B |= (1 << WGM12);  
  TCCR1B |= (1 << CS11);   
  TIMSK1 |= (1 << OCIE1A); 
  interrupts(); 
}

void loop() {
  task1.log_telemetry();
  task2.log_telemetry();
}