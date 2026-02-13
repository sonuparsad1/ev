#ifndef QUEUE_H
#define QUEUE_H

#include "vehicle.h"

typedef struct QueueNode {
    Vehicle vehicle;
    struct QueueNode *next;
} QueueNode;

typedef struct {
    QueueNode *front;
    QueueNode *rear;
    int size;
} VehicleQueue;

void queue_init(VehicleQueue *q);
int queue_enqueue(VehicleQueue *q, const Vehicle *vehicle);
int queue_dequeue(VehicleQueue *q, Vehicle *out);
int queue_is_empty(VehicleQueue *q);
void queue_clear(VehicleQueue *q);

#endif
