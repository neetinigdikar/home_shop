import streamlit as st
from pymongo import MongoClient
import bcrypt
from bson.objectid import ObjectId
import pandas as pd
from datetime import datetime

# -------------------------------
# MongoDB Connection
# -------------------------------
@st.cache_resource
def get_db():
    # Fetch MongoDB connection from secrets
    uri = st.secrets["mongo"]["uri"]
    dbname = st.secrets["mongo"]["db"]
    client = MongoClient(uri)
    return client[dbname]

db = get_db()
users_col = db["users"]
products_col = db["products"]
orders_col = db["orders"]

# -------------------------------
# Admin Credentials (stored in secrets)
# -------------------------------
ADMIN_USERNAME = st.secrets["admin"]["username"]
ADMIN_PASSWORD = st.secrets["admin"]["password"]

# -------------------------------
# Helper Functions
# -------------------------------
def hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

def check_password(password: str, hashed: bytes) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed)

def create_user(username: str, password: str):
    """Admin creates a new user"""
    if users_col.find_one({"username": username}):
        return {"success": False, "msg": "Username already exists."}
    hashed_pw = hash_password(password)
    users_col.insert_one({"username": username, "password": hashed_pw})
    return {"success": True, "msg": "User created successfully."}

def create_product(name: str, price: float, stock: int):
    """Admin creates a new product"""
    if products_col.find_one({"name": name}):
        return {"success": False, "msg": "Product already exists."}
    products_col.insert_one({"name": name, "price": price, "stock": stock})
    return {"success": True, "msg": "Product added successfully."}

# -------------------------------
# Session State
# -------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.is_admin = False
    st.session_state.username = None
    st.session_state.cart = {}

# -------------------------------
# Login Page
# -------------------------------
def login_page():
    st.title("🛒 Online Shopping Portal")

    login_type = st.radio("Login as:", ["User", "Admin"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if login_type == "Admin":
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                st.session_state.logged_in = True
                st.session_state.is_admin = True
                st.session_state.username = username
                st.success("Admin login successful!")
                st.experimental_rerun()
            else:
                st.error("Invalid admin credentials.")
        else:
            user = users_col.find_one({"username": username})
            if user and check_password(password, user["password"]):
                st.session_state.logged_in = True
                st.session_state.is_admin = False
                st.session_state.username = username
                st.success(f"Welcome, {username}!")
                st.experimental_rerun()
            else:
                st.error("Invalid user credentials.")

# -------------------------------
# Admin Page
# -------------------------------
def admin_page():
    st.title("👨‍💼 Admin Dashboard")
    st.subheader("Create New User")

    with st.form("create_user"):
        new_username = st.text_input("New Username")
        new_password = st.text_input("New Password", type="password")
        submit_user = st.form_submit_button("Create User")
        if submit_user:
            res = create_user(new_username, new_password)
            if res["success"]:
                st.success(res["msg"])
            else:
                st.error(res["msg"])

    st.subheader("Add Product")
    with st.form("add_product"):
        product_name = st.text_input("Product Name")
        product_price = st.number_input("Price", min_value=0.0, format="%.2f")
        product_stock = st.number_input("Stock", min_value=0, step=1)
        submit_prod = st.form_submit_button("Add Product")
        if submit_prod:
            res = create_product(product_name, product_price, int(product_stock))
            if res["success"]:
                st.success(res["msg"])
            else:
                st.error(res["msg"])

    st.subheader("Existing Products")
    products = list(products_col.find({}))
    if products:
        df = pd.DataFrame(products)
        df["_id"] = df["_id"].astype(str)
        st.dataframe(df[["name", "price", "stock"]])
    else:
        st.info("No products found.")

    if st.button("Logout"):
        st.session_state.clear()
        st.experimental_rerun()

# -------------------------------
# User Page
# -------------------------------
def user_page():
    st.title("🛍️ Welcome to Our Store!")
    st.subheader(f"Logged in as: {st.session_state.username}")

    products = list(products_col.find({}))
    if not products:
        st.warning("No products available.")
        return

    for product in products:
        st.markdown(f"### {product['name']}  ₹{product['price']}")
        st.write(f"Stock: {product['stock']}")
        qty = st.number_input(f"Quantity for {product['name']}", 1, product["stock"], 1, key=str(product["_id"]))
        if st.button(f"Add to Cart - {product['name']}", key=f"add_{product['_id']}"):
            pid = str(product["_id"])
            cart = st.session_state.cart
            if pid in cart:
                cart[pid]["qty"] += qty
            else:
                cart[pid] = {"name": product["name"], "price": product["price"], "qty": qty}
            st.success(f"Added {qty} × {product['name']} to cart")

    st.markdown("---")
    st.subheader("🛒 Your Cart")
    if st.session_state.cart:
        total = 0.0
        for pid, item in st.session_state.cart.items():
            subtotal = item["price"] * item["qty"]
            st.write(f"{item['name']} — ₹{item['price']} × {item['qty']} = ₹{subtotal}")
            total += subtotal
        st.write(f"**Total: ₹{total}**")

        if st.button("Buy Now"):
            order = {
                "username": st.session_state.username,
                "items": list(st.session_state.cart.values()),
                "total": total,
                "created_at": datetime.utcnow()
            }
            orders_col.insert_one(order)
            st.session_state.cart = {}
            st.success("✅ Order placed successfully!")
    else:
        st.info("Cart is empty.")

    if st.button("Logout"):
        st.session_state.clear()
        st.experimental_rerun()

# -------------------------------
# Main App
# -------------------------------
def main():
    if not st.session_state.logged_in:
        login_page()
    elif st.session_state.is_admin:
        admin_page()
    else:
        user_page()

if __name__ == "__main__":
    main()
