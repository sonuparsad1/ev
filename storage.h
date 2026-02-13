#ifndef STORAGE_H
#define STORAGE_H

#include "vehicle.h"

int storage_save_vehicle(const Vehicle *v);
int storage_load_vehicles(Vehicle *arr, int maxCount);
int storage_save_session(const char *vehicleNo, float energy, float totalCost, const char *dateText);
int storage_add_revenue(float amount, const char *dateText);
float storage_get_total_revenue(void);
int storage_get_total_sessions(void);

#endif
