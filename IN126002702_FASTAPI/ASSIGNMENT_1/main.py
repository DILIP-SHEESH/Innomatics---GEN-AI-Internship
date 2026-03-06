from fastapi import FastAPI

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