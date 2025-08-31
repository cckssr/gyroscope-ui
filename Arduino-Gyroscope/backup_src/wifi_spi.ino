#include "WiFiS3.h"
#include "secrets.h" 
#include <Adafruit_LSM6DS3TRC.h>

#define LSM_CS 7
#define LSM_SCK 13
#define LSM_MISO 12
#define LSM_MOSI 11

Adafruit_LSM6DS3TRC lsm6ds3trc;

volatile unsigned long lastMillis = 0;
volatile unsigned long lastlastMillis = 0;

void handleInterrupt() {
  lastlastMillis = lastMillis;
  lastMillis = millis();
}

// Buffer for printing
char buffer[256];



// Hall Sensor
const int hallDigitalPin = 2;   // pin for hall sensor reading
int hallDigital;                // variable for hall sensor value

///////please enter your sensitive data in the Secret tab/arduino_secrets.h
char ssid[] = SECRET_SSID;        // your network SSID (name)
char pass[] = SECRET_PASS;        // your network password (use for WPA, or use as key for WEP)
int keyIndex = 0;                 // your network key index number (needed only for WEP)

int status = WL_IDLE_STATUS;
WiFiServer server(80);

void setup() {
  pinMode(hallDigitalPin,INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(hallDigitalPin), handleInterrupt, FALLING);
  pinMode(LED_BUILTIN,OUTPUT);
  //Initialize serial and wait for port to open:
  Serial.begin(9600);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }
  
  Serial.println("Access Point Web Server");
  
  // check for the WiFi module:
  if (WiFi.status() == WL_NO_MODULE) {
    Serial.println("Communication with WiFi module failed!");
    // don't continue
    while (true);
  }

  String fv = WiFi.firmwareVersion();
  if (fv < WIFI_FIRMWARE_LATEST_VERSION) {
    Serial.println("Please upgrade the firmware");
  }

  // by default the local IP address will be 192.168.4.1
  // you can override it with the following:
  //WiFi.config(IPAddress(192,48,56,2));

  // print the network name (SSID);
  Serial.print("Creating access point named: ");
  Serial.println(ssid);

  // Create open network. Change this line if you want to create an WEP network:
  status = WiFi.beginAP(ssid, pass);
  if (status != WL_AP_LISTENING) {
    Serial.println("Creating access point failed");
    // don't continue
    while (true);
  }

  // wait 10 seconds for connection:la
  delay(10000);

  // start the web server on port 80
  server.begin();

  // you're connected now, so print out the status
  printWiFiStatus();

   if (!lsm6ds3trc.begin_SPI(LSM_CS)) {
    Serial.println("Failed to find LSM6DS3TR-C chip");
    while (1) {
      delay(10);
    }
  }

  Serial.println("LSM6DS3TR-C Found!");
}


void loop() {
  
  // compare the previous status to the current status
  if (status != WiFi.status()) {
    // it has changed update the variable
    status = WiFi.status();

    if (status == WL_AP_CONNECTED) {
      // a device has connected to the AP
      Serial.println("Device connected to AP");
    } else {
      // a device has disconnected from the AP, and we are back in listening mode
      Serial.println("Device disconnected from AP");
    }
  }
  
  WiFiClient client = server.available();   // listen for incoming clients


  if (client) {                             // if you get a client,
    
    Serial.println("new client");           // print a message out the serial port
    Serial.println();
    

    String currentLine = "";                // make a String to hold incoming data from the client
    while (client.connected()) {            // loop while the client's connected
      delayMicroseconds(10);                // This is required for the Arduino Nano RP2040 Connect - otherwise it will loop so fast that SPI will never be served.
      if (client.available()) {             // if there's bytes to read from the client,

         // read sensor values
        //hallDigital = digitalRead(hallDigitalPin);
        //Serial.println(hallDigital);
        // control LED: High means magnet is far away
        // if(hallDigital == HIGH){
        // digitalWrite(LED_BUILTIN,LOW);
        //}
  
        //else{
        // digitalWrite(LED_BUILTIN,HIGH);
       //}

        noInterrupts();
        unsigned long lasttprint = lastlastMillis;
        unsigned long tprint = lastMillis;
        interrupts();

        sensors_event_t accel;
        sensors_event_t gyro;
        sensors_event_t temp;
    
        lsm6ds3trc.getEvent(&accel, &gyro, &temp);
    
        snprintf(buffer, sizeof(buffer), "%lu,%d,%d,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f", millis(),tprint, lasttprint,accel.acceleration.x,accel.acceleration.y,accel.acceleration.z,gyro.gyro.x,gyro.gyro.y,gyro.gyro.z,accel.acceleration.x,accel.acceleration.y,accel.acceleration.z,gyro.gyro.x,gyro.gyro.y,gyro.gyro.z);

        client.println(buffer);
 
        //Serial.print(millis());
        //Serial.print(",");
        //Serial.print(hallDigital);
        //Serial.print(",");
        //Serial.print(accel.acceleration.x);
        //Serial.print(",");
        //Serial.print(accel.acceleration.y);
        //Serial.print(","); 
        //Serial.print(accel.acceleration.z);
        //Serial.print(",");
        //Serial.print(gyro.gyro.x);
        //Serial.print(","); 
        //Serial.print(gyro.gyro.y);
        //Serial.print(",");
        //Serial.print(gyro.gyro.z);
        //Serial.print(",");
        //Serial.print(accel2.acceleration.x);
        //Serial.print(",");
        //Serial.print(accel2.acceleration.y);
        //Serial.print(","); 
        //Serial.print(accel2.acceleration.z);
        //Serial.print(",");
        //Serial.print(gyro2.gyro.x);
        //Serial.print(","); 
        //Serial.print(gyro2.gyro.y);
        //Serial.print(",");
        //Serial.println(gyro2.gyro.z);
        delay(10);
        }
        
      }
    }
    
    
    //Serial.println("client disconnected");
  
}


void printWiFiStatus() {
  // print the SSID of the network you're attached to:
  Serial.print("SSID: ");
  Serial.println(WiFi.SSID());

  // print your WiFi shield's IP address:
  IPAddress ip = WiFi.localIP();
  Serial.print("IP Address: ");
  Serial.println(ip);

}
