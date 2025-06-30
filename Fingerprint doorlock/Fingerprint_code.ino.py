#include <Adafruit_Fingerprint.h>
#include <Keypad.h>

// ----------------------
// Fingerprint Setup
// ----------------------
#define mySerial Serial1 // Using hardware serial port Serial1 (pins 18 RX, 19 TX)
Adafruit_Fingerprint finger(&mySerial);

// ----------------------
// Keypad Setup
// ----------------------
const byte ROWS = 4;
const byte COLS = 4;
char keys[ROWS][COLS] = {
    {'1', '2', '3', 'A'},
    {'4', '5', '6', 'B'},
    {'7', '8', '9', 'C'},
    {'*', '0', '#', 'D'}};
byte rowPins[ROWS] = {4, 5, 6, 7};
byte colPins[COLS] = {8, 9, 10, 11};
Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

// ----------------------
// Relay and PIR Setup
// ----------------------
#define RELAY_PIN 12
#define PIR_PIN 3 // Reverted PIR pin back to 13
unsigned long lastPIRTrigger = 0;
const unsigned long pirCooldown = 10000; // 10 seconds

// ----------------------
// Admin Password
// ----------------------
const String adminPassword = "1234"; // Change this

// ----------------------
// Setup
// ----------------------
void setup()
{
    Serial.begin(9600);
    mySerial.begin(57600); // Fingerprint sensor serial communication

    pinMode(RELAY_PIN, OUTPUT);
    pinMode(PIR_PIN, INPUT);
    digitalWrite(RELAY_PIN, HIGH); // Locked initially

    finger.begin(57600);
    if (finger.verifyPassword())
    {
        Serial.println("Fingerprint sensor ready.");
    }
    else
    {
        Serial.println("Fingerprint sensor not found.");
        while (1)
            ;
    }

    finger.getTemplateCount();
    Serial.print("Sensor has ");
    Serial.print(finger.templateCount);
    Serial.println(" templates.");
    Serial.println("Press A to enroll (password protected).");
}

// ----------------------
// Main Loop
// ----------------------
void loop()
{
    char key = keypad.getKey();
    if (key == 'A')
    {
        if (checkPassword())
        {
            enrollFingerprint();
        }
        else
        {
            Serial.println("Incorrect password. Enrollment denied.");
        }
    }

    scanForFingerprint(); // External side
                          // checkPIR();           // Inside motion
}

// ----------------------
// Fingerprint Unlock
// ----------------------
void scanForFingerprint()
{
    if (finger.getImage() != FINGERPRINT_OK)
        return;
    if (finger.image2Tz() != FINGERPRINT_OK)
        return;

    if (finger.fingerSearch() == FINGERPRINT_OK)
    {
        Serial.print("Access Granted! ID: ");
        Serial.println(finger.fingerID);
        unlockDoor();
        while (finger.getImage() != FINGERPRINT_NOFINGER)
            ;
        delay(1000);
    }
    else
    {
        Serial.println("Access Denied");
        delay(1000);
    }
}

// ----------------------
// PIR Motion Auto-Unlock
// ----------------------
// void checkPIR() {
//   int pirState = digitalRead(PIR_PIN);

//   // If PIR sensor is unplugged (pin state is floating, unreliable)
//   if (pirState != LOW && pirState != HIGH) {
//     Serial.println("PIR sensor is disconnected or malfunctioning.");
//     return;  // Exit the function early, no action taken
//   }

//   // If motion is detected (pirState is HIGH)
//   if (pirState == HIGH) {
//     unsigned long currentMillis = millis();
//     if (currentMillis - lastPIRTrigger > pirCooldown) {  // Wait for cooldown period
//       Serial.println("Motion detected inside — auto-unlock");
//       unlockDoor();
//       lastPIRTrigger = currentMillis;
//     }
//   }
// }

// ----------------------
// Unlock Door (Relay Active LOW)
// ----------------------
void unlockDoor()
{
    Serial.println("Unlocking...");
    digitalWrite(RELAY_PIN, LOW);  // Relay ON → Unlock
    delay(5000);                   // Door stays unlocked for 5 seconds
    digitalWrite(RELAY_PIN, HIGH); // Relay OFF → Lock
    Serial.println("Locked");
}

// ----------------------
// Enroll Fingerprint
// ----------------------
void enrollFingerprint()
{
    int id = finger.templateCount + 1;
    Serial.print("Enrolling ID #");
    Serial.println(id);

    Serial.println("Place finger...");
    while (finger.getImage() != FINGERPRINT_OK)
        ;
    if (finger.image2Tz(1) != FINGERPRINT_OK)
    {
        Serial.println("Image conversion failed.");
        return;
    }

    Serial.println("Remove finger...");
    delay(2000);
    while (finger.getImage() != FINGERPRINT_NOFINGER)
        ;

    Serial.println("Place same finger again...");
    while (finger.getImage() != FINGERPRINT_OK)
        ;
    if (finger.image2Tz(2) != FINGERPRINT_OK)
    {
        Serial.println("Second image conversion failed.");
        return;
    }

    if (finger.createModel() != FINGERPRINT_OK)
    {
        Serial.println("Fingerprint match failed.");
        return;
    }

    if (finger.storeModel(id) == FINGERPRINT_OK)
    {
        Serial.println("Fingerprint enrolled successfully!");
    }
    else
    {
        Serial.println("Failed to store fingerprint.");
    }
}

// ----------------------
// Password Entry via Keypad
// ----------------------
bool checkPassword()
{
    Serial.println("Enter 4-digit admin password:");

    String input = "";
    unsigned long startTime = millis();

    while (input.length() < 4 && millis() - startTime < 10000)
    {
        char key = keypad.getKey();
        if (key)
        {
            if (key == '#')
            {
                Serial.println("\nCanceled.");
                return false;
            }
            if (key >= '0' && key <= '9')
            {
                input += key;
                Serial.print("*"); // Optional masking
            }
        }
    }

    Serial.println();
    return input == adminPassword;
}