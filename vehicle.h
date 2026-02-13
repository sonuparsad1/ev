#ifndef VEHICLE_H
#define VEHICLE_H

#define MAX_NAME 64
#define MAX_VEHICLE_NO 32
#define MAX_TYPE 16
#define MAX_VEHICLES 512

typedef struct {
    char owner[MAX_NAME];
    char vehicleNo[MAX_VEHICLE_NO];
    float batteryCapacity;
    char chargingType[MAX_TYPE];
    char status[24];
} Vehicle;

int vehicle_register(const char *owner, const char *vehicleNo, float battery, const char *chargingType);
int vehicle_load_all(Vehicle *arr, int maxCount);
int vehicle_find_by_no(const char *vehicleNo, Vehicle *out);
int vehicle_update_status(const char *vehicleNo, const char *status);

#endif
