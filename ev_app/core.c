#include "core.h"
#include <stdlib.h>
#include <string.h>

#define MAX_SLOTS 6
#define RATE_PER_KWH 15.0
#define TAX_RATE 0.05
#define FAST_FACTOR 1.6
#define SLOW_FACTOR 0.9

typedef struct VehicleNode {
    char id[32];
    double capacity;
    int charging_type;
    struct VehicleNode *next;
} VehicleNode;

typedef struct QueueNode {
    char id[32];
    struct QueueNode *next;
} QueueNode;

typedef struct Slot {
    int active;
    char id[32];
    double capacity;
    int charging_type;
    double energy;
    double percent;
} Slot;

static VehicleNode *registry = NULL;
static QueueNode *queue_head = NULL;
static QueueNode *queue_tail = NULL;
static Slot slots[MAX_SLOTS] = {0};
static int total_vehicles = 0;
static double total_revenue = 0.0;

static VehicleNode *find_vehicle(const char *id) {
    VehicleNode *cur = registry;
    while (cur) {
        if (strcmp(cur->id, id) == 0) return cur;
        cur = cur->next;
    }
    return NULL;
}

void register_vehicle(const char *vehicle_id, double capacity_kwh, int charging_type) {
    VehicleNode *existing = find_vehicle(vehicle_id);
    if (existing) {
        existing->capacity = capacity_kwh;
        existing->charging_type = charging_type;
        return;
    }
    VehicleNode *node = (VehicleNode *)malloc(sizeof(VehicleNode));
    if (!node) return;
    strncpy(node->id, vehicle_id, sizeof(node->id) - 1);
    node->id[sizeof(node->id) - 1] = '\0';
    node->capacity = capacity_kwh;
    node->charging_type = charging_type;
    node->next = registry;
    registry = node;
    total_vehicles++;
}

int enqueue_vehicle(const char *vehicle_id) {
    if (!find_vehicle(vehicle_id)) return 0;
    QueueNode *node = (QueueNode *)malloc(sizeof(QueueNode));
    if (!node) return 0;
    strncpy(node->id, vehicle_id, sizeof(node->id) - 1);
    node->id[sizeof(node->id) - 1] = '\0';
    node->next = NULL;
    if (!queue_head) {
        queue_head = queue_tail = node;
    } else {
        queue_tail->next = node;
        queue_tail = node;
    }
    return 1;
}

static int assign_to_slot(const char *id) {
    VehicleNode *v = find_vehicle(id);
    if (!v) return 0;
    for (int i = 0; i < MAX_SLOTS; i++) {
        if (!slots[i].active) {
            slots[i].active = 1;
            strncpy(slots[i].id, id, sizeof(slots[i].id) - 1);
            slots[i].id[sizeof(slots[i].id) - 1] = '\0';
            slots[i].capacity = v->capacity;
            slots[i].charging_type = v->charging_type;
            slots[i].energy = 0;
            slots[i].percent = 0;
            return 1;
        }
    }
    return 0;
}

int start_charging(void) {
    int started = 0;
    while (queue_head) {
        if (!assign_to_slot(queue_head->id)) break;
        QueueNode *tmp = queue_head;
        queue_head = queue_head->next;
        if (!queue_head) queue_tail = NULL;
        free(tmp);
        started++;
    }
    return started;
}

double calculate_bill(double energy_kwh) {
    double base = energy_kwh * RATE_PER_KWH;
    return base + (base * TAX_RATE);
}

void update_charging(double minutes_step) {
    for (int i = 0; i < MAX_SLOTS; i++) {
        if (!slots[i].active) continue;
        double speed = slots[i].charging_type == 1 ? FAST_FACTOR : SLOW_FACTOR;
        double add = speed * minutes_step;
        slots[i].energy += add;
        if (slots[i].capacity > 0) {
            slots[i].percent = (slots[i].energy / slots[i].capacity) * 100.0;
        }
        if (slots[i].percent >= 100.0) {
            slots[i].percent = 100.0;
            slots[i].energy = slots[i].capacity;
            total_revenue += calculate_bill(slots[i].energy);
            slots[i].active = 0;
            slots[i].id[0] = '\0';
            slots[i].capacity = 0;
            slots[i].charging_type = 0;
            slots[i].energy = 0;
            slots[i].percent = 0;
        }
    }
    start_charging();
}

double get_total_revenue(void) { return total_revenue; }
int get_total_vehicles(void) { return total_vehicles; }

int get_active_sessions(void) {
    int active = 0;
    for (int i = 0; i < MAX_SLOTS; i++) if (slots[i].active) active++;
    return active;
}

int get_slot_count(void) { return MAX_SLOTS; }
int get_slot_status(int slot_idx) {
    if (slot_idx < 0 || slot_idx >= MAX_SLOTS) return 0;
    return slots[slot_idx].active;
}
const char *get_slot_vehicle(int slot_idx) {
    if (slot_idx < 0 || slot_idx >= MAX_SLOTS) return "";
    return slots[slot_idx].id;
}
double get_slot_energy(int slot_idx) {
    if (slot_idx < 0 || slot_idx >= MAX_SLOTS) return 0;
    return slots[slot_idx].energy;
}
double get_slot_percent(int slot_idx) {
    if (slot_idx < 0 || slot_idx >= MAX_SLOTS) return 0;
    return slots[slot_idx].percent;
}
