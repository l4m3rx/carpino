#include "Canbus.h"
#include "defaults.h"
#include "global.h"
#include "mcp2515.h"
#include "mcp2515_defs.h"
 
String CanMsg;
#define    CANSPEED_100    9     // 100 Kbps
//char mesaj [32] = "212 8 04 88 04 77 07 D0 E7 CF ";
char mesaj [32];
int canMesaj[10] = { 0 };
 
void setup() {
  Serial.begin(250000);
  Serial.println("CAN Read - Testing receival of CAN Bus message");  
  delay(1000);
 
  if(Canbus.init(CANSPEED_100))
    Serial.println("CAN Init ok");
  else
    Serial.println("Can't init CAN");
   
  delay(1000);
}
 
void loop(){
  tCAN message;
  if (mcp2515_check_message()) { // Messages from CAN
    if (mcp2515_get_message(&message)) {
      CanMsg = "ID: " + String(message.id, HEX) + String(" -");
      CanMsg = CanMsg + String(message.header.rtr, DEC) + String("- Data: [");
      CanMsg = CanMsg + String(message.header.length, DEC) + String("] ");
      for(int i=0;i<message.header.length;i++) {
        CanMsg = CanMsg + " " + String(message.data[i], HEX);
      }
      Serial.println(CanMsg);
      Serial.println("");
      Serial.flush();
      }
}
  // Message from serial
  if ( Serial.available() >= 31 ) {
    Serial.readBytes(mesaj, 31);
 
    char *pos = mesaj;
    canMesaj[0] = strtol(pos, &pos, 16);
    canMesaj[1] = strtol(pos, &pos, 16);
    canMesaj[2] = strtol(pos, &pos, 16);
    canMesaj[3] = strtol(pos, &pos, 16);
    canMesaj[4] = strtol(pos, &pos, 16);
    canMesaj[5] = strtol(pos, &pos, 16);
    canMesaj[6] = strtol(pos, &pos, 16);
    canMesaj[7] = strtol(pos, &pos, 16);
    canMesaj[8] = strtol(pos, &pos, 16);
    canMesaj[9] = strtol(pos, &pos, 16);
 
    for( int i = 0; i < 32;  ++i ) {
      mesaj[i] = 0;
    }
 
    tCAN message;
    message.id = canMesaj[0]; //formatted in HEX
    message.header.rtr = 0;
    message.header.length = canMesaj[1]; //formatted in DEC
    //for ( i=0; i<canMesaj[1], i++ ) {
    //  message.data[0] = canMesaj[(n+2)}
    //}
    message.data[0] = canMesaj[2];
    message.data[1] = canMesaj[3];
    message.data[2] = canMesaj[4];
    message.data[3] = canMesaj[5]; //formatted in HEX
    message.data[4] = canMesaj[6];
    message.data[5] = canMesaj[7];
    message.data[6] = canMesaj[8];
    message.data[7] = canMesaj[9];
 
    Serial.println("");
    mcp2515_bit_modify(CANCTRL, (1 << REQOP2) | (1 << REQOP1) | (1 << REQOP0), 0);
    mcp2515_send_message(&message);
    }
}

