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
  // Using USB cable for Raspberry Pi ROS 2
  Serial.begin(115200); 
  
  Serial.println("ESP32 Calibrated PWM Driver Ready.");

  #if ESP_ARDUINO_VERSION_MAJOR >= 3
    // Modern ESP32 Core v3+ Hardware PWM
    ledcAttach(FL_A, 5000, 8); ledcAttach(FL_B, 5000, 8);
    ledcAttach(RL_A, 5000, 8); ledcAttach(RL_B, 5000, 8);
    ledcAttach(FR_A, 5000, 8); ledcAttach(FR_B, 5000, 8);
    ledcAttach(RR_A, 5000, 8); ledcAttach(RR_B, 5000, 8);
  #else
    // Legacy ESP32 Core v2 Hardware PWM Check
    ledcSetup(0, 5000, 8); ledcAttachPin(FL_A, 0);
    ledcSetup(1, 5000, 8); ledcAttachPin(FL_B, 1);
    ledcSetup(2, 5000, 8); ledcAttachPin(RL_A, 2);
    ledcSetup(3, 5000, 8); ledcAttachPin(RL_B, 3);
    ledcSetup(4, 5000, 8); ledcAttachPin(FR_A, 4);
    ledcSetup(5, 5000, 8); ledcAttachPin(FR_B, 5);
    ledcSetup(6, 5000, 8); ledcAttachPin(RR_A, 6);
    ledcSetup(7, 5000, 8); ledcAttachPin(RR_B, 7);
  #endif

  // Set all to 0
  stopMotors();
  inputString.reserve(50);
}

void loop() {
  // Read Serial data from Raspberry Pi over USB 
  while (Serial.available()) {
    char inChar = (char)Serial.read();
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

// --- Helper to support V2 / V3 API seamlessly ---
void safePWM(int pin, int channel, int duty) {
  #if ESP_ARDUINO_VERSION_MAJOR >= 3
    ledcWrite(pin, duty);
  #else
    ledcWrite(channel, duty);
  #endif
}

void applyPWM(int left_pwm, int right_pwm) {
  // Restore all calibration logic and proportional speeds!
  int pwm_fl = constrain(left_pwm * CALIB_FL, -255, 255);
  int pwm_rl = constrain(left_pwm * CALIB_RL, -255, 255);
  int pwm_fr = constrain(right_pwm * CALIB_FR, -255, 255);
  int pwm_rr = constrain(right_pwm * CALIB_RR, -255, 255);

  // --- Front Left ---
  if (pwm_fl >= 0) {
    safePWM(FL_A, 0, pwm_fl); safePWM(FL_B, 1, 0);
  } else {
    safePWM(FL_A, 0, 0);      safePWM(FL_B, 1, -pwm_fl);
  }

  // --- Rear Left ---
  if (pwm_rl >= 0) {
    safePWM(RL_A, 2, pwm_rl); safePWM(RL_B, 3, 0);
  } else {
    safePWM(RL_A, 2, 0);      safePWM(RL_B, 3, -pwm_rl);
  }

  // --- Front Right ---
  if (pwm_fr >= 0) {
    safePWM(FR_A, 4, pwm_fr); safePWM(FR_B, 5, 0);
  } else {
    safePWM(FR_A, 4, 0);      safePWM(FR_B, 5, -pwm_fr);
  }

  // --- Rear Right ---
  if (pwm_rr >= 0) {
    safePWM(RR_A, 6, pwm_rr); safePWM(RR_B, 7, 0);
  } else {
    safePWM(RR_A, 6, 0);      safePWM(RR_B, 7, -pwm_rr);
  }
}

void stopMotors() {
  safePWM(FL_A, 0, 0); safePWM(FL_B, 1, 0);
  safePWM(RL_A, 2, 0); safePWM(RL_B, 3, 0);
  safePWM(FR_A, 4, 0); safePWM(FR_B, 5, 0);
  safePWM(RR_A, 6, 0); safePWM(RR_B, 7, 0);
}
