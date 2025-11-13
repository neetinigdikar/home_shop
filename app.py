import streamlit as st
from pymongo import MongoClient
from datetime import datetime

# ---------------------------------------------------
# MongoDB Connection
# ---------------------------------------------------
MONGO_URI = st.secrets["MONGO"]["MONGO_URI"]
client = MongoClient(MONGO_URI)
db = client["home_shop_db"]

users_col = db["users"]
products_col = db["products"]
orders_col = db["orders"]

# ---------------------------------------------------
# Admin Credentials
# ---------------------------------------------------
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# ---------------------------------------------------
# Admin Dashboard
# ---------------------------------------------------
def admin_page():
    st.title("👩‍💼 Admin Dashboard")

    st.subheader("➕ Create New User")
    new_username = st.text_input("New Username")
    new_password = st.text_input("New Password", type="password")

    if st.button("Create User"):
        if users_col.find_one({"username": new_username}):
            st.error("⚠️ Username already exists!")
        else:
            users_col.insert_one({"username": new_username, "password": new_password})
            st.success("User created successfully!")

    st.subheader("Registered Users:")
    for u in users_col.find():
        st.write(f"• {u['username']}")

    if st.button("Logout"):
        st.session_state.clear()
        st.session_state["page"] = "login"


# ---------------------------------------------------
# USER: Product Display + Add to Cart
# ---------------------------------------------------
def products_page():
    st.title("🛍 Products")

    products = list(products_col.find())

    if not products:
        st.info("No products found in database.")
        return

    for product in products:
        st.write("---")
        st.write(f"### {product['name']}")
        st.write(f"Price: ₹{product['price']}")
        st.write(f"Stock: {product['stock']}")

        qty = st.number_input(f"Quantity for {product['id']}", min_value=1, max_value=product['stock'], key=f"qty_{product['id']}")

        if st.button(f"Add to Cart: {product['id']}"):
            cart = st.session_state.get("cart", {})

            if product["id"] in cart:
                cart[product["id"]]["qty"] += int(qty)
            else:
                cart[product["id"]] = {
                    "name": product["name"],
                    "price": product["price"],
                    "qty": int(qty)
                }

            st.session_state["cart"] = cart
            st.success(f"Added {qty} × {product['name']} to cart!")


    if st.button("Go to Cart"):
        st.session_state["page"] = "user_cart"


# ---------------------------------------------------
# User Cart Page
# ---------------------------------------------------
def user_cart_page():
    st.title("🛒 Your Cart")

    cart = st.session_state.get("cart", {})

    if not cart:
        st.info("Your cart is empty.")
        return

    total = 0
    for pid, item in cart.items():
        line_total = item["price"] * item["qty"]
        st.write(f"{item['name']} — ₹{item['price']} × {item['qty']} = ₹{line_total}")
        total += line_total

    st.write(f"### Total: ₹{total}")

    if st.button("Buy Now"):
        out_of_stock = []

        for pid, item in cart.items():
