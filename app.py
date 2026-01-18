import os
from flask import Flask, render_template, request, redirect, session
from flask_mail import Mail, Message
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from bson.errors import InvalidId
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ================= MAIL CONFIG =================
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = "propbelgaum@gmail.com"
app.config['MAIL_PASSWORD'] = "asig sjtg qvqh okfn"
app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']

mail = Mail(app)

# ================= MONGO CONFIG =================
mongo_uri = os.getenv("MONGO_URI")
mongo_dbname = os.getenv("MONGO_DBNAME")

mongo_client = MongoClient(mongo_uri)
db = mongo_client[mongo_dbname]
  # Use ayush1 database

# ================= USERS =================
USERS = {
    "tanvipatil": {"password": "tanvipatil@2211", "role": "admin"},
    "superadmin": {"password": "superadmin123", "role": "superadmin"}
}

# ================= LOGIN =================
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Check hardcoded users
        user = USERS.get(request.form["username"])
        # Or check MongoDB users collection
        if not user:
            user = db.users.find_one({"username": request.form["username"]})
        if user and user["password"] == request.form["password"]:
            session["username"] = user.get("username") or request.form["username"]
            session["role"] = user.get("role", "admin")
            return redirect("/dashboard")
        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect("/login")

    total_properties = db.properties.count_documents({})
    total_sold = db.properties.count_documents({"status": "Sold"})
    total_collab = db.collaborations.count_documents({})
    collab_completed = db.collaborations.count_documents({"pending_amount": 0})

    property_revenue = sum([p.get("sold_price", 0) for p in db.properties.find({"status": "Sold"})])
    collaboration_revenue = sum([c.get("paid_amount", 0) for c in db.collaborations.find()])

    stats = {
        "total_properties": total_properties,
        "total_sold": total_sold,
        "collab_completed": collab_completed,
        "total_collab": total_collab,
        "property_revenue": float(property_revenue),
        "collaboration_revenue": float(collaboration_revenue),
        "total_revenue": float(property_revenue + collaboration_revenue),
        "adjusted_property_revenue": float(property_revenue * 0.9),
        "adjusted_collaboration_revenue": float(collaboration_revenue * 0.9),
        "total_adjusted_revenue": float(property_revenue * 0.9 + collaboration_revenue * 0.9)
    }

    if session["role"] == "superadmin":
        return render_template("dashboard_actual.html", stats=stats)
    return render_template("dashboard_adjusted.html", stats=stats)

# ================= PROPERTIES =================
@app.route("/properties")
def properties_page():
    if "username" not in session:
        return redirect("/login")
    
    properties = list(db.properties.find())
    for p in properties:
        p["_id"] = str(p["_id"])
    return render_template("properties.html", properties=properties)

@app.route("/properties/add", methods=["GET", "POST"])
def add_property():
    if request.method == "POST":
        db.properties.insert_one({
            "title": request.form["title"],
            "type": request.form["type"],
            "location": request.form["location"],
            "size": request.form["size"],
            "price": float(request.form["price"]),
            "owner": request.form["owner"],
            "contact": request.form["contact"],
            "status": "Available",
            "sold_price": 0
        })
        return redirect("/properties")
    return render_template("add_property.html")

@app.route("/properties/<pid>")
def property_detail(pid):
    try:
        obj_id = ObjectId(pid)
    except InvalidId:
        return "Invalid Property ID", 404

    prop = db.properties.find_one({"_id": obj_id})
    if not prop:
        return "Property Not Found", 404

    interactions = list(db.interactions.find({"property_id": obj_id}).sort("date", -1))
    for i in interactions:
        i["_id"] = str(i["_id"])
        if isinstance(i.get("date"), datetime):
            i["date_str"] = i["date"].strftime("%d-%m-%Y")
    prop["_id"] = str(prop["_id"])
    prop["interactions"] = interactions
    return render_template("property_detail.html", prop=prop)

@app.route("/properties/<pid>/edit", methods=["GET", "POST"])
def edit_property(pid):
    try:
        obj_id = ObjectId(pid)
    except InvalidId:
        return "Invalid Property ID", 404

    prop = db.properties.find_one({"_id": obj_id})
    if not prop:
        return "Property Not Found", 404

    if request.method == "POST":
        db.properties.update_one({"_id": obj_id}, {"$set": {
            "title": request.form["title"],
            "type": request.form["type"],
            "location": request.form["location"],
            "size": request.form["size"],
            "price": float(request.form["price"]),
            "owner": request.form["owner"],
            "contact": request.form["contact"],
            "status": request.form["status"],
            "sold_price": float(request.form["sold_price"])
        }})
        return redirect(f"/properties/{pid}")

    prop["_id"] = str(prop["_id"])
    return render_template("edit_property.html", prop=prop)

@app.route("/properties/<pid>/delete")
def delete_property(pid):
    try:
        obj_id = ObjectId(pid)
    except InvalidId:
        return "Invalid Property ID", 404

    db.properties.delete_one({"_id": obj_id})
    db.interactions.delete_many({"property_id": obj_id})
    return redirect("/properties")

@app.route("/properties/<pid>/interactions/add", methods=["POST"])
def add_interaction(pid):
    try:
        obj_id = ObjectId(pid)
    except InvalidId:
        return "Invalid Property ID", 404

    db.interactions.insert_one({
        "property_id": obj_id,
        "customer_name": request.form["customer_name"],
        "contact": request.form["contact"],
        "notes": request.form["notes"],
        "date": datetime.now()
    })

    return redirect(f"/properties/{pid}")

@app.route("/properties/<pid>/sold", methods=["POST"])
def mark_sold(pid):
    obj_id = ObjectId(pid)
    sold_price = float(request.form["sold_price"])
    db.properties.update_one({"_id": obj_id}, {"$set": {"status": "Sold", "sold_price": sold_price}})
    return redirect(f"/properties/{pid}")

# ================= COLLABORATIONS =================
@app.route("/collaborations")
def collaborations_page():
    if "username" not in session:
        return redirect("/login")

    filter_type = request.args.get("filter")
    collaborations = list(db.collaborations.find())
    today = datetime.now().date()
    processed = []

    for c in collaborations:
        c_copy = c.copy()
        c_copy["_id"] = str(c["_id"])
        status = "Active"

        due = c.get("due_date")
        if isinstance(due, datetime):
            due_date = due.date()
        else:
            due_date = today

        if due_date < today:
            status = "Expired"
        elif due_date <= today + timedelta(days=30):
            status = "Due Soon"

        c_copy["status"] = status
        pending = c_copy.get("pending_amount", 0)
        if filter_type == "pending" and pending == 0:
            continue
        if filter_type == "completed" and pending != 0:
            continue
        if filter_type == "due_soon" and status != "Due Soon":
            continue

        processed.append(c_copy)

    if filter_type == "due_asc":
        processed.sort(key=lambda x: x.get("due_date", today))
    elif filter_type == "due_desc":
        processed.sort(key=lambda x: x.get("due_date", today), reverse=True)

    return render_template("collaborations.html", collaborations=processed)

@app.route("/collaborations/add", methods=["GET", "POST"])
def add_collaboration():
    if "username" not in session:
        return redirect("/login")

    if request.method == "POST":
        total = float(request.form["total_amount"])
        paid = float(request.form["paid_amount"])
        pending = total - paid

        start_date = datetime.strptime(request.form["start_date"], "%Y-%m-%d")
        due_date = datetime.strptime(request.form["due_date"], "%Y-%m-%d")

        collab = {
            "supplier": request.form["supplier"],
            "category": request.form["category"],
            "service": request.form["service"],
            "contact_person": request.form["contact_person"],
            "contact_number": request.form["contact_number"],
            "email": request.form["email"],
            "start_date": start_date,
            "due_date": due_date,
            "total_amount": total,
            "paid_amount": paid,
            "pending_amount": pending,
            "interactions": []
        }
        db.collaborations.insert_one(collab)
        return redirect("/collaborations")
    return render_template("add_collaboration.html", collab=None)

@app.route("/collaborations/<cid>")
def view_collaboration(cid):
    if "username" not in session:
        return redirect("/login")
    collab = db.collaborations.find_one({"_id": ObjectId(cid)})
    if not collab:
        return "Collaboration Not Found", 404
    collab["_id"] = str(collab["_id"])
    interactions = collab.get("interactions", [])
    for i in interactions:
        if isinstance(i.get("date"), datetime):
            i["date_str"] = i["date"].strftime("%d-%m-%Y")
        else:
            i["date_str"] = ""
    return render_template("collaboration_detail.html", collab=collab)

@app.route("/collaborations/<cid>/edit", methods=["GET", "POST"])
def edit_collaboration(cid):
    if "username" not in session:
        return redirect("/login")
    collab = db.collaborations.find_one({"_id": ObjectId(cid)})
    if not collab:
        return "Collaboration Not Found", 404

    if request.method == "POST":
        total = float(request.form["total_amount"])
        paid = float(request.form["paid_amount"])
        pending = total - paid
        start_date = datetime.strptime(request.form["start_date"], "%Y-%m-%d")
        due_date = datetime.strptime(request.form["due_date"], "%Y-%m-%d")

        db.collaborations.update_one({"_id": ObjectId(cid)}, {"$set": {
            "supplier": request.form["supplier"],
            "category": request.form["category"],
            "service": request.form["service"],
            "contact_person": request.form["contact_person"],
            "contact_number": request.form["contact_number"],
            "email": request.form["email"],
            "start_date": start_date,
            "due_date": due_date,
            "total_amount": total,
            "paid_amount": paid,
            "pending_amount": pending
        }})
        return redirect(f"/collaborations/{cid}")
    collab["_id"] = str(collab["_id"])
    return render_template("edit_collaboration.html", collab=collab)

@app.route("/collaborations/<cid>/delete", methods=["POST"])
def delete_collaboration(cid):
    if "username" not in session:
        return redirect("/login")
    db.collaborations.delete_one({"_id": ObjectId(cid)})
    return redirect("/collaborations")

@app.route("/collaborations/<cid>/interactions/add", methods=["POST"])
def add_collab_interaction(cid):
    if "username" not in session:
        return redirect("/login")
    
    collab = db.collaborations.find_one({"_id": ObjectId(cid)})
    if not collab:
        return "Collaboration Not Found", 404

    note = request.form.get("notes", "").strip()
    if not note:
        return redirect(f"/collaborations/{cid}")

    date_str = request.form.get("interaction_date")
    if date_str:
        try:
            interaction_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            interaction_date = datetime.now()
    else:
        interaction_date = datetime.now()

    # Create interaction object
    interaction = {
        "_id": ObjectId(),  # unique ID for this interaction
        "note": note,
        "date": interaction_date
    }

    # Push into collaborations array
    result = db.collaborations.update_one(
        {"_id": ObjectId(cid)},
        {"$push": {"interactions": interaction}}
    )

    if result.modified_count == 0:
        return "Failed to add interaction", 500

    return redirect(f"/collaborations/{cid}")

@app.route("/collaborations/<cid>/interactions/delete/<iid>", methods=["POST"])
def delete_collab_interaction(cid, iid):
    if "username" not in session:
        return redirect("/login")
    db.collaborations.update_one({"_id": ObjectId(cid)}, {"$pull": {"interactions": {"_id": ObjectId(iid)}}})
    return redirect(f"/collaborations/{cid}")

@app.route("/revenue/actual")
def revenue_actual_page():  # changed from revenue_actual
    if "username" not in session:
        return redirect("/login")

    property_total = sum([p.get("sold_price", 0) for p in db.properties.find({"status": "Sold"})])
    collaboration_total = sum([c.get("paid_amount", 0) for c in db.collaborations.find()])
    grand_total = property_total + collaboration_total

    revenue = {
        "property_total": round(property_total, 2),
        "collaboration_total": round(collaboration_total, 2),
        "grand_total": round(grand_total, 2),
        "profit": round(grand_total, 2)
    }

    return render_template("revenue_actual.html", revenue=revenue)


@app.route("/revenue/adjusted")
def revenue_adjusted_page():  # changed from revenue_adjusted
    if "username" not in session:
        return redirect("/login")

    property_total = sum([p.get("sold_price", 0) for p in db.properties.find({"status": "Sold"})])
    collaboration_total = sum([c.get("paid_amount", 0) for c in db.collaborations.find()])
    property_total_adj = property_total * 0.9
    collaboration_total_adj = collaboration_total * 0.9
    grand_total = property_total_adj + collaboration_total_adj

    revenue = {
        "property_total": round(property_total_adj, 2),
        "collaboration_total": round(collaboration_total_adj, 2),
        "grand_total": round(grand_total, 2),
        "profit": round(grand_total, 2)
    }

    return render_template("revenue_adjusted.html", revenue=revenue)


# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ================= RUN APP =================
if __name__ == "__main__":
    app.run(debug=True)
