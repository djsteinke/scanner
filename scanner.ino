
const int PUL = 12;
const int DIR = 13;
const int ENBL = 9;

const int L1 = 6;
const int L2 = 7;

const int stepsPerRev = 200;
const int microSteps = 16;
const int pulsePerRev = 6400;
const int microPerStep;

int steps = 50;
long stepCount;
bool cw = false;
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

    microPerStep = 60000000/16/pulsePerRev;

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
        } else if (msg == "STEP") {
            stepCount = getValue(data, 2);
            cw = getValue(data, 3) == "CW";
            step(stepCount, cw);
        }

        Serial.print(response);
        delay(250);
    }
}

bool step(int numberOfSteps, int cw)
{
  if (cw) {
    digitalWrite(DIR, HIGH);
  } else {
    digitalWrite(DIR, LOW);
  }
  for(int n = 0; n < numberOfSteps; n++) {
    digitalWrite(PUL, HIGH);
    delayMicroseconds(20); // this line is probably unnecessary
    digitalWrite(PUL, LOW);
    delayMicroseconds(microPerStep);
  }
}

String getValue(String data, int index)
{
    int element = 0
    int found[] = {0, -1, -1, -1, -1};

    for (int i = 0; i <= maxIndex && element <= index+1; i++) {
        if (data.charAt(i) == ':') {
            element ++;
            found[element] = i
        }
    }
    return found[1] < 0 ? data : data.substring(found[index], found[index+1]-1);
}