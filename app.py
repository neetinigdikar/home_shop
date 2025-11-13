import streamlit as st
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

# ---------------------------------------------------
# MongoDB Connection (secure via secrets)
# ---------------------------------------------------
MONGO_URI = st.secrets["MONGO"]["MONGO_URI"]
client = MongoClient(MONGO_URI)
db = client["home_shop_db"]

users_col = db["users"]
products_col = db["products"]
orders_col = db["orders"]

# ---------------------------------------------------
# ADMIN CREDENTIALS (HARDCODED)
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
            users_col.insert_one({"username": new_username, "password": new_password})
            st.success("✅ User created successfully!")

    st.subheader("👥 Registered Users")
    users = list(users_col.find())
    if users:
        for u in users:
            st.write(f"• {u['username']}")
    else:
        st.info("No users created yet.")

    if st.button("Logout"):
        st.session_state.clear()
        st.session_state["page"] = "login"


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
            st.session_state["user_id"] = str(user["_id"])
            st.session_state["is_admin"] = False
            st.session_state["page"] = "user"
            st.success("✅ Login successful!")
        else:
            st.error("❌ Invalid username or password")


# ---------------------------------------------------
# USER SHOPPING PAGE
# ---------------------------------------------------
def user_page():
    st.title(f"👤 Welcome, {st.session_state['username']}")

    cart = st.session_state.get("cart", {})

    st.subheader("🛒 Your Cart")

    if cart:
        total = 0
        for pid, item in cart.items():
            st.write(f"{item['name']} — ₹{item['price']} × {item['qty']} = ₹{item['price'] * item['qty']}")
            total += item["price"] * item["qty"]

        st.write(f"### Total: ₹{total}")

        if st.button("Buy Now"):
            out_of_stock = []

            for pid, item in cart.items():
                product = products_col.find_one({"_id": ObjectId(pid)})
                if not product or product.get("stock", 0) < item["qty"]:
                    out_of_stock.append(item["name"])

            if out_of_stock:
                st.error("❌ Out of stock: " + ", ".join(out_of_stock))
            else:
                orders_col.insert_one({
                    "user": st.session_state["username"],
                    "user_id": st.session_state["user_id"],
                    "items": [{"product_id": pid, **item} for pid, item in cart.items()],
                    "total": total,
                    "created_at": datetime.utcnow(),
                })

                for pid, item in cart.items():
                    products_col.update_one(
                        {"_id": ObjectId(pid)},
                        {"$inc": {"stock": -item["qty"]}}
                    )

                st.success("✅ Order placed successfully!")
                st.session_state["cart"] = {}

    else:
        st.info("🛍️ Your cart is empty.")

    if st.button("Logout"):
        st.session_state.clear()
        st.session_state["page"] = "login"


# ---------------------------------------------------
# LOGIN SELECTION PAGE
# ---------------------------------------------------
def login_selection_page():
    st.title("🔐 Login Portal")

    login_type = st.radio("Login as:", ["User", "Admin"])

    if login_type == "Admin":
        admin_user = st.text_input("Admin Username")
        admin_pass = st.text_input("Admin Password", type="password")

        if st.button("Admin Login"):
            if admin_user == ADMIN_USERNAME and admin_pass == ADMIN_PASSWORD:
                st.session_state["logged_in"] = True
                st.session_state["is_admin"] = True
                st.session_state["page"] = "admin"
                st.success("✅ Admin login successful!")
            else:
                st.error("❌ Invalid admin credentials")

    else:
        user_login_page()


# ---------------------------------------------------
# MAIN ROUTER
# ---------------------------------------------------
def main():
    page = st.session_state.get("page", "login")

    if page == "login":
        login_selection_page()
    elif page == "admin":
        admin_page()
    elif page == "user":
        user_page()


# ---------------------------------------------------
# RUN APP
# ---------------------------------------------------
if __name__ == "__main__":
    main()
