#include <Arduino.h>
#include <SoftwareSerial.h>
#include "serial_com.h"

/**
 * Hardware Random Number Generator (HRNG) for Arduino
 *
 * This program measures the time intervals between interrupts triggered by
 * an external random process (such as a radioactive decay). These measured time
 * intervals are used as a source for true random numbers.
 */

// Device constants
const char *OPENBIS_CODE = "TEST"; // OpenBIS code for the device
// Global constants
const int INTERRUPT_PIN = 2;            // Pin number for the interrupt source
const unsigned long DEBOUNCE_TIME = 10; // Debounce time in microseconds to filter noise
const bool DEBUG = false;               // Debug mode toggle
const int MAX_LENGTH = 64;              // Maximum allowed length of a message line
const bool USE_BUFFER = false;          // Flag to use a buffer for incoming messages
const int BUFFER_SIZE = 50;             // Size of the buffer for incoming messages

// Variable to store the time difference between consecutive pulses
volatile unsigned long lastPulseTime = 0;    // Timestamp of the last pulse (volatile because it's accessed from interrupt)
volatile bool firstPulseOccurred = false;    // Flag to identify the first pulse event
volatile uint32_t currentDelta = 0;          // Updated in the interrupt handler
volatile bool measurementInProgress = false; // Flag to indicate if a measurement is in progress
volatile char message[MAX_LENGTH + 1];       // Buffer (+1 for null terminator)
volatile int index = 0;                      // Current position in buffer
volatile unsigned long buffer[BUFFER_SIZE];  // Buffer for storing incoming messages
volatile int bufferIndex = 0;                // Current position in the buffer
volatile bool bufferFull = false;            // Flag to indicate if the buffer is full

/**
 * Interrupt handler function
 * Called when a RISING edge is detected on the interrupt pin.
 * Calculates the time between consecutive pulses and stores it in currentDelta.
 */
void handleInterrupt()
{
    unsigned long currentTime = micros(); // Current time in microseconds

    if (firstPulseOccurred)
    {
        // Calculate the time difference between consecutive pulses
        currentDelta = currentTime - lastPulseTime;

        if (currentDelta > DEBOUNCE_TIME)
        {
            // Save the current delta to the buffer
            if (USE_BUFFER)
            {
                buffer[bufferIndex] = currentDelta;
                bufferIndex++;
                if (bufferIndex >= BUFFER_SIZE)
                {
                    bufferFull = true; // Set the flag indicating the buffer is full
                    bufferIndex = 0;   // Reset the index to start overwriting old values
                }
            }

            // Always update lastPulseTime for the next delta calculation
            lastPulseTime = currentTime;
        }
        else
        {
            // Delta is too small (debounce), don't update anything
            currentDelta = 0;
        }
    }
    else
    {
        // This is the first pulse, so just record the time.
        lastPulseTime = currentTime; // Store the time of the first pulse
        firstPulseOccurred = true;   // Set the flag indicating the first pulse has occurred
        currentDelta = 0;            // No delta for the first pulse
    }
}

void sendByteValue(u_int32_t value)
{
    // Send pure binary data without any text mixing
    Serial.write(0xAA);                            // Start byte
    Serial.write((uint8_t)(value & 0xFF));         // Byte 0 (LSB)
    Serial.write((uint8_t)((value >> 8) & 0xFF));  // Byte 1
    Serial.write((uint8_t)((value >> 16) & 0xFF)); // Byte 2
    Serial.write((uint8_t)((value >> 24) & 0xFF)); // Byte 3 (MSB)
    Serial.write(0x55);                            // End byte for packet validation
}

void debugByteValue(u_int32_t value)
{
    if (DEBUG)
    {
        // Use Serial1 for debug to avoid mixing with binary data on Serial
        Serial1.print("DEBUG - Sent value: ");
        Serial1.print(value, DEC);
        Serial1.print(" (0x");
        Serial1.print(value, HEX);
        Serial1.println(")");
    }
}

void handleTimer(u_int32_t deltaToPrint = 0)
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
        sendByteValue(deltaToPrint);  // Send the value as pure binary data
        debugByteValue(deltaToPrint); // Optional debug output via Serial1
    }
}

/**
 * Setup function
 * Runs once when the Arduino starts.
 * Initializes serial communication and configures the interrupt.
 */
void setup()
{
    Serial.begin(500000);          // Initialize serial communication at 115200 baud
    Serial1.begin(9600);           // Initialize second serial communication with GM-Counter
    pinMode(INTERRUPT_PIN, INPUT); // Configure the interrupt pin as an input
    // Attach interrupt to the pin, using RISING edge detection
    attachInterrupt(digitalPinToInterrupt(INTERRUPT_PIN), handleInterrupt, RISING);
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
        if (Serial.available() > 0)
        {
            sendMessage(Serial.readStringUntil('\n'), measurementInProgress, OPENBIS_CODE, DEBUG);
        }
    }
    else
    {
        // Serial.println("test");
        // If no measurement is in progress, check for incoming messages
        if (Serial1.available() > 0)
        {
            receiveMessage(Serial1.read(), message, index, MAX_LENGTH, DEBUG);
        }
        if (Serial.available() > 0)
        {
            sendMessage(Serial.readStringUntil('\n'), measurementInProgress, OPENBIS_CODE, DEBUG);
        }
    }
}