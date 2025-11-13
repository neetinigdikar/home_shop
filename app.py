import streamlit as st
from pymongo import MongoClient
from datetime import datetime

# ---------------------------------------------------
# MongoDB Connection (URI stored in secrets.toml)
# ---------------------------------------------------
MONGO_URI = st.secrets["MONGO"]["MONGO_URI"]
client = MongoClient(MONGO_URI)
db = client["home_shop_db"]

users_col = db["users"]
products_col = db["products"]
orders_col = db["orders"]

# ---------------------------------------------------
# ADMIN LOGIN (Hardcoded)
# ---------------------------------------------------
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# ---------------------------------------------------
# ADMIN DASHBOARD
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
            users_col.insert_one({
                "username": new_username,
                "password": new_password
            })
            st.success("✅ User created successfully!")

    st.subheader("👥 All Users")
    for user in users_col.find():
        st.write(f"• {user['username']}")

    if st.button("Logout"):
        st.session_state.clear()
        st.session_state["page"] = "login"
        st.session_state["navigate"] = True


# ---------------------------------------------------
# USER LOGIN PAGE
# ---------------------------------------------------
def user_login_page():
    st.title("👤 User Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("User Login"):
        user = users_col.find_one({"username": username, "password": password})

        if user:
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.session_state["is_admin"] = False
            st.session_state["page"] = "user"
            st.session_state["navigate"] = True
        else:
            st.error("❌ Invalid username or password")


# ---------------------------------------------------
# USER DASHBOARD
# ---------------------------------------------------
def user_page():
    st.title(f"👤 Welcome, {st.session_state['username']}")

    cart = st.session_state.get("cart", {})
    st.subheader("🛒 Your Cart")

    if cart:
        total = 0

        for pid, item in cart.items():
            st.write(f"{item['name']} — ₹{item['price']} × {item['qty']} = ₹{item[']()
