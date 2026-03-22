# 🏋️ Gym Management System API (FastAPI)

A complete backend system to manage **gym plans, memberships, and class bookings** built using **FastAPI**.

This project demonstrates REST API design, validation, business logic, and advanced features like filtering, sorting, and pagination.

---

## 🚀 Features

### 🧾 Plans Management

* View all plans with pricing insights
* Get plan by ID
* Create, update, and delete plans
* Filter plans by price, duration, and features
* Search plans by keyword
* Sort and paginate plans
* Advanced browse API (filter + sort + paginate)

---

### 👤 Membership System

* Enroll users into plans
* Automatic fee calculation with:

  * Duration-based discounts
  * Referral discounts
  * EMI processing fee
* Freeze and reactivate memberships
* Search, sort, and paginate memberships

---

### 🏋️ Class Booking System

* Book classes (only for eligible members)
* View all bookings
* Cancel bookings

---

## 🛠️ Tech Stack

* **Backend Framework:** FastAPI
* **Validation:** Pydantic
* **Language:** Python 3.10+
* **Server:** Uvicorn

---

## 📂 Project Structure

```
.
├── main.py        # Main FastAPI application
└── README.md      # Project documentation
```

---

## ▶️ Getting Started

### 1. Install dependencies

```bash
pip install fastapi uvicorn
```

---

### 2. Run the server

```bash
uvicorn main:app --reload
```

---

### 3. Open API Docs

* Swagger UI: http://127.0.0.1:8000/docs
* ReDoc: http://127.0.0.1:8000/redoc

---

## 📌 API Endpoints Overview

---

### 🧾 Plans

| Method | Endpoint           | Description        |
| ------ | ------------------ | ------------------ |
| GET    | `/plans`           | Get all plans      |
| GET    | `/plans/summary`   | Summary of plans   |
| GET    | `/plans/filter`    | Filter plans       |
| GET    | `/plans/search`    | Search plans       |
| GET    | `/plans/sort`      | Sort plans         |
| GET    | `/plans/page`      | Paginate plans     |
| GET    | `/plans/browse`    | Combined filtering |
| GET    | `/plans/{plan_id}` | Get plan by ID     |
| POST   | `/plans`           | Create plan        |
| PUT    | `/plans/{plan_id}` | Update plan        |
| DELETE | `/plans/{plan_id}` | Delete plan        |

---

### 👤 Memberships

| Method | Endpoint                       | Description           |
| ------ | ------------------------------ | --------------------- |
| GET    | `/memberships`                 | Get all memberships   |
| POST   | `/memberships`                 | Create membership     |
| PUT    | `/memberships/{id}/freeze`     | Freeze membership     |
| PUT    | `/memberships/{id}/reactivate` | Reactivate membership |
| GET    | `/memberships/search`          | Search memberships    |
| GET    | `/memberships/sort`            | Sort memberships      |
| GET    | `/memberships/page`            | Paginate memberships  |

---

### 🏋️ Classes

| Method | Endpoint               | Description      |
| ------ | ---------------------- | ---------------- |
| POST   | `/classes/book`        | Book a class     |
| GET    | `/classes/bookings`    | Get all bookings |
| DELETE | `/classes/cancel/{id}` | Cancel booking   |

---

## 💡 Business Logic

### 💰 Fee Calculation

Membership cost is calculated based on:

* **10% discount** → for duration ≥ 6 months
* **20% discount** → for duration ≥ 12 months
* **Extra 5% discount** → if referral code is used
* **₹200 processing fee** → for EMI payments

---

### 📊 Example Fee Breakdown

```json
{
  "base_price": 8980,
  "duration_discount": 0.2,
  "referral_discount": 0.05,
  "processing_fee": 200,
  "total": 7184
}
```

---

## ⚠️ Validations

* `member_name` → minimum 2 characters
* `phone` → minimum 10 digits
* `plan_id` → must be valid
* Duplicate plan names are not allowed
* Cannot delete plan with active memberships
* Class booking allowed only if:

  * Membership is active
  * Plan includes classes

---

## 🧪 Sample Request

### Create Membership

```json
POST /memberships

{
  "member_name": "Dilip",
  "plan_id": 4,
  "phone": "9876543210",
  "start_month": "March",
  "payment_mode": "emi",
  "referral_code": "FIT50"
}
```

---

## 📈 Advanced Features

* 🔍 Search functionality
* 🔃 Sorting (multiple fields)
* 📄 Pagination
* 🔗 Combined filtering (browse API)
* ✅ Strong validation using Pydantic
* ⚡ Fast performance with FastAPI

---

## 🧠 Key Learnings

* REST API design with FastAPI
* Data validation using Pydantic
* Business logic implementation
* CRUD operations
* Query parameters handling
* Pagination, filtering, and sorting
* Error handling and HTTP exceptions

---

## 🎯 Future Improvements

* Database integration (PostgreSQL / MongoDB)
* Authentication (JWT)
* Admin dashboard
* Payment gateway integration
* Deployment on cloud (AWS / Render)

---

## 👨‍💻 Author

**Dilip**
