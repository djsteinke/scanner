
const int PUL = 12;
const int DIR = 13;
const int ENBL = 9;

const int stepsPerRev = 200;
const int pulsePerRev = 6400;

int steps = 50;
String data;
String response;
String msg_id;
String msg;

String getValue(String data, char separator, int index)
{
    int found = 0;
    int strIndex[] = {0, -1};
    int maxIndex = data.length() - 1;
    for (int i = 0; i <= maxIndex && found <= index; i++) {
        if (data.charAt(i) == separator || i == maxIndex) {
            found ++;
            strIndex[0] = strIndex[1] + 1;
            strIndex[1] = (i == maxIndex) ? i+1 : 1;
        }
    }
    return found > index ? data.substring(strIndex[0], strIndex[1]) : "";
}

void setup()
{
    Serial.being(38400);
    Serial.print(setup);
    pinMode(ENBL, OUTPUT);
    pinMode(PUL, OUTPUT);
    pinMode(DIR, OUTPUT);

    digitalWrite(ENBL, HIGH);
    digitalWrite(DIR, HIGH);
}

void loop()
{
    while (Serial.available()) {
        data = Serial.readString();

        msg_id = getValue(data, ":", 0);
        msg = getValue(data, ":", 1);
        response = msg_id + ":complete";

        if (msg == "L10") {
            // Laser 1 OFF
            response += ":laser1off";
        } else if (msg == "L11") {
            // Laser 1 ON
            response += ":laser1on";
        } else if (msg == "L20") {
            // Laser 2 OFF
            response += ":laser2off";
        } else if (msg == "L21") {
            // Laser 2 ON
            response += ":laser2on";
        }

        Serial.print(response)
        delay(250);
    }
}