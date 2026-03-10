from fastapi import FastAPI
from typing import Optional, List
from pydantic import BaseModel, Field

app = FastAPI()

# Product list
products = [
    {"id": 1, "name": "Wireless Mouse", "price": 799, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": True},
    {"id": 4, "name": "Monitor", "price": 8999, "category": "Electronics", "in_stock": False},

    # Q1 – Added products
    {"id": 5, "name": "Laptop Stand", "price": 599, "category": "Electronics", "in_stock": True},
    {"id": 6, "name": "Mechanical Keyboard", "price": 2499, "category": "Electronics", "in_stock": True},
    {"id": 7, "name": "Webcam", "price": 1499, "category": "Electronics", "in_stock": False}
]

# ---------------------------------------------------------
# DAY 1 ENDPOINTS
# ---------------------------------------------------------

# Q1 — Show all products
@app.get("/products")
def get_products():
    return {
        "products": products,
        "total": len(products)
    }

# Q2 — Filter by category
@app.get("/products/category/{category_name}")
def get_products_by_category(category_name: str):
    filtered = []
    for product in products:
        if product["category"].lower() == category_name.lower():
            filtered.append(product)
    if len(filtered) == 0:
        return {"error": "No products found in this category"}
    return {"products": filtered}

# Q3 — Only in-stock products
@app.get("/products/instock")
def get_instock_products():
    instock = []
    for product in products:
        if product["in_stock"] == True:
            instock.append(product)
    return {
        "in_stock_products": instock,
        "count": len(instock)
    }

# Q4 — Store summary
@app.get("/store/summary")
def store_summary():
    total_products = len(products)
    instock = 0
    outstock = 0
    categories = []

    for product in products:
        if product["in_stock"]:
            instock += 1
        else:
            outstock += 1

        if product["category"] not in categories:
            categories.append(product["category"])

    return {
        "store_name": "My E-commerce Store",
        "total_products": total_products,
        "in_stock": instock,
        "out_of_stock": outstock,
        "categories": categories
    }

# Q5 — Search products
@app.get("/products/search/{keyword}")
def search_products(keyword: str):
    results = []
    for product in products:
        if keyword.lower() in product["name"].lower():
            results.append(product)
    if len(results) == 0:
        return {"message": "No products matched your search"}
    return {
        "matched_products": results,
        "count": len(results)
    }

# ⭐ BONUS — Best deal and premium pick
@app.get("/products/deals")
def product_deals():
    cheapest = products[0]
    expensive = products[0]

    for product in products:
        if product["price"] < cheapest["price"]:
            cheapest = product
        if product["price"] > expensive["price"]:
            expensive = product

    return {
        "best_deal": cheapest,
        "premium_pick": expensive
    }

# ---------------------------------------------------------
# DAY 2 PRACTICE TASKS 
# ---------------------------------------------------------

# Day 2 - Task 1: Filter Products by Minimum Price
@app.get("/products/filter")
def filter_products(
    category: Optional[str] = None, 
    max_price: Optional[int] = None, 
    min_price: Optional[int] = None
):
    filtered = products
    if category:
        filtered = [p for p in filtered if p["category"].lower() == category.lower()]
    if max_price is not None:
        filtered = [p for p in filtered if p["price"] <= max_price]
    if min_price is not None:
        filtered = [p for p in filtered if p["price"] >= min_price]
        
    return filtered

# Day 2 - Task 2: Get Only the Price of a Product
@app.get("/products/{product_id}/price")
def get_product_price(product_id: int):
    for product in products:
        if product["id"] == product_id:
            return {"name": product["name"], "price": product["price"]}
    return {"error": "Product not found"}


# Day 2 - Task 3: Pydantic + POST - Accept Customer Feedback
class CustomerFeedback(BaseModel):
    customer_name: str = Field(min_length=2)
    product_id: int = Field(gt=0)
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=300)

feedback_list = []

@app.post("/feedback")
def submit_feedback(feedback: CustomerFeedback):
    feedback_list.append(feedback.model_dump())
    return {
        "message": "Feedback submitted successfully",
        "feedback": feedback.model_dump(),
        "total_feedback": len(feedback_list)
    }


# Day 2 - Task 4: Build a Product Summary Dashboard
@app.get("/products/summary")
def get_products_summary():
    in_stock_count = sum(1 for p in products if p["in_stock"])
    out_of_stock_count = len(products) - in_stock_count
    
    sorted_products = sorted(products, key=lambda x: x["price"])
    cheapest = {"name": sorted_products[0]["name"], "price": sorted_products[0]["price"]}
    most_expensive = {"name": sorted_products[-1]["name"], "price": sorted_products[-1]["price"]}
    
    # Extract unique categories
    categories = list(set(p["category"] for p in products))
    
    return {
        "total_products": len(products),
        "in_stock_count": in_stock_count,
        "out_of_stock_count": out_of_stock_count,
        "most_expensive": most_expensive,
        "cheapest": cheapest,
        "categories": categories
    }


# Day 2 - Task 5: Validate & Place a Bulk Order
class OrderItem(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(ge=1, le=50)

class BulkOrder(BaseModel):
    company_name: str = Field(min_length=2)
    contact_email: str = Field(min_length=5)
    items: List[OrderItem] = Field(min_length=1)

@app.post("/orders/bulk")
def place_bulk_order(order: BulkOrder):
    confirmed = []
    failed = []
    grand_total = 0

    for item in order.items:
        # Find the product in our dictionary list
        product = next((p for p in products if p["id"] == item.product_id), None)
        
        if not product:
            failed.append({"product_id": item.product_id, "reason": "Product not found"})
        elif not product["in_stock"]:
            failed.append({"product_id": item.product_id, "reason": f"{product['name']} is out of stock"})
        else:
            subtotal = product["price"] * item.quantity
            grand_total += subtotal
            confirmed.append({
                "product": product["name"],
                "qty": item.quantity,
                "subtotal": subtotal
            })

    return {
        "company": order.company_name,
        "confirmed": confirmed,
        "failed": failed,
        "grand_total": grand_total
    }


# Day 2 - ⭐ Bonus: Order Status Tracker
class SingleOrder(BaseModel):
    product_id: int
    quantity: int

orders_db = []
order_id_counter = 1

@app.post("/orders")
def create_order(order: SingleOrder):
    global order_id_counter
    
    new_order = {
        "order_id": order_id_counter,
        "product_id": order.product_id,
        "quantity": order.quantity,
        "status": "pending"
    }
    
    orders_db.append(new_order)
    order_id_counter += 1
    return new_order

@app.get("/orders/{order_id}")
def get_order(order_id: int):
    for order in orders_db:
        if order["order_id"] == order_id:
            return order
    return {"error": "Order not found"}

@app.patch("/orders/{order_id}/confirm")
def confirm_order(order_id: int):
    for order in orders_db:
        if order["order_id"] == order_id:
            order["status"] = "confirmed"
            return {"message": "Order confirmed successfully", "order": order}
            
    return {"error": "Order not found"}