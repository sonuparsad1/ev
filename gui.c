#include "gui.h"
#include "auth.h"
#include "vehicle.h"
#include "queue.h"
#include "charging.h"
#include "storage.h"
#include "chart.h"

#include <windows.h>
#include <commctrl.h>
#include <stdio.h>
#include <stdlib.h>

#pragma comment(lib, "comctl32.lib")

HINSTANCE g_hInst;

#define IDC_USERNAME 1001
#define IDC_PASSWORD 1002
#define IDC_LOGIN_BTN 1003

#define IDC_SIDEBAR_REGISTER 2001
#define IDC_SIDEBAR_VIEW 2002
#define IDC_SIDEBAR_QUEUE 2003
#define IDC_SIDEBAR_REVENUE 2004
#define IDC_SIDEBAR_LOGOUT 2005

#define IDC_REG_OWNER 3001
#define IDC_REG_VNO 3002
#define IDC_REG_BATTERY 3003
#define IDC_REG_TYPE 3004
#define IDC_REG_SUBMIT 3005

#define IDC_QUEUE_INPUT 4001
#define IDC_QUEUE_ADD 4002
#define IDC_QUEUE_LIST 4003

#define IDC_VEHICLE_LIST 5001

static int g_loginAttempts = 0;
static HWND g_mainWnd;
static HWND g_cards[SLOT_COUNT][4];
static HWND g_metrics[4];
static HWND g_panel;
static HWND g_queueList;
static VehicleQueue g_queue;

static void set_default_font(HWND h) {
    SendMessage(h, WM_SETFONT, (WPARAM)GetStockObject(DEFAULT_GUI_FONT), TRUE);
}

static void refresh_dashboard_metrics(void) {
    char buf[128];
    Vehicle arr[MAX_VEHICLES];
    int vCount = vehicle_load_all(arr, MAX_VEHICLES);

    sprintf(buf, "Total Vehicles: %d", vCount);
    SetWindowTextA(g_metrics[0], buf);
    sprintf(buf, "Active Sessions: %d", charging_active_sessions());
    SetWindowTextA(g_metrics[1], buf);
    sprintf(buf, "Total Revenue: %.2f", storage_get_total_revenue());
    SetWindowTextA(g_metrics[2], buf);
    sprintf(buf, "Available Slots: %d", charging_available_slots());
    SetWindowTextA(g_metrics[3], buf);
}

static void refresh_slot_cards(void) {
    ChargingSlot *slots = charging_get_slots();
    int i;
    char buf[128];
    for (i = 0; i < SLOT_COUNT; i++) {
        sprintf(buf, "Slot %d", slots[i].id);
        SetWindowTextA(g_cards[i][0], buf);
        sprintf(buf, "Status: %s", slots[i].active ? "Charging" : "Available");
        SetWindowTextA(g_cards[i][1], buf);
        sprintf(buf, "Vehicle: %s", slots[i].active ? slots[i].vehicle.vehicleNo : "-");
        SetWindowTextA(g_cards[i][2], buf);
        SendMessage(g_cards[i][3], PBM_SETPOS, slots[i].progress, 0);
    }
}

static void assign_queue_to_slots(void) {
    Vehicle v;
    while (!queue_is_empty(&g_queue) && charging_available_slots() > 0) {
        if (queue_dequeue(&g_queue, &v)) charging_assign_vehicle(&v);
    }
    if (g_queueList) {
        SendMessageA(g_queueList, LB_RESETCONTENT, 0, 0);
        QueueNode *n = g_queue.front;
        while (n) {
            SendMessageA(g_queueList, LB_ADDSTRING, 0, (LPARAM)n->vehicle.vehicleNo);
            n = n->next;
        }
    }
}

static void show_registration_form(HWND parent) {
    HWND dlg = CreateWindowExA(WS_EX_DLGMODALFRAME, "STATIC", "Register Vehicle",
        WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU | WS_VISIBLE,
        300, 200, 360, 280, parent, NULL, g_hInst, NULL);
    HWND owner = CreateWindowA("EDIT", "", WS_CHILD | WS_VISIBLE | WS_BORDER, 140, 30, 180, 24, dlg, (HMENU)IDC_REG_OWNER, g_hInst, NULL);
    HWND vno = CreateWindowA("EDIT", "", WS_CHILD | WS_VISIBLE | WS_BORDER, 140, 65, 180, 24, dlg, (HMENU)IDC_REG_VNO, g_hInst, NULL);
    HWND battery = CreateWindowA("EDIT", "", WS_CHILD | WS_VISIBLE | WS_BORDER, 140, 100, 180, 24, dlg, (HMENU)IDC_REG_BATTERY, g_hInst, NULL);
    HWND type = CreateWindowA("COMBOBOX", "", WS_CHILD | WS_VISIBLE | CBS_DROPDOWNLIST, 140, 135, 180, 100, dlg, (HMENU)IDC_REG_TYPE, g_hInst, NULL);
    HWND submit = CreateWindowA("BUTTON", "Submit", WS_CHILD | WS_VISIBLE, 140, 180, 100, 28, dlg, (HMENU)IDC_REG_SUBMIT, g_hInst, NULL);

    CreateWindowA("STATIC", "Owner Name:", WS_CHILD | WS_VISIBLE, 20, 30, 100, 24, dlg, NULL, g_hInst, NULL);
    CreateWindowA("STATIC", "Vehicle Number:", WS_CHILD | WS_VISIBLE, 20, 65, 100, 24, dlg, NULL, g_hInst, NULL);
    CreateWindowA("STATIC", "Battery (kWh):", WS_CHILD | WS_VISIBLE, 20, 100, 100, 24, dlg, NULL, g_hInst, NULL);
    CreateWindowA("STATIC", "Charging Type:", WS_CHILD | WS_VISIBLE, 20, 135, 100, 24, dlg, NULL, g_hInst, NULL);
    SendMessageA(type, CB_ADDSTRING, 0, (LPARAM)"Slow");
    SendMessageA(type, CB_ADDSTRING, 0, (LPARAM)"Fast");
    SendMessageA(type, CB_SETCURSEL, 0, 0);

    set_default_font(owner); set_default_font(vno); set_default_font(battery); set_default_font(type); set_default_font(submit);
}

static void show_vehicle_list(HWND parent) {
    HWND dlg = CreateWindowExA(WS_EX_DLGMODALFRAME, WC_LISTVIEWA, "",
        WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU | WS_VISIBLE | LVS_REPORT,
        220, 130, 620, 380, parent, (HMENU)IDC_VEHICLE_LIST, g_hInst, NULL);
    LVCOLUMNA col = {0};
    LVITEMA item = {0};
    Vehicle arr[MAX_VEHICLES];
    int i, n;

    SetWindowTextA(dlg, "Registered Vehicles");
    ListView_SetExtendedListViewStyle(dlg, LVS_EX_FULLROWSELECT | LVS_EX_GRIDLINES);

    col.mask = LVCF_TEXT | LVCF_WIDTH;
    col.cx = 140; col.pszText = "Owner Name"; ListView_InsertColumn(dlg, 0, &col);
    col.cx = 140; col.pszText = "Vehicle Number"; ListView_InsertColumn(dlg, 1, &col);
    col.cx = 120; col.pszText = "Battery"; ListView_InsertColumn(dlg, 2, &col);
    col.cx = 120; col.pszText = "Status"; ListView_InsertColumn(dlg, 3, &col);

    n = vehicle_load_all(arr, MAX_VEHICLES);
    for (i = 0; i < n; i++) {
        char battery[32];
        item.mask = LVIF_TEXT;
        item.iItem = i;
        item.iSubItem = 0;
        item.pszText = arr[i].owner;
        ListView_InsertItem(dlg, &item);
        ListView_SetItemText(dlg, i, 1, arr[i].vehicleNo);
        sprintf(battery, "%.2f", arr[i].batteryCapacity);
        ListView_SetItemText(dlg, i, 2, battery);
        ListView_SetItemText(dlg, i, 3, arr[i].status);
    }
}

static void show_queue_window(HWND parent) {
    HWND dlg = CreateWindowExA(WS_EX_DLGMODALFRAME, "STATIC", "Queue Management",
        WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU | WS_VISIBLE,
        260, 160, 420, 320, parent, NULL, g_hInst, NULL);
    HWND input = CreateWindowA("EDIT", "", WS_CHILD | WS_VISIBLE | WS_BORDER, 20, 30, 200, 24, dlg, (HMENU)IDC_QUEUE_INPUT, g_hInst, NULL);
    HWND add = CreateWindowA("BUTTON", "Add to Queue", WS_CHILD | WS_VISIBLE, 240, 30, 140, 24, dlg, (HMENU)IDC_QUEUE_ADD, g_hInst, NULL);
    g_queueList = CreateWindowA("LISTBOX", "", WS_CHILD | WS_VISIBLE | WS_BORDER | LBS_NOTIFY, 20, 70, 360, 180, dlg, (HMENU)IDC_QUEUE_LIST, g_hInst, NULL);
    set_default_font(input); set_default_font(add); set_default_font(g_queueList);
}

static LRESULT CALLBACK RevenueWndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    PAINTSTRUCT ps;
    HDC hdc;
    RECT rc;
    switch (msg) {
        case WM_PAINT:
            hdc = BeginPaint(hwnd, &ps);
            GetClientRect(hwnd, &rc);
            chart_draw_revenue(hdc, rc);
            EndPaint(hwnd, &ps);
            return 0;
    }
    return DefWindowProc(hwnd, msg, wParam, lParam);
}

static void show_revenue_window(HWND parent) {
    WNDCLASSA wc = {0};
    wc.lpfnWndProc = RevenueWndProc;
    wc.hInstance = g_hInst;
    wc.lpszClassName = "RevenueWndClass";
    wc.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
    RegisterClassA(&wc);
    CreateWindowA("RevenueWndClass", "Revenue Report", WS_OVERLAPPEDWINDOW | WS_VISIBLE,
        280, 160, 600, 420, parent, NULL, g_hInst, NULL);
}

static void build_dashboard(HWND hwnd) {
    int i;
    CreateWindowA("STATIC", "EV Charging Station Dashboard", WS_CHILD | WS_VISIBLE,
        220, 10, 350, 24, hwnd, NULL, g_hInst, NULL);

    for (i = 0; i < 4; i++) {
        g_metrics[i] = CreateWindowA("STATIC", "", WS_CHILD | WS_VISIBLE | SS_CENTER | WS_BORDER,
            220 + i * 180, 40, 170, 40, hwnd, NULL, g_hInst, NULL);
    }

    CreateWindowA("BUTTON", "Register Vehicle", WS_CHILD | WS_VISIBLE, 20, 40, 170, 34, hwnd, (HMENU)IDC_SIDEBAR_REGISTER, g_hInst, NULL);
    CreateWindowA("BUTTON", "View Vehicles", WS_CHILD | WS_VISIBLE, 20, 85, 170, 34, hwnd, (HMENU)IDC_SIDEBAR_VIEW, g_hInst, NULL);
    CreateWindowA("BUTTON", "Add to Queue", WS_CHILD | WS_VISIBLE, 20, 130, 170, 34, hwnd, (HMENU)IDC_SIDEBAR_QUEUE, g_hInst, NULL);
    CreateWindowA("BUTTON", "Revenue Report", WS_CHILD | WS_VISIBLE, 20, 175, 170, 34, hwnd, (HMENU)IDC_SIDEBAR_REVENUE, g_hInst, NULL);
    CreateWindowA("BUTTON", "Logout", WS_CHILD | WS_VISIBLE, 20, 220, 170, 34, hwnd, (HMENU)IDC_SIDEBAR_LOGOUT, g_hInst, NULL);

    g_panel = CreateWindowA("STATIC", "", WS_CHILD | WS_VISIBLE | WS_BORDER, 220, 100, 740, 420, hwnd, NULL, g_hInst, NULL);

    for (i = 0; i < SLOT_COUNT; i++) {
        int x = 240 + (i % 2) * 360;
        int y = 120 + (i / 2) * 190;
        CreateWindowA("BUTTON", "", WS_CHILD | WS_VISIBLE | BS_GROUPBOX, x, y, 330, 170, hwnd, NULL, g_hInst, NULL);
        g_cards[i][0] = CreateWindowA("STATIC", "", WS_CHILD | WS_VISIBLE, x + 20, y + 30, 220, 20, hwnd, NULL, g_hInst, NULL);
        g_cards[i][1] = CreateWindowA("STATIC", "", WS_CHILD | WS_VISIBLE, x + 20, y + 55, 220, 20, hwnd, NULL, g_hInst, NULL);
        g_cards[i][2] = CreateWindowA("STATIC", "", WS_CHILD | WS_VISIBLE, x + 20, y + 80, 220, 20, hwnd, NULL, g_hInst, NULL);
        g_cards[i][3] = CreateWindowExA(0, PROGRESS_CLASSA, "", WS_CHILD | WS_VISIBLE, x + 20, y + 110, 280, 22, hwnd, NULL, g_hInst, NULL);
        SendMessage(g_cards[i][3], PBM_SETRANGE, 0, MAKELPARAM(0, 100));
    }

    refresh_dashboard_metrics();
    refresh_slot_cards();
    SetTimer(hwnd, 1, 1000, NULL);
}

static LRESULT CALLBACK MainWndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    switch (msg) {
        case WM_CREATE:
            g_mainWnd = hwnd;
            queue_init(&g_queue);
            charging_init_slots();
            build_dashboard(hwnd);
            return 0;
        case WM_TIMER:
            charging_tick(hwnd);
            assign_queue_to_slots();
            refresh_slot_cards();
            refresh_dashboard_metrics();
            return 0;
        case WM_COMMAND:
            switch (LOWORD(wParam)) {
                case IDC_SIDEBAR_REGISTER:
                    show_registration_form(hwnd);
                    break;
                case IDC_SIDEBAR_VIEW:
                    show_vehicle_list(hwnd);
                    break;
                case IDC_SIDEBAR_QUEUE:
                    show_queue_window(hwnd);
                    break;
                case IDC_SIDEBAR_REVENUE:
                    show_revenue_window(hwnd);
                    break;
                case IDC_SIDEBAR_LOGOUT:
                    ShowWindow(hwnd, SW_HIDE);
                    PostQuitMessage(0);
                    break;
                case IDC_REG_SUBMIT: {
                    char owner[64], vno[32], bat[32], type[16];
                    GetWindowTextA(GetDlgItem(GetParent((HWND)lParam), IDC_REG_OWNER), owner, sizeof(owner));
                    GetWindowTextA(GetDlgItem(GetParent((HWND)lParam), IDC_REG_VNO), vno, sizeof(vno));
                    GetWindowTextA(GetDlgItem(GetParent((HWND)lParam), IDC_REG_BATTERY), bat, sizeof(bat));
                    GetWindowTextA(GetDlgItem(GetParent((HWND)lParam), IDC_REG_TYPE), type, sizeof(type));
                    if (vehicle_register(owner, vno, (float)atof(bat), type)) {
                        MessageBoxA(hwnd, "Vehicle registered successfully. Password is Vehicle Number.", "Success", MB_OK | MB_ICONINFORMATION);
                    } else {
                        MessageBoxA(hwnd, "Unable to save vehicle.", "Error", MB_OK | MB_ICONERROR);
                    }
                    refresh_dashboard_metrics();
                    break;
                }
                case IDC_QUEUE_ADD: {
                    char vno[32];
                    Vehicle v;
                    GetWindowTextA(GetDlgItem(GetParent((HWND)lParam), IDC_QUEUE_INPUT), vno, sizeof(vno));
                    if (vehicle_find_by_no(vno, &v)) {
                        queue_enqueue(&g_queue, &v);
                        assign_queue_to_slots();
                        refresh_dashboard_metrics();
                        refresh_slot_cards();
                    } else {
                        MessageBoxA(hwnd, "Vehicle not found.", "Queue", MB_OK | MB_ICONWARNING);
                    }
                    break;
                }
            }
            return 0;
        case WM_DESTROY:
            KillTimer(hwnd, 1);
            queue_clear(&g_queue);
            PostQuitMessage(0);
            return 0;
    }
    return DefWindowProc(hwnd, msg, wParam, lParam);
}

static LRESULT CALLBACK LoginWndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    switch (msg) {
        case WM_CREATE:
            CreateWindowA("STATIC", "Username:", WS_CHILD | WS_VISIBLE, 40, 40, 80, 24, hwnd, NULL, g_hInst, NULL);
            CreateWindowA("EDIT", "", WS_CHILD | WS_VISIBLE | WS_BORDER, 130, 40, 170, 24, hwnd, (HMENU)IDC_USERNAME, g_hInst, NULL);
            CreateWindowA("STATIC", "Password:", WS_CHILD | WS_VISIBLE, 40, 80, 80, 24, hwnd, NULL, g_hInst, NULL);
            CreateWindowA("EDIT", "", WS_CHILD | WS_VISIBLE | WS_BORDER | ES_PASSWORD, 130, 80, 170, 24, hwnd, (HMENU)IDC_PASSWORD, g_hInst, NULL);
            CreateWindowA("BUTTON", "Login", WS_CHILD | WS_VISIBLE, 130, 125, 100, 28, hwnd, (HMENU)IDC_LOGIN_BTN, g_hInst, NULL);
            return 0;
        case WM_COMMAND:
            if (LOWORD(wParam) == IDC_LOGIN_BTN) {
                char user[64], pass[32];
                GetWindowTextA(GetDlgItem(hwnd, IDC_USERNAME), user, sizeof(user));
                GetWindowTextA(GetDlgItem(hwnd, IDC_PASSWORD), pass, sizeof(pass));
                if (auth_validate(user, pass)) {
                    HWND dash;
                    WNDCLASSA wc = {0};
                    wc.lpfnWndProc = MainWndProc;
                    wc.hInstance = g_hInst;
                    wc.lpszClassName = "EVMainWindow";
                    wc.hbrBackground = (HBRUSH)(COLOR_BTNFACE + 1);
                    RegisterClassA(&wc);
                    dash = CreateWindowA("EVMainWindow", "EV Charging Station Management", WS_OVERLAPPEDWINDOW | WS_VISIBLE,
                        100, 50, 1000, 600, NULL, NULL, g_hInst, NULL);
                    ShowWindow(dash, SW_SHOW);
                    DestroyWindow(hwnd);
                } else {
                    g_loginAttempts++;
                    if (g_loginAttempts >= 3) {
                        MessageBoxA(hwnd, "Too many failed attempts.", "Authentication", MB_OK | MB_ICONERROR);
                        PostQuitMessage(0);
                    } else {
                        MessageBoxA(hwnd, "Invalid credentials. Password should be Vehicle Number.", "Authentication", MB_OK | MB_ICONWARNING);
                    }
                }
            }
            return 0;
        case WM_DESTROY:
            return 0;
    }
    return DefWindowProc(hwnd, msg, wParam, lParam);
}

int gui_run(HINSTANCE hInst) {
    MSG msg;
    HWND hwnd;
    WNDCLASSA wc = {0};
    INITCOMMONCONTROLSEX ic = { sizeof(ic), ICC_PROGRESS_CLASS | ICC_LISTVIEW_CLASSES };
    InitCommonControlsEx(&ic);
    g_hInst = hInst;

    wc.lpfnWndProc = LoginWndProc;
    wc.hInstance = hInst;
    wc.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
    wc.lpszClassName = "EVLoginWindow";
    wc.hCursor = LoadCursor(NULL, IDC_ARROW);
    RegisterClassA(&wc);

    hwnd = CreateWindowA("EVLoginWindow", "EV Charging Login", WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU | WS_VISIBLE,
        450, 220, 370, 230, NULL, NULL, hInst, NULL);

    ShowWindow(hwnd, SW_SHOW);
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }
    return (int)msg.wParam;
}
