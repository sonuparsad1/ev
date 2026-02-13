#ifndef BILLING_H
#define BILLING_H

typedef struct {
    float energy;
    float baseCost;
    float tax;
    float total;
} Bill;

Bill billing_calculate(float batteryCapacity, float chargedPercent);

#endif
