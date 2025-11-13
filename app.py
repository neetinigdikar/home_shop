import streamlit as st
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

# ---------------------------------------------------
# DATABASE CONNECTION (SECURE)
# ---------------------------------------------------
MONGO_URI = st.secrets["MONGO"]["MONGO_URI"]
client = MongoClient(MONGO_URI)
db = client["home_shop_db"]

users_col = db["users"]          # stores all users created by admin
products_col = db["products"]    # your products collection
orders_col = db["orders"]        # order collection

# ---------------------------------------------------
# ADMIN LOGIN (HARDCODED)
# ---------------------------------------------------
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


# ---------------------------------------------------
# ADMIN DASHBOARD
# ---------------------------------------------------
def admin_page():
    st.title("👩‍💼 Admin Dashboard")

    st.subheader("➕ Create New User")

    new_username = st.text_input("Enter new username")
    new_password = st.text_input("Enter new password", type="password")

    if st.button("Create User"):
        if users_col.find_one({"username": new_username}):
            st.error("⚠️ Username already exists!")
        else:
            users_col.insert_one({
                "username": new_username,
                "password": new_password
            })
            st.success("✅ User created successfully!")

    st.subheader("👥 All Registered Users")

    users = list(users_col.find())
    for user in users:
        st.write(f"• {user['username']}")

    if st.button("Logout"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.experimental_rerun()


# ---------------------------------------------------
# USER LOGIN PAGE
# ---------------------------------------------------
def user_login_page():
    st.title("👤 User Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = users_col.find_one({"username": username, "password": password})

        if user:
            st.session_state["logged_in"] = True
            st.session_state["username"] = user["username"]
            st.session_state["user_id"] = str(user["_id"])
            st.session_state["is_admin"] = False
            st.success("✅ User login successful!")
            st.experimental_rerun()
        else:
            st.error("❌ Invalid username or password")


# ---------------------------------------------------
# SHOPPING CART PAGE FOR USERS
# ---------------------------------------------------
def user_page():
    st.title(f"👤 Welcome, {st.session_state['username']}")

    cart = st.session_state.get("cart", {})

    st.subheader("🛒 Your Cart")
    if cart:
        total = 0.0
        for pid, item in cart.items():
            st.write(f"{item['name']} — ₹{item['price']} × {item['qty']} = ₹{item['price'] * item['qty']}")
            total += item["price"] * item["qty"]

        st.write(f"### 💰 Total: ₹{total}")

        if st.button("Buy Now"):
            out_of_stock = []

            for pid, item in cart.items():
                prod = products_col.find_one({"_id": ObjectId(pid)})
                if not prod or prod.get("stock", 0) < item["qty"]:
                    out_of_stock.append(item["name"])

            if out_of_stock:
                st.error(f"❌ Out of stock: {', '.join(out_of_stock)}")
            else:
                orders_col.insert_one({
                    "user": st.session_state["username"],
                    "user_id": st.session_state["user_id"],
                    "items": [
                        {"product_id": pid, "name": item["name"], "price": item["price"], "qty": item["qty"]}
                        for pid, item in cart.items()
                    ],
                    "total": total,
                    "created_at": datetime.utcnow()
                })

                for pid, item in cart.items():
                    products_col.update_one(
                        {"_id": ObjectId(pid)},
                        {"$inc": {"stock": -item["qty"]}}
                    )

                st.success("✅ Order placed successfully!")
                st.session_state["cart"] = {}
                st.experimental_rerun()
    else:
        st.info("🛍️ Your cart is empty.")

    if st.button("Logout"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.experimental_rerun()


# ---------------------------------------------------
# LOGIN CHOICE PAGE
# ---------------------------------------------------
def login_selection_page():
    st.title("🔐 Login Portal")
    st.subheader("Choose login type:")

    choice = st.radio("Login as:", ["User", "Admin"])

    if choice == "Admin":
        admin_user = st.text_input("Admin Username")
        admin_pass = st.text_input("Admin Password", type="password")

        if st.button("Admin Login"):
            if admin_user == ADMIN_USERNAME and admin_pass == ADMIN_PASSWORD:
                st.session_state["logged_in"] = True
                st.session_state["is_admin"] = True
                st.success("✅ Admin login successful!")
                st.experimental_rerun()
            else:
                st.error("❌ Invalid admin credentials")

    else:
        user_login_page()


# ---------------------------------------------------
# MAIN ROUTING LOGIC
# ---------------------------------------------------
def main():
    if not st.session_state.get("logged_in"):
        login_selection_page()
    else:
        if st.session_state.get("is_admin"):
            admin_page()
        else:
            user_page()


if __name__ == "__main__":
    main()
