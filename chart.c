#include "chart.h"
#include "storage.h"
#include <stdio.h>
#include <string.h>

void chart_draw_revenue(HDC hdc, RECT rc) {
    float totalRevenue = storage_get_total_revenue();
    int totalSessions = storage_get_total_sessions();
    int margin = 40;
    int chartHeight = (rc.bottom - rc.top) - 120;
    int baseY = rc.top + margin + chartHeight;
    int barW = 80;
    int x1 = rc.left + 70;
    int barH = (int)(totalRevenue > 0 ? (totalRevenue > 5000 ? chartHeight : (totalRevenue / 5000.0f) * chartHeight) : 0);
    char buf[128];

    Rectangle(hdc, rc.left + margin, rc.top + margin, rc.right - margin, rc.bottom - margin);
    MoveToEx(hdc, rc.left + margin + 20, baseY, NULL);
    LineTo(hdc, rc.right - margin - 20, baseY);
    MoveToEx(hdc, rc.left + margin + 20, baseY, NULL);
    LineTo(hdc, rc.left + margin + 20, rc.top + margin + 20);

    Rectangle(hdc, x1, baseY - barH, x1 + barW, baseY);
    TextOutA(hdc, x1, baseY + 10, "Revenue", 7);

    sprintf(buf, "Total Sessions: %d", totalSessions);
    TextOutA(hdc, rc.left + 60, rc.bottom - 60, buf, (int)strlen(buf));
    sprintf(buf, "Total Revenue: %.2f", totalRevenue);
    TextOutA(hdc, rc.left + 60, rc.bottom - 40, buf, (int)strlen(buf));
}
