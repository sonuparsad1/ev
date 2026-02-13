#ifndef CORE_H
#define CORE_H

#ifdef __cplusplus
extern "C" {
#endif

void register_vehicle(const char *vehicle_id, double capacity_kwh, int charging_type);
int enqueue_vehicle(const char *vehicle_id);
int start_charging(void);
void update_charging(double minutes_step);
double calculate_bill(double energy_kwh);
double get_total_revenue(void);
int get_total_vehicles(void);
int get_active_sessions(void);
int get_slot_count(void);
int get_slot_status(int slot_idx);
const char *get_slot_vehicle(int slot_idx);
double get_slot_energy(int slot_idx);
double get_slot_percent(int slot_idx);

#ifdef __cplusplus
}
#endif

#endif
