#include <stdio.h>
#include <assert.h>
#include <stdlib.h>
#include <time.h>
#include <Arduino.h>
#include <Arduino_FreeRTOS.h>
#include <queue.h>
#include <semphr.h>
#include <SPI.h>
#include <EEPROM.h>
#include <ThreeWire.h>
#include <RtcDS1302.h>

#define V_TASK_DELAY
#define ADDR_LIGHT_THRESHOLD		6
#define ADDR_TEMPERATURE_THRESHOLD	8	
#define ADDR_LED_WORKMODE			15
#define PIN_SOUNDER					3
#define PIN_LDR						PIN_A1
#define PIN_SMOKE					PIN_A2
#define PIN_LM35					PIN_A4

int n_led = 4;
int led[] = {5, 10, 6, 12};
int status[4];

ThreeWire myWire(9, 8, 7); // IO, SCLK, CE
RtcDS1302<ThreeWire> Rtc(myWire);

QueueHandle_t Queue_SendData;

SemaphoreHandle_t Mutex_CurrentLightThreshold;
SemaphoreHandle_t Mutex_CurrentTemperatureThreshold;
SemaphoreHandle_t Mutex_LEDWorkMode;
SemaphoreHandle_t Mutex_ACWorkMode;
SemaphoreHandle_t Mutex_Alert;
SemaphoreHandle_t Mutex_Serial;
SemaphoreHandle_t Mutex_Status;

TaskHandle_t Task_LightIntensityData;
TaskHandle_t Task_TemperatureData;
TaskHandle_t Task_LEDStatusData;
TaskHandle_t Task_ACStatusData;
TaskHandle_t Task_SendData;
TaskHandle_t Task_GetData;

enum DataToServerTaskType {
	Nothing_DataToServerTaskType,
	LightIntensity,
	Temprature,
	LEDStatus,
	ACStatus,
};

enum DataFromServerTaskType {
	Nothing_DataFromServerTaskType,
	LightThreshold,
	TemperatureThreshold,
	LEDWorkMode,
	ACWorkMode,
};

struct DataToServer {
	DataToServerTaskType type;
	int value1, value2;
};

struct DataFromServer {
	DataFromServerTaskType type;
	int id, value;
};

void TaskLightIntensityData(void *pvParameters);
void TaskTemperatureData(void *pvParameters);
void TaskLEDData(void *pvParameters);
// void TaskACData(void *pvParameters);
void TaskSendData(void *pvParameters);
void TaskGetData(void *pvParameters);

int GetTemperatureThreshold();
void SetTemperatureThreshold(int value);
int GetTemperatureThreshold();
void SetTemperatureThreshold(int value);
int GetLEDWorkMode(int id);
void SetLEDWorkMode(int id, int value); 
int GetACWorkMode();
void SetACWorkMode(int value);
void Alert(bool);
void printDateTime(const RtcDateTime& dt);

void setup() {
	// SP = RAMEND; // 初始化栈指针
	Serial.begin(9600);
	Rtc.Begin();

	pinMode(PIN_SOUNDER, OUTPUT);
	for (int i = 0; i < n_led; i++) {
		pinMode(led[i], OUTPUT);
		digitalWrite(led[i], LOW);
	}

	Queue_SendData = xQueueCreate(3, sizeof(DataToServer));
	
	// assert(Queue_SendData != NULL);
	// DataToServer dataToServer;
	// assert(0);
	// while(xQueueReceive(Queue_SendData, &dataToServer, portMAX_DELAY) == pdPASS);
	// assert(xQueueReceive(Queue_SendData, &dataToServer, portMAX_DELAY) != pdPASS);

	Mutex_CurrentLightThreshold = xSemaphoreCreateMutex();
	Mutex_CurrentTemperatureThreshold = xSemaphoreCreateMutex();
	Mutex_LEDWorkMode = xSemaphoreCreateMutex();
	Mutex_ACWorkMode = xSemaphoreCreateMutex();
	Mutex_Alert = xSemaphoreCreateMutex();
	Mutex_Serial = xSemaphoreCreateMutex();
	Mutex_Status = xSemaphoreCreateMutex();

	xSemaphoreGive(Mutex_CurrentLightThreshold);
	xSemaphoreGive(Mutex_CurrentTemperatureThreshold);
	xSemaphoreGive(Mutex_LEDWorkMode);
	xSemaphoreGive(Mutex_ACWorkMode);
	xSemaphoreGive(Mutex_Alert);
	xSemaphoreGive(Mutex_Serial);
	xSemaphoreGive(Mutex_Status);

	for (int i = 0; i < n_led; i++) {
		status[i] = GetLEDWorkMode(i);
		if (status[i] <= 1) {
			digitalWrite(led[i], status[i]);
		}
	}

	// while(Serial.available())
	// 	Serial.read();

	xTaskCreate(TaskLightIntensityData, "LightIntensityData", 72, NULL, 1, &Task_LightIntensityData);	
	xTaskCreate(TaskTemperatureData, "TemperatureData", 72, NULL, 1, &Task_TemperatureData);
	xTaskCreate(TaskLEDData, "LEDData", 72, NULL, 1, &Task_LEDStatusData);
	// xTaskCreate(TaskACData, "ACData", 72, NULL, 2, &Task_ACStatusData);
	xTaskCreate(TaskSendData, "SendData", 96, NULL, 3, &Task_SendData);
	xTaskCreate(TaskGetData, "GetData", 96, NULL, 3, &Task_GetData);

	vTaskStartScheduler();
}

void loop() {
	// digitalWrite(led[0], LOW);
	// delay(1500);
	// digitalWrite(led[0], HIGH);
	// delay(1500);
	
}

int GetLightThreshold() {
	xSemaphoreTake(Mutex_CurrentLightThreshold, portMAX_DELAY);
	int data1 = (int)EEPROM.read(ADDR_LIGHT_THRESHOLD);
	int data2 = (int)EEPROM.read(ADDR_LIGHT_THRESHOLD + 1);
	int data = (data1 << 8) + data2;
	xSemaphoreGive(Mutex_CurrentLightThreshold);
	return data;
}

void SetLightThreshold(int value) {
	xSemaphoreTake(Mutex_CurrentLightThreshold, portMAX_DELAY);
	EEPROM.write(ADDR_LIGHT_THRESHOLD, byte(value >> 8));
	EEPROM.write(ADDR_LIGHT_THRESHOLD + 1, byte(value & ((1 << 8) - 1)));
	xSemaphoreGive(Mutex_CurrentLightThreshold);
}

int GetTemperatureThreshold() {
	xSemaphoreTake(Mutex_CurrentTemperatureThreshold, portMAX_DELAY);
	int data1 = (int)EEPROM.read(ADDR_TEMPERATURE_THRESHOLD);
	int data2 = (int)EEPROM.read(ADDR_TEMPERATURE_THRESHOLD + 1);
	int data = (data1 << 8) + data2;
	xSemaphoreGive(Mutex_CurrentTemperatureThreshold);
	return data;
}

void SetTemperatureThreshold(int value) {
	xSemaphoreTake(Mutex_CurrentTemperatureThreshold, portMAX_DELAY);
	EEPROM.write(ADDR_TEMPERATURE_THRESHOLD, byte(value >> 8));
	EEPROM.write(ADDR_TEMPERATURE_THRESHOLD + 1, byte(value & ((1 << 8) - 1)));
	xSemaphoreGive(Mutex_CurrentTemperatureThreshold);
}

int GetLEDWorkMode(int id) {
	xSemaphoreTake(Mutex_LEDWorkMode, portMAX_DELAY);
	int value = EEPROM.read(ADDR_LED_WORKMODE + id);
	xSemaphoreGive(Mutex_LEDWorkMode);
	return value;
}

void SetLEDWorkMode(int id, int value) {
	xSemaphoreTake(Mutex_LEDWorkMode, portMAX_DELAY);

	if(0<=value && value<=1){
		EEPROM.write(ADDR_LED_WORKMODE + id, byte(value));
		digitalWrite(led[id], value);
	}

	xSemaphoreGive(Mutex_LEDWorkMode);

    xSemaphoreTake(Mutex_Status, portMAX_DELAY);
    status[id] = value;
    xSemaphoreGive(Mutex_Status);
}

int GetACWorkMode(){
	return GetLEDWorkMode(3);
}

void SetACWorkMode(int value){
	SetLEDWorkMode(3, value);
}

void Alert(bool isOn) {
	xSemaphoreTake(Mutex_Alert, portMAX_DELAY);
	if (isOn) {
		analogWrite(PIN_SOUNDER, 127);
	} else {
		analogWrite(PIN_SOUNDER, 0);
	}
	xSemaphoreGive(Mutex_Alert);
}

void printDateTime(const RtcDateTime& dt) {
	char datestring[20];
	snprintf_P(datestring, 
			countof(datestring),
			PSTR("%04u/%02u/%02u %02u:%02u:%02u"),
			dt.Year(),
			dt.Month(),
			dt.Day(),
			dt.Hour(),
			dt.Minute(),
			dt.Second() );
	Serial.print(datestring);
}

bool alert[] = {false, false};
// 光强 A1
void TaskLightIntensityData(void *pvParameters) {
	for (;;) {
		float LightData = analogRead(PIN_LDR), LightThreshold = GetLightThreshold();
		LightData = (LightData - 250) /5;
		if(LightData >= LightThreshold){
			alert[0] = true;
			Alert(true);
		}else{
			alert[0] = false;
			if(!alert[0] && !alert[1])
				Alert(false);
		}
		DataToServer LightIntensityData = (DataToServer){LightIntensity, (int)LightData, (int)LightThreshold};
		xQueueSend(Queue_SendData, &LightIntensityData, portMAX_DELAY);
#ifdef V_TASK_DELAY
		vTaskDelay(1000 / portTICK_PERIOD_MS * 10);
#endif
	}
}

// Temprature 温度
void TaskTemperatureData(void *pvParameters) {
	for(;;) {
		float t = analogRead(PIN_LM35) * 0.48828125, threshold = GetTemperatureThreshold();
		if(t >= threshold){
			alert[1] = true;
			Alert(true);
		}else{
			alert[1] = false;
			if(!alert[0] && !alert[1])
				Alert(false);
		}
		DataToServer temperatureData = (DataToServer){Temprature, (int)t, (int)threshold};
		xQueueSend(Queue_SendData, &temperatureData, portMAX_DELAY);
#ifdef V_TASK_DELAY
		vTaskDelay(1000 / portTICK_PERIOD_MS * 10);
#endif
	}
}

void TaskLEDData(void *pvParameters){
	for(;;) {
		xSemaphoreTake(Mutex_Status, portMAX_DELAY);
		DataToServer LEDData = (DataToServer){LEDStatus, status[0]|status[1]<<1, status[2]|status[3]<<1};
		xSemaphoreGive(Mutex_Status);

		xQueueSend(Queue_SendData, &LEDData, portMAX_DELAY);
#ifdef V_TASK_DELAY
		vTaskDelay(1000 / portTICK_PERIOD_MS * 10);
#endif
	}
}

// void TaskACData(void *pvParameters){
// 	for(;;) {
// 		xSemaphoreTake(Mutex_Status, portMAX_DELAY);
// 		DataToServer ACData = (DataToServer){ACStatus, (float)status[3], 0.0, 0.0};
// 		xSemaphoreGive(Mutex_Status);

// 		xQueueSend(Queue_SendData, &ACData, portMAX_DELAY);
// #ifdef V_TASK_DELAY
// 		vTaskDelay(1000 / portTICK_PERIOD_MS * 10);
// #endif
// 	}
// }


DataToServer dataToServer;

void TaskSendData(void *pvParameters) {
	for (;;) {
		if (xQueueReceive(Queue_SendData, &dataToServer, portMAX_DELAY) == pdPASS) {
			xSemaphoreTake(Mutex_Serial, portMAX_DELAY);
			Serial.print(dataToServer.type);
			Serial.print("\t");
			Serial.print(dataToServer.value1);
			Serial.print("\t");
			Serial.print(dataToServer.value2);
			Serial.print("\t");
			printDateTime(Rtc.GetDateTime());
			Serial.println();
			xSemaphoreGive(Mutex_Serial);
		}

#ifdef V_TASK_DELAY
		vTaskDelay(1000 / portTICK_PERIOD_MS);
#endif

	}
}

String strRead;
DataFromServer dataFromServer;

void TaskGetData(void *pvParameters) {
	for (;;) {
		strRead = "";
		while (Serial.available() > 0){
			strRead += char(Serial.read());
			vTaskDelay(20 / portTICK_PERIOD_MS);
		}
		sscanf(strRead.c_str(), "%d%d%d", (int *)&dataFromServer.type, &dataFromServer.id, &dataFromServer.value);
		// assert(dataFromServer.type != LightThreshold);

		switch (dataFromServer.type) {
			case Nothing_DataFromServerTaskType:
				break;
			case LightThreshold:
				SetLightThreshold(dataFromServer.value);
				break;
			case TemperatureThreshold:
				SetTemperatureThreshold(dataFromServer.value);
				break;
			case LEDWorkMode:
				SetLEDWorkMode(dataFromServer.id, dataFromServer.value);
				break;
			case ACWorkMode:
				SetLEDWorkMode(3, dataFromServer.value);
				break;
        }

#ifdef V_TASK_DELAY
		vTaskDelay(1000 / portTICK_PERIOD_MS);
#endif

	}
}
