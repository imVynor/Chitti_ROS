#include <Arduino.h>

// --- Driver 1: LEFT MOTORS ---
#define FL_A 26  // Front-Left Forward
#define FL_B 27  // Front-Left Backward
#define RL_A 14  // Rear-Left Forward
#define RL_B 12  // Rear-Left Backward

// --- Driver 2: RIGHT MOTORS ---
#define FR_A 33  // Front-Right Forward
#define FR_B 32  // Front-Right Backward
#define RR_A 25  // Rear-Right Forward
#define RR_B 4   // Rear-Right Backward

// Dedicated speed for Binary Testing
int motorSpeed = 200; 

void setup() {
  Serial.begin(115200); 
  
  // Use Serial2 if wired via Pi GPIO Pins. 
  // Change to Serial if plugged into Pi via USB!
  Serial2.begin(9600, SERIAL_8N1, 16, 17); 
  Serial.println("ESP32 Binary Logic Mode Ready.");

  pinMode(FL_A, OUTPUT); pinMode(FL_B, OUTPUT);
  pinMode(RL_A, OUTPUT); pinMode(RL_B, OUTPUT);
  pinMode(FR_A, OUTPUT); pinMode(FR_B, OUTPUT);
  pinMode(RR_A, OUTPUT); pinMode(RR_B, OUTPUT);

  stopMotors();
}

void loop() {
  if (Serial2.available() > 0) {
    char command = Serial2.read();
    Serial.print("Received Command: ");
    Serial.println(command);

    switch (command) {
      case 'F': case 'f': moveForward(); break;
      case 'B': case 'b': moveBackward(); break;
      case 'L': case 'l': turnLeft(); break;
      case 'R': case 'r': turnRight(); break;
      case 'S': case 's': stopMotors(); break;
    }
  }
}

// --- Movement Logic ---

void moveForward() {
  // All 'A' pins get speed, 'B' pins get 0
  analogWrite(FL_A, motorSpeed); analogWrite(FL_B, 0);
  analogWrite(RL_A, motorSpeed); analogWrite(RL_B, 0);
  analogWrite(FR_A, motorSpeed); analogWrite(FR_B, 0);
  analogWrite(RR_A, motorSpeed); analogWrite(RR_B, 0);
}

void moveBackward() {
  // All 'B' pins get speed, 'A' pins get 0
  analogWrite(FL_A, 0); analogWrite(FL_B, motorSpeed);
  analogWrite(RL_A, 0); analogWrite(RL_B, motorSpeed);
  analogWrite(FR_A, 0); analogWrite(FR_B, motorSpeed);
  analogWrite(RR_A, 0); analogWrite(RR_B, motorSpeed);
}

void turnLeft() {
  // Left backward, Right forward
  analogWrite(FL_A, 0); analogWrite(FL_B, motorSpeed);
  analogWrite(RL_A, 0); analogWrite(RL_B, motorSpeed);
  analogWrite(FR_A, motorSpeed); analogWrite(FR_B, 0);
  analogWrite(RR_A, motorSpeed); analogWrite(RR_B, 0);
}

void turnRight() {
  // Left forward, Right backward
  analogWrite(FL_A, motorSpeed); analogWrite(FL_B, 0);
  analogWrite(RL_A, motorSpeed); analogWrite(RL_B, 0);
  analogWrite(FR_A, 0); analogWrite(FR_B, motorSpeed);
  analogWrite(RR_A, 0); analogWrite(RR_B, motorSpeed);
}

void stopMotors() {
  analogWrite(FL_A, 0); analogWrite(FL_B, 0);
  analogWrite(RL_A, 0); analogWrite(RL_B, 0);
  analogWrite(FR_A, 0); analogWrite(FR_B, 0);
  analogWrite(RR_A, 0); analogWrite(RR_B, 0);
}
