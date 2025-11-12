import streamlit as st
if cart:
total = 0.0
for pid, item in cart.items():
st.write(f"{item['name']} — ₹{item['price']} × {item['qty']} = ₹{item['price']*item['qty']}")
total += item['price']*item['qty']
st.write(f"**Total: ₹{total}**")
if st.button("Buy Now"):
# Validate stock
out_of_stock = []
for pid, item in cart.items():
prod = products_col.find_one({"_id": ObjectId(pid)})
if not prod or prod.get('stock',0) < item['qty']:
out_of_stock.append(item['name'])
if out_of_stock:
st.error(f"These items are out of stock or insufficient: {', '.join(out_of_stock)}")
else:
# create order
order = {
'user': st.session_state.get('username'),
'user_id': st.session_state.get('user_id'),
'items': [{ 'product_id': pid, 'name': item['name'], 'price': item['price'], 'qty': item['qty']} for pid,item in cart.items()],
'total': total,
'created_at': datetime.utcnow()
}
orders_col.insert_one(order)
# decrement stock
for pid, item in cart.items():
products_col.update_one({'_id': ObjectId(pid)}, {'$inc': {'stock': -int(item['qty'])}})
st.success('Order placed successfully!')
st.session_state['cart'] = {}
st.experimental_rerun()
else:
st.info('Your cart is empty')


if st.button('Logout'):
for k in ['logged_in','is_admin','username','user_id','cart']:
if k in st.session_state:
del st.session_state[k]
st.experimental_rerun()




# -----------------------------
# Main routing
# -----------------------------
def main():
if not st.session_state.get('logged_in'):
login_page()
else:
if st.session_state.get('is_admin'):
admin_page()
else:
user_page()


if __name__ == '__main__':
main()