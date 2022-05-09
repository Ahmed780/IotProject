#include <WiFi.h>
#include <SPI.h>
#include <PubSubClient.h>
#include <MFRC522.h>
#include "DHTesp.h"

const int sensorPin = 34; 
const int dht11Pin = 13;
#define SS_PIN  5
#define RST_PIN 17
DHTesp dht;
String id;

//Set up some global variables for the light level an initial value.
int lightVal;  // initial value
MFRC522 rfid(SS_PIN, RST_PIN);

const char* ssid = "Bear"; //replace here
const char* password = "getyourownwifi"; //replace here
const char* mqtt_server = "192.168.156.115"; //replace here

//const char* ssid = "BELL721-2.4"; //replace here
//const char* password = "37395A2A"; //replace here
//const char* mqtt_server = "192.168.2.105"; //replace here

//const char* ssid = "TP-Link_2AD8"; //replace here
//const char* password = "14730078"; //replace here
//const char* mqtt_server = "192.168.0.178"; //replace here

WiFiClient vanieriot;
PubSubClient client(vanieriot);

unsigned long previousMillis = 0;
unsigned long interval = 30000;

void setup() {
  Serial.begin(115200);
  setup_wifi();
  client.setServer(mqtt_server, 1883);
  dht.setup(dht11Pin, DHTesp::DHT11);
  SPI.begin(); // init SPI bus
  rfid.PCD_Init(); // init MFRC522
}

void loop() {
  unsigned long currentMillis = millis();
  // if WiFi is down, try reconnecting every CHECK_WIFI_TIME seconds
  if ((WiFi.status() != WL_CONNECTED) && (currentMillis - previousMillis >=interval)) {
    Serial.print(millis());
    Serial.println("Reconnecting to WiFi...");
    WiFi.disconnect();
    WiFi.reconnect();
    previousMillis = currentMillis;
  }
  else {
     lightVal = analogRead(sensorPin); // read the current light levels
     
     char lightArr [8];
     dtostrf(lightVal,6,2,lightArr);
  
     float temp= dht.getTemperature();
     float hum= dht.getHumidity();
    
     char tempArr [8];
     dtostrf(temp,6,2,tempArr);
     char humArr [8];
     dtostrf(hum,6,2,humArr);

     String idTemp;

     if (client.connect("vanieriot")) { 
      delay(500); 
      client.publish("IoTLab/light", lightArr);
      client.publish("IoTLab/temperature", tempArr);
      client.publish("IoTLab/humidity", humArr); 

      if (rfid.PICC_IsNewCardPresent()) { // new tag is available
        if (rfid.PICC_ReadCardSerial()) { // NUID has been readed
          MFRC522::PICC_Type piccType = rfid.PICC_GetType(rfid.uid.sak);
          for (int i = 0; i < rfid.uid.size; i++) {
              idTemp.concat(String(rfid.uid.uidByte[i] < 0x10 ? " 0" : " "));
              idTemp.concat(String(rfid.uid.uidByte[i], HEX));
              idTemp.toUpperCase();
              id = idTemp;
          }
          rfid.PICC_HaltA(); // halt PICC
          rfid.PCD_StopCrypto1(); // stop encryption on PCD  
        }
      }
      
      int str_len = id.length() + 1;
      char rfidArr [str_len];
      id.toCharArray(rfidArr, str_len);
      client.publish("IoTLab/rfid", rfidArr);
      
    }
  }
}

void setup_wifi() {
  delay(10);
  // We start by connecting to a WiFi network
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print("*");
  }
  Serial.println("");
  Serial.print("WiFi connected - ESP-32 IP address: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
      if (client.connect("vanieriot")) {
      Serial.println("connected");  
      client.publish("IoTLab/light", "Hello");
    } else {
      delay(5000);
    }
  }
}
