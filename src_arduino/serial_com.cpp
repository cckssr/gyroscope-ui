#include <Arduino.h>
#include "serial_com.h"

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
 * @param debug Debug flag to enable/disable debug output
 * @return true if the message is valid, false otherwise
 */
bool validateMessage(volatile char *msg, bool debug)
{
    int numberCount = 0; // Number of integers found
    char temp[10];       // Buffer for current number
    int tempIndex = 0;   // Index for temporary number
    bool isValid = true;

    if (debug)
    {
        Serial.print("Complete message is ");
        Serial.println((const char *)msg);
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

/**
 * @brief Receives and processes a character as part of a message
 *
 * @param receivedChar The character received from serial
 * @param message Buffer to store the message
 * @param index Current index in the message buffer
 * @param maxLength Maximum length of the message buffer
 * @param debug Debug flag to enable/disable debug output
 */
void receiveMessage(char receivedChar, volatile char *message, volatile int &index, int maxLength, bool debug)
{
    // Check for end of message (newline)
    if (receivedChar == '\n')
    {
        message[index] = '\0'; // Add null terminator
        if (!debug)
        {
            Serial.println((char *)message);
        }
        else
        {
            // Validate message
            if (validateMessage(message, debug))
            {
                Serial.print("Message is valid: ");
                Serial.println((char *)message);
            }
            else
            {
                Serial.println("invalid");
            }
        }
        // Reset buffer
        index = 0;
    }
    // Check for buffer overflow
    else if (index >= maxLength - 1)
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

/**
 * @brief Sends a message/command to the external device
 *
 * @param command The command string to send
 * @param measurementInProgress Reference to the measurement progress flag
 * @param openBisCode The OpenBIS code to send with info command
 * @param debug Debug flag to enable/disable debug output
 */
void sendMessage(String command, volatile bool &measurementInProgress, const char *openBisCode, bool debug)
{
    // Send commands to the external device
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
    if (command == "s0")
    {
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
    if (command == "info")
    {
        // Handle info command
        if (debug)
        {
            Serial.println("Info command received.");
        }
        Serial.print("OpenBIS code: ");
        Serial.println(openBisCode); // Send OpenBIS code
    }
}
