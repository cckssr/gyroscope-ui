#ifndef SERIAL_COM_H
#define SERIAL_COM_H

#include <Arduino.h>

/**
 * @brief Checks if a string is a valid integer
 *
 * @param str The string to check
 * @return true if the string is a valid integer, false otherwise
 */
bool isInteger(const char *str);

/**
 * @brief Validates a received message according to specific format rules
 *
 * @param msg The message to validate
 * @param debug Debug flag to enable/disable debug output
 * @return true if the message is valid, false otherwise
 */
bool validateMessage(volatile char *msg, bool debug);

/**
 * @brief Receives and processes a character as part of a message
 *
 * @param receivedChar The character received from serial
 * @param message Buffer to store the message
 * @param index Current index in the message buffer
 * @param maxLength Maximum length of the message buffer
 * @param debug Debug flag to enable/disable debug output
 */
void receiveMessage(char receivedChar, volatile char *message, volatile int &index, int maxLength, bool debug);

/**
 * @brief Sends a message/command to the external device
 *
 * @param command The command string to send
 * @param measurementInProgress Reference to the measurement progress flag
 * @param openBisCode The OpenBIS code to send with info command
 * @param debug Debug flag to enable/disable debug output
 */
void sendMessage(String command, volatile bool &measurementInProgress, const char *openBisCode, bool debug);

#endif // SERIAL_COM_H
