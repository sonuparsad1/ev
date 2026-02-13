#include "vehicle.h"
#include "storage.h"
#include <string.h>
#include <stdio.h>

int vehicle_register(const char *owner, const char *vehicleNo, float battery, const char *chargingType) {
    Vehicle v;
    strncpy(v.owner, owner, MAX_NAME - 1); v.owner[MAX_NAME - 1] = 0;
    strncpy(v.vehicleNo, vehicleNo, MAX_VEHICLE_NO - 1); v.vehicleNo[MAX_VEHICLE_NO - 1] = 0;
    v.batteryCapacity = battery;
    strncpy(v.chargingType, chargingType, MAX_TYPE - 1); v.chargingType[MAX_TYPE - 1] = 0;
    strcpy(v.status, "Registered");
    return storage_save_vehicle(&v);
}

int vehicle_load_all(Vehicle *arr, int maxCount) {
    return storage_load_vehicles(arr, maxCount);
}

int vehicle_find_by_no(const char *vehicleNo, Vehicle *out) {
    Vehicle arr[MAX_VEHICLES];
    int n = vehicle_load_all(arr, MAX_VEHICLES);
    int i;
    for (i = 0; i < n; i++) {
        if (strcmp(arr[i].vehicleNo, vehicleNo) == 0) {
            if (out) *out = arr[i];
            return 1;
        }
    }
    return 0;
}

int vehicle_update_status(const char *vehicleNo, const char *status) {
    Vehicle arr[MAX_VEHICLES];
    int n = vehicle_load_all(arr, MAX_VEHICLES), i, found = 0;
    FILE *f;
    for (i = 0; i < n; i++) {
        if (strcmp(arr[i].vehicleNo, vehicleNo) == 0) {
            strncpy(arr[i].status, status, sizeof(arr[i].status) - 1);
            arr[i].status[sizeof(arr[i].status) - 1] = 0;
            found = 1;
            break;
        }
    }
    if (!found) return 0;
    f = fopen("vehicles.txt", "w");
    if (!f) return 0;
    for (i = 0; i < n; i++) {
        fprintf(f, "%s|%s|%.2f|%s|%s\n", arr[i].owner, arr[i].vehicleNo, arr[i].batteryCapacity, arr[i].chargingType, arr[i].status);
    }
    fclose(f);
    return 1;
}
