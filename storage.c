#include "storage.h"
#include <stdio.h>
#include <string.h>

#define VEHICLES_FILE "vehicles.txt"
#define SESSIONS_FILE "sessions.txt"
#define REVENUE_FILE "revenue.txt"

int storage_save_vehicle(const Vehicle *v) {
    FILE *f = fopen(VEHICLES_FILE, "a");
    if (!f) return 0;
    fprintf(f, "%s|%s|%.2f|%s|%s\n", v->owner, v->vehicleNo, v->batteryCapacity, v->chargingType, v->status);
    fclose(f);
    return 1;
}

int storage_load_vehicles(Vehicle *arr, int maxCount) {
    FILE *f = fopen(VEHICLES_FILE, "r");
    int count = 0;
    if (!f) return 0;
    while (count < maxCount && fscanf(f, " %63[^|]|%31[^|]|%f|%15[^|]|%23[^\n]\n", arr[count].owner,
            arr[count].vehicleNo, &arr[count].batteryCapacity, arr[count].chargingType, arr[count].status) == 5) {
        count++;
    }
    fclose(f);
    return count;
}

int storage_save_session(const char *vehicleNo, float energy, float totalCost, const char *dateText) {
    FILE *f = fopen(SESSIONS_FILE, "a");
    if (!f) return 0;
    fprintf(f, "%s|%.2f|%.2f|%s\n", vehicleNo, energy, totalCost, dateText);
    fclose(f);
    return 1;
}

int storage_add_revenue(float amount, const char *dateText) {
    FILE *f = fopen(REVENUE_FILE, "a");
    if (!f) return 0;
    fprintf(f, "%s|%.2f\n", dateText, amount);
    fclose(f);
    return 1;
}

float storage_get_total_revenue(void) {
    FILE *f = fopen(REVENUE_FILE, "r");
    char date[32];
    float amount, total = 0.0f;
    if (!f) return 0.0f;
    while (fscanf(f, " %31[^|]|%f\n", date, &amount) == 2) total += amount;
    fclose(f);
    return total;
}

int storage_get_total_sessions(void) {
    FILE *f = fopen(SESSIONS_FILE, "r");
    int count = 0;
    char line[256];
    if (!f) return 0;
    while (fgets(line, sizeof(line), f)) count++;
    fclose(f);
    return count;
}
