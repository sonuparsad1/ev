#include "queue.h"
#include <stdlib.h>

void queue_init(VehicleQueue *q) {
    q->front = q->rear = NULL;
    q->size = 0;
}

int queue_enqueue(VehicleQueue *q, const Vehicle *vehicle) {
    QueueNode *node = (QueueNode*)malloc(sizeof(QueueNode));
    if (!node) return 0;
    node->vehicle = *vehicle;
    node->next = NULL;
    if (q->rear) q->rear->next = node;
    else q->front = node;
    q->rear = node;
    q->size++;
    return 1;
}

int queue_dequeue(VehicleQueue *q, Vehicle *out) {
    QueueNode *tmp;
    if (!q->front) return 0;
    tmp = q->front;
    if (out) *out = tmp->vehicle;
    q->front = tmp->next;
    if (!q->front) q->rear = NULL;
    free(tmp);
    q->size--;
    return 1;
}

int queue_is_empty(VehicleQueue *q) { return q->front == NULL; }

void queue_clear(VehicleQueue *q) {
    Vehicle dummy;
    while (queue_dequeue(q, &dummy));
}
