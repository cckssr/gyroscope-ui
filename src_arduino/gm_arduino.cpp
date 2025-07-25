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
volatile unsigned long lastPulseTime = 0;   // Timestamp of the last pulse (volatile because it's accessed from interrupt)
volatile bool firstPulseOccurred = false;   // Flag to identify the first pulse event
volatile uint32_t timestamp = 0;            // Timestamp of the current pulse
static uint32_t last_timestamp = 0;         // Last timestamp for delta calculation
volatile uint32_t currentDelta = 0;         // Updated in the interrupt handler
volatile bool measurementInProgress = true; // Flag to indicate if a measurement is in progress
volatile char message[MAX_LENGTH + 1];      // Buffer (+1 for null terminator)
volatile int index = 0;                     // Current position in buffer
volatile unsigned long buffer[BUFFER_SIZE]; // Buffer for storing incoming messages
volatile int bufferIndex = 0;               // Current position in the buffer
volatile bool bufferFull = false;           // Flag to indicate if the buffer is full

volatile uint32_t timestamps[128];
volatile uint8_t writeIndex = 0;
volatile uint8_t readIndex = 0;

/**
 * ISR handler function
 * This function is called in the interrupt context to store the current time in microseconds.
 * It wraps around the writeIndex to keep it within the bounds of the timestamps array.
 * The function is keept simple and fast to ensure it can be executed quickly without blocking.
 * This is used to measure the time intervals between interrupts.
 */
void isr_handle()
{
    timestamps[writeIndex++] = micros(); // Store the current time in microseconds
    writeIndex %= 128;                   // Wrap around to keep the index within bounds
}
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

void debugByteValue(u_int32_t value)
{
    // Use Serial1 for debug to avoid mixing with binary data on Serial
    Serial.print("DEBUG - Sent value: ");
    Serial.print(value, DEC);
    Serial.print(" (0x");
    Serial.print(value, HEX);
    Serial.println(")");
}
/**
 * Sends a 32-bit unsigned integer as pure binary data over Serial.
 * The data is sent in little-endian format, starting with a start byte (0xAA),
 * followed by the four bytes of the integer, and ending with an end byte (0x55).
 *
 * @param value The 32-bit unsigned integer to send.
 */
void sendByteValue(u_int32_t value)
{
    // Send pure binary data without any text mixing
    Serial.write(0xAA);                            // Start byte
    Serial.write((uint8_t)(value & 0xFF));         // Byte 0 (LSB)
    Serial.write((uint8_t)((value >> 8) & 0xFF));  // Byte 1
    Serial.write((uint8_t)((value >> 16) & 0xFF)); // Byte 2
    Serial.write((uint8_t)((value >> 24) & 0xFF)); // Byte 3 (MSB)
    // Serial1.write(0x55);                            // End byte for packet validation
    if (DEBUG)
    {
        Serial.println("DEBUG - Sent value: " + String(value));
    }
}

void handleTimer()
{
    // Safely read the shared variable
    noInterrupts(); // Disable interrupts for atomic access to shared variables
    if (readIndex != writeIndex)
    {
        timestamp = timestamps[readIndex]; // Copy the value to a local variable
        readIndex = (readIndex + 1) % 128; // Increment readIndex and wrap around
    }
    interrupts(); // Re-enable interrupts

    if (timestamp != 0)
    {
        currentDelta = timestamp - last_timestamp; // Calculate the delta time since the last timestamp
        last_timestamp = timestamp;                // Update the last timestamp
        if (currentDelta > DEBOUNCE_TIME)
        {
            sendByteValue(currentDelta); // Send the value as pure binary data
        }
    }
}

/**
 * Setup function
 * Runs once when the Arduino starts.
 * Initializes serial communication and configures the interrupt.
 */
void setup()
{
    init(DEBUG, OPENBIS_CODE, MAX_LENGTH); // Initialize serial communication and set debug mode
    Serial.begin(1000000);                 // Initialize serial communication at 115200 baud
    // Serial1.begin(9600);           // Initialize second serial communication with GM-Counter
    Serial1.begin(1000000);        // Initialize second serial communication with GM-Counter
    pinMode(INTERRUPT_PIN, INPUT); // Configure the interrupt pin as an input
    // Attach interrupt to the pin, using RISING edge detection
    attachInterrupt(digitalPinToInterrupt(INTERRUPT_PIN), isr_handle, RISING);
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
            sendMessage(Serial.readStringUntil('\n'), measurementInProgress);
        }
    }
    else
    {
        // Serial.println("test");
        // If no measurement is in progress, check for incoming messages
        if (Serial1.available() > 0)
        {
            receiveMessage(Serial1.read(), message, index);
        }
        if (Serial.available() > 0)
        {
            sendMessage(Serial.readStringUntil('\n'), measurementInProgress);
        }
    }
}