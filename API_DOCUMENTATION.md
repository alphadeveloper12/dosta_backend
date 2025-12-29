# Dosta Backend API Documentation

This document provides a comprehensive overview of the available APIs in the Dosta Backend, grouped by their respective applications: **Vending**, **Catering**, and **Kitchen**.

## Base URL

`/api/`

---

## 1. Vending API

**Base URL:** `/api/vending/`

These endpoints manage the vending machine ordering flow, including location selection, menu browsing, cart management, and order placement.

### **Locations**

#### `GET /api/vending/locations/`

- **Description:** Retrieves a list of all vending locations.
- **Parameters:**
  - `active` (optional, boolean): Set to `true` to return only active locations.
  - `ids` (optional, string): Comma-separated list of IDs to filter (e.g., `1,2,3`).
  - `search` (optional, string): Search by name or info.
- **Response:** List of location objects `{ id, name, info, hours, position: {lat, lng}, ... }`.

### **Ordering Workflow**

#### `GET /api/vending/plan-types/`

- **Description:** Returns available overarching plan types (e.g., Order Now, Start a Plan).
- **Response:**
  - `options`: List of `{ key, label }`.
  - `next_step`: Hint for the next step (e.g., `"pickup_options"`).

#### `GET /api/vending/pickup-options/`

- **Description:** Returns pickup timing options for a specific location.
- **Parameters:**
  - `location_id` (required): ID of the selected location.
- **Response:**
  - `pickup_types`: List of `{ key, label }` (e.g., Today, In 24 Hours).
  - `time_slots`: List of available time slots.
  - `next_step`: `"choose_menu"`.

#### `GET /api/vending/menu/<plan_type>/`

- **Description:** Fetches the menu for "Order Now" or "Smart Grab" modes.
- **Parameters:**
  - `day` (optional): Filter by day of week (e.g., `Monday`).
- **Response:**
  - `menus`: List of menu objects with items.
  - `next_step`: `"confirm_order"`.

#### `GET /api/vending/plan-options/`

- **Description:** Returns subtypes for "Start a Plan" (Weekly vs Monthly).
- **Response:** `plan_subtypes` list.

#### `GET /api/vending/menu/plan/<subtype>/`

- **Description:** Fetches the structured menu for Weekly or Monthly plans.
- **Parameters:**
  - `subtype`: `WEEKLY` or `MONTHLY`.
- **Response:**
  - For `WEEKLY`: Nested object keyed by day (`Monday`, `Tuesday`...).
  - For `MONTHLY`: List of weeks, each containing a day-keyed menu object.

### **Cart Management**

#### `GET /api/vending/cart/`

- **Description:** Retrieves the current user's active cart (items + plan details).
- **Response:** Cart object with `items`, `total_price`, etc.

#### `POST /api/vending/cart/`

- **Description:** Syncs the cart state. Replaces existing items with the new list and updates plan context.
- **Body:** Same structure as `order/confirm/` (see below).
  ```json
  {
      "location_id": 1,
      "plan_type": "ORDER_NOW",
      "items": [...]
  }
  ```

### **Management**

#### `GET /api/vending/saved-plans/`

- **Description:** Retrieves saved meal plans for the authenticated user.
- **Response:** List of saved plans.

#### `POST /api/vending/order/confirm/`

- **Description:** Creates a new order.
- **Body:**
  ```json
  {
   "location_id": 1,
   "plan_type": "ORDER_NOW",
   "plan_subtype": "NONE",
   "pickup_type": "TODAY",
   "pickup_date": "YYYY-MM-DD",
   "pickup_slot_id": 3,
   "items": [{ "menu_item_id": 2, "quantity": 1, "day_of_week": "Monday" }]
  }
  ```
- **Response:** Created order object.

#### `GET /api/vending/order/progress/`

- **Description:** Tracks the status of an active order.
- **Parameters:** `order_id` (required).
- **Response:** Order status, current step, and next step hint.

#### `PATCH /api/vending/order/progress/`

- **Description:** Updates the current step of an order.
- **Body:** `{ "order_id": 1, "current_step": 4 }`

---

## 2. Catering API

**Base URL:** `/api/catering/`

These endpoints provide metadata for the catering booking form. **All endpoints require authentication.**

#### `GET /api/catering/event-types/`

- **Description:** List of event types (e.g., Wedding, Corporate).

#### `GET /api/catering/provider-types/`

- **Description:** List of provider types (e.g., Buffet, Plated).

#### `GET /api/catering/service-styles/`

- **Description:** List of service styles.

#### `GET /api/catering/cuisines/`

- **Description:** List of available cuisines.

#### `GET /api/catering/courses/`

- **Description:** List of courses (Appetizer, Main, etc.).

#### `GET /api/catering/locations/`

- **Description:** List of available catering locations.

#### `GET /api/catering/budget-options/`

- **Description:** List of budget ranges.

---

## 3. Kitchen API

**Base URL:** `/kitchen/`

These endpoints are used by the Kitchen Dashboard to manage order preparation.

#### `GET /kitchen/`

- **Description:** Renders the Kitchen Dashboard HTML page showing orders with status `PENDING`, `PREPARING`, or `READY`.

#### `GET /kitchen/api/active-orders/`

- **Description:** Returns a lightweight JSON list of active order IDs and statuses. Used for polling to update the dashboard in real-time.

#### `POST /kitchen/order/<id>/update-status/`

- **Description:** Updates the status of an order (e.g., from `PENDING` to `PREPARING`).
- **Body:** Form data `status=<NEW_STATUS>`.

#### `POST /kitchen/menu-upload/`

- **Description:** Endpoint to upload menu data via CSV or Excel.
- **Body:** Multipart form data with file field `menu_file`.
