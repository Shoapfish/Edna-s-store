from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import json, os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = "edna-secret-key-2026"
DATA_FILE = "data.json"

CATEGORIES = [
    "Snacks / Junk Foods", "Instant Foods", "Beverages",
    "Basic Goods / Grocery", "Candies / Sweets", "Bread / Bakery",
    "Personal Care", "Canned Goods", "Etc."
]

# Admin credentials (simple, no DB needed)
ADMIN_USER = "admin"
ADMIN_PASS = "edna2026"

DEFAULT_DATA = {
    "products": [
        {"id": 1,  "name": "Chippy",               "category": "Snacks / Junk Foods",   "price": 12,  "stock": 50},
        {"id": 2,  "name": "Piattos",              "category": "Snacks / Junk Foods",   "price": 15,  "stock": 5},
        {"id": 3,  "name": "Nova",                 "category": "Snacks / Junk Foods",   "price": 10,  "stock": 4},
        {"id": 4,  "name": "Lucky Me Pancit Canton","category": "Instant Foods",         "price": 15,  "stock": 6},
        {"id": 5,  "name": "Softdrinks (1.5L)",    "category": "Beverages",             "price": 65,  "stock": 3},
        {"id": 6,  "name": "Mantika (sachet)",     "category": "Basic Goods / Grocery", "price": 8,   "stock": 4},
        {"id": 7,  "name": "Stick-O (small pack)", "category": "Candies / Sweets",      "price": 10,  "stock": 5},
        {"id": 8,  "name": "Monay",                "category": "Bread / Bakery",        "price": 8,   "stock": 4},
        {"id": 9,  "name": "Cup Noodles",          "category": "Instant Foods",         "price": 20,  "stock": 2},
        {"id": 10, "name": "Shampoo sachet",       "category": "Personal Care",         "price": 15,  "stock": 43},
        {"id": 11, "name": "Conditioner sachet",   "category": "Personal Care",         "price": 20,  "stock": 53},
        {"id": 12, "name": "Soap (Safeguard, Dove)","category": "Personal Care",        "price": 25,  "stock": 2},
        {"id": 13, "name": "Toothpaste",           "category": "Personal Care",         "price": 21,  "stock": 22},
        {"id": 14, "name": "Toothbrush",           "category": "Personal Care",         "price": 25,  "stock": 53},
        {"id": 15, "name": "Facial wash",          "category": "Personal Care",         "price": 50,  "stock": 32},
        {"id": 16, "name": "Lotion",               "category": "Personal Care",         "price": 90,  "stock": 44},
        {"id": 17, "name": "Deodorant",            "category": "Personal Care",         "price": 25,  "stock": 12},
        {"id": 18, "name": "Fabric conditioner",   "category": "Etc.",                  "price": 10,  "stock": 3},
        {"id": 19, "name": "Sardines (555)",       "category": "Canned Goods",          "price": 18,  "stock": 30},
        {"id": 20, "name": "Corned Beef",          "category": "Canned Goods",          "price": 35,  "stock": 20},
    ],
    "customers": [
        {"id": 1, "name": "Mang Rolly", "contact": "", "color": 0, "utangs": [
            {"id": 1, "items": "2x Lucky Me, 1x Milo", "amount": 220, "date": "2026-04-10", "due": "2026-04-20", "paid": False},
            {"id": 2, "items": "3x Tide sachet",       "amount": 200, "date": "2026-04-14", "due": "2026-04-25", "paid": False}
        ]},
        {"id": 2, "name": "Ate Lita",  "contact": "", "color": 1, "utangs": [
            {"id": 1, "items": "1x Softdrinks, 2x Milo","amount": 210, "date": "2026-04-15", "due": "2026-04-28", "paid": False}
        ]},
        {"id": 3, "name": "Kuya Boy",  "contact": "", "color": 2, "utangs": [
            {"id": 1, "items": "5x Lucky Me",          "amount": 310, "date": "2026-04-17", "due": "2026-04-30", "paid": False},
            {"id": 2, "items": "3x Milo sachet",       "amount": 250, "date": "2026-04-18", "due": "2026-04-30", "paid": True}
        ]},
    ],
    "orders": [],
    "about": {
        "owner": "Edna B Owner",
        "contact": "+63 - 904 - 323 - 4567",
        "facebook_account": "Edna Owner",
        "facebook_page": "Edna's Sari - Sari Store",
        "address": "Purok 04 Mapalad, Arayat, Pampanga"
    }
}

LOW_STOCK_THRESHOLD = 10

def load():
    if os.path.exists(DATA_FILE):
        d = json.load(open(DATA_FILE))
        if "orders" not in d: d["orders"] = []
        return d
    return json.loads(json.dumps(DEFAULT_DATA))

def save(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f, indent=2)

def stock_status(qty):
    if qty == 0: return "No Stock"
    if qty <= LOW_STOCK_THRESHOLD: return "Low"
    return "Normal"

def is_admin():
    return session.get("role") == "admin"

def is_logged_in():
    return session.get("role") in ("admin", "customer")

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_admin():
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_logged_in():
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

# ── Auth ───────────────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    success = request.args.get("success")
    if request.method == "POST":
        mode     = request.form.get("mode", "admin")
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if mode == "admin":
            if username == ADMIN_USER and password == ADMIN_PASS:
                session["role"] = "admin"
                session["username"] = "Admin"
                return redirect(url_for("dashboard"))
            else:
                error = "Mali ang admin username o password."
        else:
            # Customer login — check registered accounts
            data = load()
            accounts = data.get("accounts", {})
            name_key = username.lower()
            if name_key in accounts and accounts[name_key]["password"] == password:
                session["role"] = "customer"
                session["username"] = accounts[name_key]["name"]
                return redirect(url_for("shop"))
            else:
                error = "Mali ang pangalan o password. Mag-register muna kung wala ka pang account."
    return render_template("login.html", error=error, success=success)

@app.route("/api/register", methods=["POST"])
def register():
    data = load()
    b = request.get_json()
    name     = b.get("name", "").strip()
    contact  = b.get("contact", "").strip()
    password = b.get("password", "").strip()
    if not name or not password:
        return jsonify({"error": "Pangalan at password ay kailangan."}), 400
    if "accounts" not in data:
        data["accounts"] = {}
    name_key = name.lower()
    if name_key in data["accounts"]:
        return jsonify({"error": f"May account na si '{name}'. Mag-login na lang."}), 409
    # Also add as customer record if not yet existing
    existing = next((c for c in data["customers"] if c["name"].lower() == name_key), None)
    if not existing:
        new_id = max((c["id"] for c in data["customers"]), default=0) + 1
        data["customers"].append({
            "id": new_id, "name": name, "contact": contact,
            "color": len(data["customers"]) % 5, "utangs": []
        })
    data["accounts"][name_key] = {"name": name, "contact": contact, "password": password}
    save(data)
    return jsonify({"ok": True, "name": name}), 201

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ── Admin Pages ────────────────────────────────────────────────────────────────

@app.route("/")
@admin_required
def dashboard():
    data = load()
    products = data["products"]
    customers = data["customers"]
    orders = data.get("orders", [])
    total_products  = len(products)
    total_stocks    = sum(p["stock"] for p in products)
    low_items       = [p for p in products if 0 < p["stock"] <= LOW_STOCK_THRESHOLD]
    out_of_stock    = [p for p in products if p["stock"] == 0]
    cat_counts = {}
    for p in products:
        cat_counts[p["category"]] = cat_counts.get(p["category"], 0) + 1
    total_utang     = sum(u["amount"] for c in customers for u in c["utangs"] if not u["paid"])
    total_may_utang = sum(1 for c in customers if any(not u["paid"] for u in c["utangs"]))
    top_debtor      = max(customers, key=lambda c: sum(u["amount"] for u in c["utangs"] if not u["paid"]), default=None)
    new_orders      = [o for o in orders if o["status"] == "Pending"]
    return render_template("dashboard.html",
        total_products=total_products, total_stocks=total_stocks,
        low_items=low_items, out_of_stock=out_of_stock,
        cat_counts=cat_counts, categories=CATEGORIES,
        total_utang=total_utang, total_may_utang=total_may_utang,
        top_debtor=top_debtor, new_orders=new_orders,
        is_admin=True)

@app.route("/products")
@admin_required
def product_list():
    data = load()
    cat    = request.args.get("category", "All Products")
    search = request.args.get("search", "").strip().lower()
    page   = int(request.args.get("page", 1))
    per_page = 10
    products = data["products"]
    if cat != "All Products":
        products = [p for p in products if p["category"] == cat]
    if search:
        products = [p for p in products if search in p["name"].lower()]
    total = len(products)
    total_pages = max(1, -(-total // per_page))
    page = max(1, min(page, total_pages))
    return render_template("products.html",
        products=products[(page-1)*per_page:page*per_page],
        categories=CATEGORIES, current_cat=cat, search=search,
        page=page, total_pages=total_pages, total=total, is_admin=True)

@app.route("/utang")
@admin_required
def utang_list():
    data = load()
    customers = data["customers"]
    page = int(request.args.get("page", 1))
    per_page = 10
    total = len(customers)
    total_pages = max(1, -(-total // per_page))
    page = max(1, min(page, total_pages))
    return render_template("utang.html",
        customers=customers[(page-1)*per_page:page*per_page],
        page=page, total_pages=total_pages, total=total, is_admin=True)

@app.route("/utang/<int:cid>")
@admin_required
def utang_detail(cid):
    data = load()
    customer = next((c for c in data["customers"] if c["id"] == cid), None)
    if not customer: return redirect(url_for("utang_list"))
    return render_template("utang_detail.html", customer=customer, is_admin=True)

@app.route("/inventory")
@admin_required
def inventory():
    data = load()
    status_filter = request.args.get("status", "All Status")
    search = request.args.get("search", "").strip().lower()
    page   = int(request.args.get("page", 1))
    per_page = 10
    products = data["products"]
    if search:
        products = [p for p in products if search in p["name"].lower()]
    if status_filter == "Normal Stock":
        products = [p for p in products if p["stock"] > LOW_STOCK_THRESHOLD]
    elif status_filter == "Low Stock":
        products = [p for p in products if 0 < p["stock"] <= LOW_STOCK_THRESHOLD]
    elif status_filter == "No Stock":
        products = [p for p in products if p["stock"] == 0]
    total = len(products)
    total_pages = max(1, -(-total // per_page))
    page = max(1, min(page, total_pages))
    return render_template("inventory.html",
        products=products[(page-1)*per_page:page*per_page],
        status_filter=status_filter, search=search,
        page=page, total_pages=total_pages, total=total,
        stock_status=stock_status, is_admin=True)

@app.route("/about")
@login_required
def about():
    data = load()
    return render_template("about.html", about=data["about"], is_admin=is_admin())

@app.route("/orders")
@admin_required
def orders_page():
    data = load()
    orders = sorted(data.get("orders", []), key=lambda o: o["created_at"], reverse=True)
    return render_template("orders.html", orders=orders, is_admin=True)

# ── Customer Pages ─────────────────────────────────────────────────────────────

@app.route("/shop")
@login_required
def shop():
    data = load()
    cat    = request.args.get("category", "All Products")
    search = request.args.get("search", "").strip().lower()
    page   = int(request.args.get("page", 1))
    per_page = 12
    products = [p for p in data["products"] if p["stock"] > 0]
    if cat != "All Products":
        products = [p for p in products if p["category"] == cat]
    if search:
        products = [p for p in products if search in p["name"].lower()]
    total = len(products)
    total_pages = max(1, -(-total // per_page))
    page = max(1, min(page, total_pages))
    # Find customer utang
    username = session.get("username", "")
    my_customer = next((c for c in data["customers"] if c["name"].lower() == username.lower()), None)
    return render_template("shop.html",
        products=products[(page-1)*per_page:page*per_page],
        categories=CATEGORIES, current_cat=cat, search=search,
        page=page, total_pages=total_pages, total=total,
        my_customer=my_customer, username=username, is_admin=False)

@app.route("/my-orders")
@login_required
def my_orders():
    data = load()
    username = session.get("username", "")
    my = [o for o in data.get("orders", []) if o["customer_name"].lower() == username.lower()]
    my = sorted(my, key=lambda o: o["created_at"], reverse=True)
    return render_template("my_orders.html", orders=my, username=username, is_admin=False)

@app.route("/my-utang")
@login_required
def my_utang():
    data = load()
    username = session.get("username", "")
    customer = next((c for c in data["customers"] if c["name"].lower() == username.lower()), None)
    return render_template("my_utang.html", customer=customer, username=username, is_admin=False)

# ── API: Auth ──────────────────────────────────────────────────────────────────

@app.route("/api/session")
def get_session():
    return jsonify({"role": session.get("role"), "username": session.get("username")})

# ── API: Orders ────────────────────────────────────────────────────────────────

@app.route("/api/orders", methods=["POST"])
@login_required
def place_order():
    data = load()
    b = request.get_json()
    customer_name = b.get("customer_name", "").strip()
    items         = b.get("items", [])
    note          = b.get("note", "").strip()
    if not customer_name or not items:
        return jsonify({"error": "customer_name and items required"}), 400
    # Calculate total & check stock
    total = 0
    order_items = []
    for item in items:
        product = next((p for p in data["products"] if p["id"] == item["id"]), None)
        if not product: return jsonify({"error": f"Product {item['id']} not found"}), 404
        qty = int(item["qty"])
        subtotal = product["price"] * qty
        total += subtotal
        order_items.append({
            "product_id": product["id"],
            "name": product["name"],
            "price": product["price"],
            "qty": qty,
            "subtotal": subtotal
        })
    new_id = max((o["id"] for o in data["orders"]), default=0) + 1
    order = {
        "id": new_id,
        "customer_name": customer_name,
        "order_items": order_items,
        "total": total,
        "note": note,
        "status": "Pending",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    data["orders"].append(order)
    save(data)
    return jsonify(order), 201

@app.route("/api/orders/<int:oid>/status", methods=["PATCH"])
@admin_required
def update_order_status(oid):
    data = load()
    order = next((o for o in data["orders"] if o["id"] == oid), None)
    if not order: return jsonify({"error": "not found"}), 404
    new_status = request.get_json().get("status")
    if new_status not in ("Pending", "Preparing", "Ready", "Completed", "Cancelled"):
        return jsonify({"error": "invalid status"}), 400
    order["status"] = new_status
    # Deduct stock when marking Ready
    if new_status == "Ready":
        for item in order["order_items"]:
            p = next((x for x in data["products"] if x["id"] == item["product_id"]), None)
            if p: p["stock"] = max(0, p["stock"] - item["qty"])
    save(data)
    return jsonify(order)

@app.route("/api/orders/<int:oid>", methods=["DELETE"])
@admin_required
def delete_order(oid):
    data = load()
    data["orders"] = [o for o in data["orders"] if o["id"] != oid]
    save(data); return jsonify({"ok": True})

@app.route("/api/orders/pending-count")
@login_required
def pending_count():
    data = load()
    return jsonify({"count": sum(1 for o in data.get("orders", []) if o["status"] == "Pending")})

# ── API: Products ──────────────────────────────────────────────────────────────

@app.route("/api/products", methods=["POST"])
@admin_required
def add_product():
    data = load()
    b = request.get_json()
    new_id = max((p["id"] for p in data["products"]), default=0) + 1
    p = {"id": new_id, "name": b["name"], "category": b["category"],
         "price": float(b["price"]), "stock": int(b["stock"])}
    data["products"].append(p); save(data); return jsonify(p), 201

@app.route("/api/products/<int:pid>", methods=["PUT"])
@admin_required
def edit_product(pid):
    data = load()
    p = next((x for x in data["products"] if x["id"] == pid), None)
    if not p: return jsonify({"error": "not found"}), 404
    b = request.get_json()
    p.update({"name": b["name"], "category": b["category"],
               "price": float(b["price"]), "stock": int(b["stock"])})
    save(data); return jsonify(p)

@app.route("/api/products/<int:pid>", methods=["DELETE"])
@admin_required
def delete_product(pid):
    data = load()
    data["products"] = [p for p in data["products"] if p["id"] != pid]
    save(data); return jsonify({"ok": True})

# ── API: Customers ─────────────────────────────────────────────────────────────

@app.route("/api/customers", methods=["POST"])
@admin_required
def add_customer():
    data = load()
    b = request.get_json()
    new_id = max((c["id"] for c in data["customers"]), default=0) + 1
    c = {"id": new_id, "name": b["name"], "contact": b.get("contact",""),
         "color": len(data["customers"]) % 5, "utangs": []}
    data["customers"].append(c); save(data); return jsonify(c), 201

@app.route("/api/customers/<int:cid>", methods=["DELETE"])
@admin_required
def delete_customer(cid):
    data = load()
    data["customers"] = [c for c in data["customers"] if c["id"] != cid]
    save(data); return jsonify({"ok": True})

@app.route("/api/customers/<int:cid>/utangs", methods=["POST"])
@admin_required
def add_utang(cid):
    data = load()
    c = next((x for x in data["customers"] if x["id"] == cid), None)
    if not c: return jsonify({"error": "not found"}), 404
    b = request.get_json()
    new_id = max((u["id"] for u in c["utangs"]), default=0) + 1
    u = {"id": new_id, "items": b["items"], "amount": float(b["amount"]),
         "date": b["date"], "due": b.get("due",""), "paid": False}
    c["utangs"].append(u); save(data); return jsonify(u), 201

@app.route("/api/customers/<int:cid>/utangs/<int:uid>/pay", methods=["PATCH"])
@admin_required
def pay_utang(cid, uid):
    data = load()
    c = next((x for x in data["customers"] if x["id"] == cid), None)
    if not c: return jsonify({"error": "not found"}), 404
    u = next((x for x in c["utangs"] if x["id"] == uid), None)
    if not u: return jsonify({"error": "not found"}), 404
    u["paid"] = True; save(data); return jsonify(u)

@app.route("/api/customers/<int:cid>/utangs/<int:uid>", methods=["DELETE"])
@admin_required
def delete_utang(cid, uid):
    data = load()
    c = next((x for x in data["customers"] if x["id"] == cid), None)
    if not c: return jsonify({"error": "not found"}), 404
    c["utangs"] = [u for u in c["utangs"] if u["id"] != uid]
    save(data); return jsonify({"ok": True})

@app.route("/api/about", methods=["PUT"])
@admin_required
def update_about():
    data = load()
    data["about"] = request.get_json()
    save(data); return jsonify(data["about"])

if __name__ == "__main__":
    app.run(debug=True, port=5000)