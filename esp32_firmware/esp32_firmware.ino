#include <Arduino.h>

// --- MOTOR CALIBRATION MULTIPLIERS ---
// 1.0 = 100% normal speed. 
// If a motor is physically slower than the rest, increase its multiplier to mathematically boost it (e.g. 1.25)
float CALIB_FL = 1.0;  // Front-Left
float CALIB_RL = 1.0;  // Rear-Left
float CALIB_FR = 1.0;  // Front-Right
float CALIB_RR = 1.0;  // Rear-Right

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

// Serial buffer
String inputString = "";
bool stringComplete = false;

void setup() {
  // Serial to PC/Monitor for debugging
  Serial.begin(115200); 
  
  // Serial2 for Raspberry Pi ROS 2
  // Using pins 16 (RX) and 17 (TX). 
  // If connecting via USB cable instead of pins, change all 'Serial2' below to 'Serial'!
  Serial2.begin(115200, SERIAL_8N1, 16, 17); 
  
  Serial.println("ESP32 Calibrated PWM Driver Ready.");

  pinMode(FL_A, OUTPUT); pinMode(FL_B, OUTPUT);
  pinMode(RL_A, OUTPUT); pinMode(RL_B, OUTPUT);
  pinMode(FR_A, OUTPUT); pinMode(FR_B, OUTPUT);
  pinMode(RR_A, OUTPUT); pinMode(RR_B, OUTPUT);

  // Set all to 0
  stopMotors();
  inputString.reserve(50);
}

void loop() {
  // Read Serial data from Raspberry Pi 
  while (Serial2.available()) {
    char inChar = (char)Serial2.read();
    inputString += inChar;
    if (inChar == '\n') {
      stringComplete = true;
    }
  }

  // Parse command: L<int>R<int>\n  (e.g., L150R-200)
  if (stringComplete) {
    if (inputString.startsWith("L")) {
      int rIndex = inputString.indexOf('R');
      if (rIndex > 0) {
        String lString = inputString.substring(1, rIndex);
        String rString = inputString.substring(rIndex + 1);
        
        int left_pwm = lString.toInt();
        int right_pwm = rString.toInt();
        
        applyPWM(left_pwm, right_pwm);
      }
    }
    
    // Clear for next transmission
    inputString = "";
    stringComplete = false;
  }
}

void applyPWM(int left_pwm, int right_pwm) {
  // Apply individual motor calibration scalars
  int pwm_fl = constrain(left_pwm * CALIB_FL, -255, 255);
  int pwm_rl = constrain(left_pwm * CALIB_RL, -255, 255);
  int pwm_fr = constrain(right_pwm * CALIB_FR, -255, 255);
  int pwm_rr = constrain(right_pwm * CALIB_RR, -255, 255);

  // --- Front Left ---
  if (pwm_fl >= 0) {
    analogWrite(FL_A, pwm_fl); analogWrite(FL_B, 0);
  } else {
    analogWrite(FL_A, 0);      analogWrite(FL_B, -pwm_fl);
  }

  // --- Rear Left ---
  if (pwm_rl >= 0) {
    analogWrite(RL_A, pwm_rl); analogWrite(RL_B, 0);
  } else {
    analogWrite(RL_A, 0);      analogWrite(RL_B, -pwm_rl);
  }

  // --- Front Right ---
  if (pwm_fr >= 0) {
    analogWrite(FR_A, pwm_fr); analogWrite(FR_B, 0);
  } else {
    analogWrite(FR_A, 0);      analogWrite(FR_B, -pwm_fr);
  }

  // --- Rear Right ---
  if (pwm_rr >= 0) {
    analogWrite(RR_A, pwm_rr); analogWrite(RR_B, 0);
  } else {
    analogWrite(RR_A, 0);      analogWrite(RR_B, -pwm_rr);
  }
}

void stopMotors() {
  analogWrite(FL_A, 0); analogWrite(FL_B, 0);
  analogWrite(RL_A, 0); analogWrite(RL_B, 0);
  analogWrite(FR_A, 0); analogWrite(FR_B, 0);
  analogWrite(RR_A, 0); analogWrite(RR_B, 0);
}
