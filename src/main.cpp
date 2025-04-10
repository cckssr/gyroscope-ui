#include <Arduino.h>
#include <SoftwareSerial.h>

/**
 * Hardware Random Number Generator (HRNG) for Arduino
 *
 * This program measures the time intervals between interrupts triggered by
 * an external random process (such as a radioactive decay). These measured time
 * intervals are used as a source for true random numbers.
 */

// Global constants
const int interruptPin = 2;               // Pin number for the interrupt source
const unsigned long debounceTime = 10;    // Debounce time in microseconds to filter noise
const bool debug = true;                 // Debug mode toggle
const int MAX_LENGTH = 64;        // Maximum allowed length of a message line

// Variable to store the time difference between consecutive pulses
volatile unsigned long lastPulseTime = 0; // Timestamp of the last pulse (volatile because it's accessed from interrupt)
volatile bool firstPulseOccurred = false; // Flag to identify the first pulse event
volatile unsigned long currentDelta = 0; // Updated in the interrupt handler
volatile bool measurementInProgress = false; // Flag to indicate if a measurement is in progress
volatile char message[MAX_LENGTH + 1];     // Buffer (+1 for null terminator)
volatile int index = 0;                    // Current position in buffer

/**
 * Interrupt handler function
 * Called when a RISING edge is detected on the interrupt pin.
 * Calculates the time between consecutive pulses and stores it in currentDelta.
 */
void handleInterrupt()
{
    unsigned long currentTime = micros(); // Current time in microseconds

    // If this is not the first pulse, and the debounce time has passed, calculate delta
    currentDelta = currentTime - lastPulseTime;
    if (firstPulseOccurred && (currentDelta > debounceTime))
    {
        // Print from the interrupt is generally discouraged, so store the value for loop processing.
        lastPulseTime = currentTime; // Update the time of the last pulse
    }
    else if (!firstPulseOccurred)
    {
        // This is the first pulse, so just record the time.
        lastPulseTime = currentTime; // Store the time of the first pulse
        firstPulseOccurred = true;   // Set the flag indicating the first pulse has occurred
    }
}

/**
 * @brief Checks if a string is a valid integer
 *
 * @param str The string to check
 * @return true if the string is a valid integer, false otherwise
 */
bool isInteger(const char *str)
{
    if (str[0] == '-' && strlen(str) > 1)
    {
        str++; // Allow negative numbers, skip the minus sign
    }

    for (int i = 0; str[i] != '\0'; i++)
    {
        if (str[i] < '0' || str[i] > '9')
        {
            return false; // Invalid character
        }
    }
    return true; // Valid number
}

/**
 * @brief Validates a received message according to specific format rules
 *
 * This function checks if the message contains only valid integers separated by commas.
 *
 * @param msg The message to validate
 * @return true if the message is valid, false otherwise
 */
bool validateMessage(volatile char *msg)
{
    int numberCount = 0; // Number of integers found
    char temp[10];       // Buffer for current number
    int tempIndex = 0;   // Index for temporary number
    bool isValid = true;

    if (debug)
    {
        Serial.print("Complete message is ");
        Serial.println((const char*)msg);
    }

    // Parse the message character by character
    for (int i = 0; msg[i] != '\0'; i++)
    {
        char currentChar = msg[i];
        if (debug)
        {
            Serial.print("Character " + String(i) + " is: ");
            Serial.println(currentChar);
        }

        if (currentChar == 0x0D)
        {
            if (debug)
                Serial.println("\t Character is CR (ignored)");
            continue; // Skip CR character
        }

        if ((currentChar >= '0' && currentChar <= '9') || currentChar == '-')
        {
            // Valid digit or minus sign
            if (debug)
                Serial.println("\t Character is between '0' and '9' or '-'");
            temp[tempIndex++] = currentChar;
        }
        else if (currentChar == ',')
        {
            if (debug)
                Serial.println("\t Character is comma");

            // Check the current number when a comma is encountered
            if (tempIndex == 0)
            {
                if (debug)
                    Serial.println("\t Number is empty");
                isValid = false; // Empty numbers are invalid
                break;
            }
            temp[tempIndex] = '\0'; // Add null terminator
            if (!isInteger(temp))
            {
                if (debug)
                    Serial.println("\t Not a valid integer");
                isValid = false; // Invalid number
                break;
            }
            tempIndex = 0; // Reset temporary number
            numberCount++; // Increment number counter
        }
        else
        {
            if (debug)
            {
                Serial.println("\t Character is neither a digit nor a comma");
                Serial.print("\t Character is: ");
                Serial.println(currentChar, HEX);
            }
            isValid = false; // Invalid character
            break;
        }
    }

    // Check the last number and ensure proper count
    if (tempIndex > 0)
    {                           // Process the last number
        temp[tempIndex] = '\0'; // Add null terminator
        if (!isInteger(temp))
        {
            isValid = false;
        }
        else
        {
            numberCount++;
        }
    }

    return (isValid && numberCount == 6); // Valid if all checks passed
}

void receiveMessage()
{
    char receivedChar = Serial1.read();

        // Check for end of message (newline)
        if (receivedChar == '\n')
        {
            message[index] = '\0'; // Add null terminator

            // Validate message
            if (validateMessage(message))
            {
                if (debug)
                {
                    Serial.print("Message is valid: ");
                }
                Serial.println((char*)message);
            }
            else
            {
                Serial.println("invalid");
            }

            // Reset buffer
            index = 0;
        }
        // Check for buffer overflow
        else if (index >= MAX_LENGTH - 1)
        {
            if (debug)
            {
                Serial.println("Error: Message too long, discarded.");
            }
            Serial.println("invalid");
            index = 0; // Reset buffer
        }
        // Store character in buffer
        else
        {
            message[index++] = receivedChar;
        }
    
}

void sendMessage()
{
    // Send commands to the external device
    String command = Serial.readStringUntil('\n');
    command.trim(); // Remove whitespace and control characters
    if (command.length() > 0)
    {
        if (debug)
        {
            Serial.print("Sending: ");
            Serial.println(command);
        }
        Serial1.println(command); // Send command via Serial1

        if (debug)
        {
            Serial.println("Successfully sent.");
        }
    }
    // Handle measurement stop
    if (command == "s0"){
        measurementInProgress = false; // Stop measurement
        if (debug)
        {
            Serial.println("Measurement stopped.");
        }
    }
    if (command == "s1")
    {
        measurementInProgress = true; // Start measurement
        if (debug)
        {
            Serial.println("Measurement started.");
        }
    }
}

void handleTimer(unsigned long deltaToPrint = 0)
{
    // Safely read the shared variable
    noInterrupts(); // Disable interrupts for atomic access to shared variables
    if (currentDelta != 0)
    {
        deltaToPrint = currentDelta; // Copy the value to a local variable
        currentDelta = 0;            // Reset currentDelta to ensure we don't print the same value twice
    }
    interrupts(); // Re-enable interrupts

    if (deltaToPrint != 0)
    {
        Serial.println(deltaToPrint, DEC); // Print the value over serial
        deltaToPrint = 0;                  // Reset the local variable
    }
}

/**
 * Setup function
 * Runs once when the Arduino starts.
 * Initializes serial communication and configures the interrupt.
 */
void setup()
{
    Serial.begin(115200);         // Initialize serial communication at 115200 baud
    Serial1.begin(9600);          // Initialize second serial communication with GM-Counter
    pinMode(interruptPin, INPUT); // Configure the interrupt pin as an input
    // Attach interrupt to the pin, using RISING edge detection
    attachInterrupt(digitalPinToInterrupt(interruptPin), handleInterrupt, RISING);
}

/**
 * Main loop
 * Runs continuously after setup() completes.
 * Reads the data stored by the interrupt handler and sends it over the serial interface.
 */
void loop()
{
    if (measurementInProgress)
    {
        // If measurement is in progress, handle the timer
        handleTimer();
        
        // Check if measurement is stopped
        if (Serial.available() > 0){
            sendMessage();
        }
    }
    else
    {
        // Serial.println("test");
        // If no measurement is in progress, check for incoming messages
        if (Serial1.available() > 0)
        {
            receiveMessage();
        }
        if (Serial.available() > 0)
        {
            sendMessage();
        }
    }
}