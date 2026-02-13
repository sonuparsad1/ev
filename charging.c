#include "charging.h"
#include "billing.h"
#include "storage.h"
#include "vehicle.h"
#include <time.h>
#include <stdio.h>

static ChargingSlot g_slots[SLOT_COUNT];

void charging_init_slots(void) {
    int i;
    for (i = 0; i < SLOT_COUNT; i++) {
        g_slots[i].id = i + 1;
        g_slots[i].active = 0;
        g_slots[i].progress = 0;
        g_slots[i].vehicle.vehicleNo[0] = 0;
    }
}

ChargingSlot *charging_get_slots(void) { return g_slots; }

int charging_active_sessions(void) {
    int i, c = 0;
    for (i = 0; i < SLOT_COUNT; i++) if (g_slots[i].active) c++;
    return c;
}

int charging_available_slots(void) { return SLOT_COUNT - charging_active_sessions(); }

int charging_assign_vehicle(const Vehicle *v) {
    int i;
    for (i = 0; i < SLOT_COUNT; i++) {
        if (!g_slots[i].active) {
            g_slots[i].vehicle = *v;
            g_slots[i].active = 1;
            g_slots[i].progress = 0;
            vehicle_update_status(v->vehicleNo, "Charging");
            return 1;
        }
    }
    return 0;
}

void charging_tick(HWND hwnd) {
    int i;
    (void)hwnd;
    for (i = 0; i < SLOT_COUNT; i++) {
        if (g_slots[i].active) {
            g_slots[i].progress += 5;
            if (g_slots[i].progress >= 100) {
                Bill b;
                char dateText[32];
                time_t t = time(NULL);
                struct tm *tmv = localtime(&t);
                strftime(dateText, sizeof(dateText), "%Y-%m-%d", tmv);
                g_slots[i].progress = 100;
                b = billing_calculate(g_slots[i].vehicle.batteryCapacity, 100.0f);
                storage_save_session(g_slots[i].vehicle.vehicleNo, b.energy, b.total, dateText);
                storage_add_revenue(b.total, dateText);
                vehicle_update_status(g_slots[i].vehicle.vehicleNo, "Completed");
                g_slots[i].active = 0;
                g_slots[i].vehicle.vehicleNo[0] = 0;
                g_slots[i].progress = 0;
            }
        }
    }
}
