#include "billing.h"

#define RATE_PER_KWH 15.0f

Bill billing_calculate(float batteryCapacity, float chargedPercent) {
    Bill b;
    b.energy = batteryCapacity * (chargedPercent / 100.0f);
    b.baseCost = b.energy * RATE_PER_KWH;
    b.tax = b.baseCost * 0.05f;
    b.total = b.baseCost + b.tax;
    return b;
}
