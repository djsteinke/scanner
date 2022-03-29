
const int PUL = 12;
const int DIR = 13;
const int ENBL = 9;

const int L1 = 6;
const int L2 = 7;

const int stepsPerRev = 200;
const int pulsePerRev = 6400;

int steps = 50;
String data;
String response;
String msg_id;
String msg;

void setup()
{
    Serial.begin(38400);
    Serial.print("setup");
    pinMode(ENBL, OUTPUT);
    pinMode(PUL, OUTPUT);
    pinMode(DIR, OUTPUT);
    digitalWrite(ENBL, HIGH);
    digitalWrite(DIR, HIGH);

    pinMode(L1, OUTPUT);
    pinMode(L2, OUTPUT);
    digitalWrite(L1, LOW);
    digitalWrite(L2, LOW);

}

void loop()
{
    while (Serial.available()) {
        data = Serial.readString();

        msg_id = getValue(data, 0);
        msg = getValue(data, 1);
        response = msg_id + ":complete";

        if (msg == "L10") {
            // Laser 1 OFF
            response += ":laser1off";
            digitalWrite(L1, LOW);
        } else if (msg == "L11") {
            // Laser 1 ON
            response += ":laser1on";
            digitalWrite(L1, HIGH);
        } else if (msg == "L20") {
            // Laser 2 OFF
            response += ":laser2off";
            digitalWrite(L2, LOW);
        } else if (msg == "L21") {
            // Laser 2 ON
            response += ":laser2on";
            digitalWrite(L2, HIGH);
        }

        Serial.print(response);
        delay(250);
    }
}

String getValue(String data, int index)
{
    int found = 0;
    int strIndex[] = {0, -1};
    int maxIndex = data.length() - 1;
    for (int i = 0; i <= maxIndex && found <= index; i++) {
        if (data.charAt(i) == ':' || i == maxIndex) {
            found ++;
            strIndex[0] = strIndex[1] + 1;
            strIndex[1] = (i == maxIndex) ? i+1 : 1;
        }
    }
    return found > index ? data.substring(strIndex[0], strIndex[1]) : "";
}