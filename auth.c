#include "auth.h"
#include "vehicle.h"
#include <string.h>

#define ADMIN_USERNAME "admin"
#define ADMIN_PASSWORD "admin123"

int auth_validate(const char *username, const char *password) {
    Vehicle arr[MAX_VEHICLES];

    if (strcmp(username, ADMIN_USERNAME) == 0 && strcmp(password, ADMIN_PASSWORD) == 0) {
        return 1;
    }
    int n = vehicle_load_all(arr, MAX_VEHICLES);
    int i;
    for (i = 0; i < n; i++) {
        if (strcmp(arr[i].owner, username) == 0 && strcmp(arr[i].vehicleNo, password) == 0) {
            return 1;
        }
    }
    return 0;
}
