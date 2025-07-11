#ifndef SERIAL_COM_H
#define SERIAL_COM_H

#include <Arduino.h>

/**
 * @brief Initializes the serial communication and sets the debug mode
 *
 * @param debug_on Flag to enable or disable debug output
 * @param openbiscode OpenBIS code for the device
 * @param max_length Maximum length of a message line
 */
void init(bool debug_on, const char *openbiscode, int max_length);

/**
 * @brief Checks if a string is a valid integer
 *
 * @param str The string to check
 * @return true if the string is a valid integer, false otherwise
 */
bool isInteger(const char *str);

/**
 * @brief Receives and processes a character as part of a message
 *
 * @param receivedChar The character received from serial
 * @param message Buffer to store the message
 * @param index Current index in the message buffer
 */
void receiveMessage(char receivedChar, volatile char *message, volatile int &index);

/**
 * @brief Sends a message/command to the external device
 *
 * @param command The command string to send
 * @param measurementInProgress Reference to the measurement progress flag
 */
void sendMessage(String command, volatile bool &measurementInProgress);

#endif // SERIAL_COM_H
