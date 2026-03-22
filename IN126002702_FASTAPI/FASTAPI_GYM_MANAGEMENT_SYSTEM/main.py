from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
import math

app = FastAPI()

plans = [
    {"id": 1, "name": "Basic", "duration_months": 1, "price": 1090, "includes_classes": False, "includes_trainer": False},
    {"id": 2, "name": "Standard", "duration_months": 3, "price": 2100, "includes_classes": True, "includes_trainer": False},
    {"id": 3, "name": "Premium", "duration_months": 6, "price": 6150, "includes_classes": True, "includes_trainer": True},
    {"id": 4, "name": "Elite", "duration_months": 12, "price": 8980, "includes_classes": True, "includes_trainer": True},
    {"id": 5, "name": "Pro", "duration_months": 9, "price": 7510, "includes_classes": True, "includes_trainer": False},
]

memberships = []
membership_counter = 1

class_bookings = []
class_counter = 1

class EnrollRequest(BaseModel):
    member_name: str = Field(..., min_length=2)
    plan_id: int = Field(..., gt=0)
    phone: str = Field(..., min_length=10)
    start_month: str = Field(..., min_length=3)
    payment_mode: str = "cash"
    referral_code: str = ""

class NewPlan(BaseModel):
    name: str = Field(..., min_length=2)
    duration_months: int = Field(..., gt=0)
    price: int = Field(..., gt=0)
    includes_classes: bool = False
    includes_trainer: bool = False

class ClassBooking(BaseModel):
    member_name: str
    class_name: str
    class_date: str


def find_plan(plan_id: int):
    for plan in plans:
        if plan["id"] == plan_id:
            return plan
    return None

def calculate_membership_fee(base_price, duration, payment_mode, referral_code=""):
    discount = 0

    if duration >= 12:
        discount += 0.20
    elif duration >= 6:
        discount += 0.10

    discounted_price = base_price * (1 - discount)

    referral_discount = 0
    if referral_code:
        referral_discount = 0.05
        discounted_price *= (1 - referral_discount)

    processing_fee = 200 if payment_mode == "emi" else 0

    total = int(discounted_price + processing_fee)

    return {
        "base_price": base_price,
        "duration_discount": discount,
        "referral_discount": referral_discount,
        "processing_fee": processing_fee,
        "total": total
    }

def filter_plans_logic(max_price, max_duration, includes_classes, includes_trainer):
    result = plans

    if max_price is not None:
        result = [p for p in result if p["price"] <= max_price]

    if max_duration is not None:
        result = [p for p in result if p["duration_months"] <= max_duration]

    if includes_classes is not None:
        result = [p for p in result if p["includes_classes"] == includes_classes]

    if includes_trainer is not None:
        result = [p for p in result if p["includes_trainer"] == includes_trainer]

    return result

@app.get("/")
def home():
    return {"message": "Welcome to CultFit Gym"}

@app.get("/plans")
def get_plans():
    prices = [p["price"] for p in plans]
    return {
        "plans": plans,
        "total": len(plans),
        "min_price": min(prices),
        "max_price": max(prices)
    }

@app.get("/plans/summary")
def plans_summary():
    cheapest = min(plans, key=lambda x: x["price"])
    expensive = max(plans, key=lambda x: x["price"])

    return {
        "total": len(plans),
        "with_classes": sum(p["includes_classes"] for p in plans),
        "with_trainer": sum(p["includes_trainer"] for p in plans),
        "cheapest": cheapest,
        "most_expensive": expensive
    }



@app.get("/plans/filter")
def filter_plans(
    max_price: Optional[int] = None,
    max_duration: Optional[int] = None,
    includes_classes: Optional[bool] = None,
    includes_trainer: Optional[bool] = None
):
    return filter_plans_logic(max_price, max_duration, includes_classes, includes_trainer)

@app.post("/plans", status_code=201)
def create_plan(new_plan: NewPlan):
    if any(p["name"].lower() == new_plan.name.lower() for p in plans):
        raise HTTPException(400, "Duplicate plan name")

    new_id = max(p["id"] for p in plans) + 1
    plan = {"id": new_id, **new_plan.dict()}
    plans.append(plan)
    return plan

@app.put("/plans/{plan_id}")
def update_plan(plan_id: int,
                price: Optional[int] = None,
                includes_classes: Optional[bool] = None,
                includes_trainer: Optional[bool] = None):

    plan = find_plan(plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")

    if price is not None:
        plan["price"] = price
    if includes_classes is not None:
        plan["includes_classes"] = includes_classes
    if includes_trainer is not None:
        plan["includes_trainer"] = includes_trainer

    return plan

@app.delete("/plans/{plan_id}")
def delete_plan(plan_id: int):
    plan = find_plan(plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")

    for m in memberships:
        if m["plan_id"] == plan_id and m["status"] == "active":
            raise HTTPException(400, "Active memberships exist")

    plans.remove(plan)
    return {"message": "Deleted"}
@app.get("/memberships")
def get_memberships():
    return {"memberships": memberships, "total": len(memberships)}

@app.post("/memberships")
def create_membership(req: EnrollRequest):
    global membership_counter

    plan = find_plan(req.plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")

    fee_data = calculate_membership_fee(
        plan["price"],
        plan["duration_months"],
        req.payment_mode,
        req.referral_code
    )

    membership = {
        "membership_id": membership_counter,
        "member_name": req.member_name,
        "plan_id": plan["id"],
        "plan_name": plan["name"],
        "duration": plan["duration_months"],
        "monthly_cost": fee_data["total"] // plan["duration_months"],
        "total_fee": fee_data["total"],
        "discount_breakdown": fee_data,
        "status": "active"
    }

    memberships.append(membership)
    membership_counter += 1

    return membership

@app.put("/memberships/{membership_id}/freeze")
def freeze_membership(membership_id: int):
    for m in memberships:
        if m["membership_id"] == membership_id:
            m["status"] = "frozen"
            return m
    raise HTTPException(404, "Not found")

@app.put("/memberships/{membership_id}/reactivate")
def reactivate_membership(membership_id: int):
    for m in memberships:
        if m["membership_id"] == membership_id:
            m["status"] = "active"
            return m
    raise HTTPException(404, "Not found")

@app.post("/classes/book")
def book_class(req: ClassBooking):
    global class_counter

    active_member = any(
        m["member_name"] == req.member_name and
        m["status"] == "active" and
        find_plan(m["plan_id"])["includes_classes"]
        for m in memberships
    )

    if not active_member:
        raise HTTPException(400, "No valid membership with classes")

    booking = {
        "booking_id": class_counter,
        **req.dict()
    }

    class_bookings.append(booking)
    class_counter += 1

    return booking

@app.get("/classes/bookings")
def get_bookings():
    return class_bookings

@app.delete("/classes/cancel/{booking_id}")
def cancel_booking(booking_id: int):
    for b in class_bookings:
        if b["booking_id"] == booking_id:
            class_bookings.remove(b)
            return {"message": "Cancelled"}
    raise HTTPException(404, "Not found")

@app.get("/memberships/search")
def search_memberships(member_name: str):
    result = [
        m for m in memberships
        if member_name.lower() in m["member_name"].lower()
    ]
    return {"results": result, "total_found": len(result)}

@app.get("/memberships/sort")
def sort_memberships(sort_by: str = "total_fee"):
    valid = ["total_fee", "duration"]
    if sort_by not in valid:
        raise HTTPException(400, "Invalid sort field")

    return sorted(memberships, key=lambda x: x[sort_by])

@app.get("/memberships/page")
def paginate_memberships(page: int = 1, limit: int = 2):
    total = len(memberships)
    total_pages = math.ceil(total / limit)

    start = (page - 1) * limit
    end = start + limit

    return {
        "data": memberships[start:end],
        "page": page,
        "total_pages": total_pages
    }
@app.get("/plans/search")
def search_plans(keyword: str):
    keyword = keyword.lower()

    result = [
        p for p in plans
        if keyword in p["name"].lower()
        or (keyword == "classes" and p["includes_classes"])
        or (keyword == "trainer" and p["includes_trainer"])
    ]

    return {"results": result, "total_found": len(result)}

@app.get("/plans/sort")
def sort_plans(sort_by: str = "price"):
    valid = ["price", "name", "duration_months"]
    if sort_by not in valid:
        raise HTTPException(400, "Invalid sort")

    return sorted(plans, key=lambda x: x[sort_by])

@app.get("/plans/page")
def paginate_plans(page: int = 1, limit: int = 2):
    total = len(plans)
    total_pages = math.ceil(total / limit)

    start = (page - 1) * limit
    end = start + limit

    return {
        "data": plans[start:end],
        "page": page,
        "total_pages": total_pages
    }
    
@app.get("/plans/browse")
def browse_plans(keyword: Optional[str] = None,
                 includes_classes: Optional[bool] = None,
                 includes_trainer: Optional[bool] = None,
                 sort_by: str = "price",
                 order: str = "asc",
                 page: int = 1,
                 limit: int = 2):

    valid = ["price", "name", "duration_months"]
    if sort_by not in valid:
        raise HTTPException(400, "Invalid sort field")

    result = plans

    if keyword:
        keyword = keyword.lower()
        result = [p for p in result if keyword in p["name"].lower()]

    if includes_classes is not None:
        result = [p for p in result if p["includes_classes"] == includes_classes]

    if includes_trainer is not None:
        result = [p for p in result if p["includes_trainer"] == includes_trainer]

    result = sorted(result, key=lambda x: x[sort_by], reverse=(order == "desc"))

    total = len(result)
    total_pages = math.ceil(total / limit)

    start = (page - 1) * limit
    end = start + limit

    return {
        "data": result[start:end],
        "total": total,
        "page": page,
        "total_pages": total_pages
    }
    
@app.get("/plans/{plan_id}")
def get_plan(plan_id: int):
    plan = find_plan(plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")
    return plan
