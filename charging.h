#ifndef CHARGING_H
#define CHARGING_H

#include <windows.h>
#include "vehicle.h"

#define SLOT_COUNT 4

typedef struct {
    int id;
    int active;
    Vehicle vehicle;
    int progress;
} ChargingSlot;

void charging_init_slots(void);
ChargingSlot *charging_get_slots(void);
int charging_active_sessions(void);
int charging_available_slots(void);
void charging_tick(HWND hwnd);
int charging_assign_vehicle(const Vehicle *v);

#endif
