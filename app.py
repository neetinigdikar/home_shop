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
# ADMIN LOGIN (HARDCODED)
# ---------------------------------------------------
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


# ---------------------------------------------------
# ADMIN PAGE
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
        st.experimental_rerun()


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
            st.session_state["page"] = "user"
            st.session_state["navigate"] = True
        else:
            st.error("❌ Invalid username or password")


# ---------------------------------------------------
# USER PAGE
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
                product = products_col.find_one({"id": pid})
                if not product or product["stock"] < item["qty"]:
                    out_of_stock.append(item["name"])

            if out_of_stock:
                st.error("Out of stock: " + ", ".join(out_of_stock))
            else:
                orders_col.insert_one({
                    "user": st.session_state["username"],
                    "items": [{"product_id": pid, **item} for pid, item in cart.items()],
                    "total": total,
                    "created_at": datetime.utcnow()
                })

                for pid, item in cart.items():
                    products_col.update_one(
                        {"id": pid},
                        {"$inc": {"stock": -item["qty"]}}
                    )

                st.success("Order placed!")
                st.session_state["cart"] = {}

    else:
        st.info("🛍️ Cart is empty.")

    if st.button("Logout"):
        st.session_state.clear()
        st.session_state["page"] = "login"
        st.experimental_rerun()


# ---------------------------------------------------
# LOGIN SELECTION PAGE
# ---------------------------------------------------
def login_selection_page():
    st.title("🔐 Login Portal")

    choice = st.radio("Login as:", ["User", "Admin"])

    # ---------------------- ADMIN LOGIN -------------------------
    if choice == "Admin":
        admin_user = st.text_input("Admin Username")
        admin_pass = st.text_input("Admin Password", type="password")

        if st.button("Admin Login"):
            if admin_user == ADMIN_USERNAME and admin_pass == ADMIN_PASSWORD:
                st.session_state["logged_in"] = True
                st.session_state["is_admin"] = True
                st.session_state["page"] = "admin"
                st.session_state["navigate"] = True   # <-- Trigger navigation
            else:
                st.error("❌ Invalid admin credentials")

    # ---------------------- USER LOGIN --------------------------
    else:
        user_login_page()


# ---------------------------------------------------
# MAIN ROUTER
# ---------------------------------------------------
def main():

    # Trigger safe rerun when needed
    if st.session_state.get("navigate"):
        st.session_state["navigate"] = False
        st.experimental_rerun()

    page = st.session_state.get("page", "login")

    if page == "login":
        login_selection_page()
    elif page == "admin":
        admin_page()
    elif page == "user":
        user_page()


if __name__ == "__main__":
    main()
