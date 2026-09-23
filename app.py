import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import time
import math

# ---------------------------------------------------------
# 1. PAGE CONFIGURATION & STYLING
# ---------------------------------------------------------
st.set_page_config(page_title="Smart Wallet", layout="wide", page_icon="🎓")

# Custom CSS for a clean look
st.markdown("""
<style>
    .big-font { font-size: 20px !important; font-weight: bold; }
    div[data-testid="stMetric"] {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #dee2e6;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    .stButton button { width: 100%; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. SESSION STATE (Memory)
# ---------------------------------------------------------
if "balance" not in st.session_state:
    st.session_state.balance = 0.0

if "goal_amount" not in st.session_state:
    st.session_state.goal_amount = 0.0

if "my_bills" not in st.session_state:
    st.session_state.my_bills = [] 

if "expenses" not in st.session_state:
    st.session_state.expenses = pd.DataFrame(columns=["Date", "Amount", "Category", "Note", "Fraud_Flag"])

# ---------------------------------------------------------
# 3. HELPER FUNCTION
# ---------------------------------------------------------
def check_if_paid_this_month(bill_name):
    if st.session_state.expenses.empty:
        return False
    
    today = datetime.now()
    curr_month = today.month
    curr_year = today.year
    
    df = st.session_state.expenses
    # Fix date format issues safely
    try:
        df["Date"] = pd.to_datetime(df["Date"])
    except:
        pass 
    
    mask = (
        (df["Category"] == "🏠 Bills") & 
        (df["Note"] == bill_name) & 
        (df["Date"].dt.month == curr_month) & 
        (df["Date"].dt.year == curr_year)
    )
    return not df[mask].empty

# ---------------------------------------------------------
# 4. SIDEBAR (Inputs)
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Wallet Setup")
    
    # INCOME
    with st.expander("💵 Add Money (Income)", expanded=True):
        income_amt = st.number_input("Amount (₹)", min_value=0.0, step=100.0, key="inc_input")
        if st.button("➕ Add to Wallet"):
            if income_amt > 0:
                st.session_state.balance += income_amt
                st.balloons()
                st.success(f"Added ₹{income_amt}!")
                time.sleep(1)
                st.rerun()

    # GOAL
    with st.expander("🎯 Savings Goal"):
        curr_goal = float(st.session_state.goal_amount)
        new_goal = st.number_input("Target Amount (₹)", min_value=0.0, value=curr_goal, step=500.0)
        if st.button("Update Goal"):
            st.session_state.goal_amount = new_goal
            st.success("Goal Updated!")
            time.sleep(0.5)
            st.rerun()

    # BILLS
    st.divider()
    st.subheader("🧾 Manage Bills")
    
    c1, c2 = st.columns(2)
    new_bill_name = c1.text_input("Bill Name", placeholder="e.g. WiFi")
    new_bill_amt = c2.number_input("Cost (₹)", min_value=0.0, step=100.0, key="bill_amt")
    
    if st.button("Add Bill"):
        if new_bill_name and new_bill_amt > 0:
            st.session_state.my_bills.append({"name": new_bill_name, "amount": new_bill_amt})
            st.success(f"Added {new_bill_name}!")
            time.sleep(0.5)
            st.rerun()

    if st.session_state.my_bills:
        st.write("---")
        st.write("**Active Bills:**")
        for i, bill in enumerate(st.session_state.my_bills):
            col_txt, col_del = st.columns([3, 1])
            col_txt.text(f"{bill['name']}: ₹{bill['amount']}")
            if col_del.button("❌", key=f"del_{i}"):
                st.session_state.my_bills.pop(i)
                st.rerun()

# ---------------------------------------------------------
# 5. MAIN DASHBOARD
# ---------------------------------------------------------
st.title("🎓 Smart Wallet")
st.markdown("### Manage pocket money, bills, and dreams.")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("💰 Wallet Balance", f"₹{st.session_state.balance:,.0f}")
with col2:
    st.metric("🎯 Goal Target", f"₹{st.session_state.goal_amount:,.0f}")
with col3:
    unpaid_total = 0
    for bill in st.session_state.my_bills:
        if not check_if_paid_this_month(bill['name']):
            unpaid_total += bill['amount']
    
    if st.session_state.goal_amount > 0:
        safe_spend = max(st.session_state.balance - st.session_state.goal_amount - unpaid_total, 0)
    else:
        safe_spend = max(st.session_state.balance - unpaid_total, 0)
    
    st.metric("✅ Safe to Spend", f"₹{safe_spend:,.0f}", delta=f"-₹{unpaid_total} bills due", delta_color="off")

st.divider()

# ---------------------------------------------------------
# 6. TABS
# ---------------------------------------------------------
tab_pay, tab_history, tab_predict = st.tabs(["⚡ Pay & Spend", "📜 History", "🔮 Dream Planner"])

# --- TAB 1: PAY ---
with tab_pay:
    # A. BILLS
    st.subheader("📅 Monthly Bills")
    if not st.session_state.my_bills:
        st.info("👈 Add bills in the Sidebar first!")
    else:
        cols = st.columns(3)
        for i, bill in enumerate(st.session_state.my_bills):
            with cols[i % 3]:
                is_paid = check_if_paid_this_month(bill['name'])
                with st.container(border=True):
                    st.markdown(f"**{bill['name']}**")
                    st.markdown(f"₹{bill['amount']}")
                    if is_paid:
                        st.button("✅ Paid", key=f"btn_paid_{i}", disabled=True)
                    else:
                        if st.button(f"Pay Now", key=f"pay_{i}"):
                            if st.session_state.balance >= bill['amount']:
                                st.session_state.balance -= bill['amount']
                                new_row = pd.DataFrame([{
                                    "Date": datetime.today(),
                                    "Amount": float(bill['amount']),
                                    "Category": "🏠 Bills",
                                    "Note": bill['name'],
                                    "Fraud_Flag": "No"
                                }])
                                st.session_state.expenses = pd.concat([st.session_state.expenses, new_row], ignore_index=True)
                                st.balloons()
                                st.success("Paid!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Low Balance!")

    st.divider()
    
    # B. DAILY SPEND (WITH EMOJIS)
    st.subheader("🍔 Daily Spend")
    c1, c2 = st.columns(2)
    daily_amt = c1.number_input("Amount", min_value=0.0, step=50.0, key="daily_amt")
    
    # Added Emojis here!
    daily_cat = c2.selectbox("Category", [
        "🍔 Food", 
        "🚕 Transport", 
        "🛍️ Shopping", 
        "🎉 Entertainment", 
        "💊 Health", 
        "📚 Education", 
        "Other"
    ])
    
    if st.button("💸 Spend Now"):
        if daily_amt > 0 and daily_amt <= st.session_state.balance:
            fraud = "High Value" if daily_amt > 5000 else "No"
            st.session_state.balance -= daily_amt
            new_row = pd.DataFrame([{
                "Date": datetime.today(),
                "Amount": float(daily_amt),
                "Category": daily_cat,
                "Note": daily_cat,
                "Fraud_Flag": fraud
            }])
            st.session_state.expenses = pd.concat([st.session_state.expenses, new_row], ignore_index=True)
            st.success("Saved!")
            time.sleep(0.5)
            st.rerun()
        elif daily_amt > st.session_state.balance:
            st.error("Insufficient Funds!")

# --- TAB 2: HISTORY ---
with tab_history:
    st.subheader("📜 Transaction Log")
    if not st.session_state.expenses.empty:
        df_display = st.session_state.expenses.copy()
        try:
            df_display["Date"] = pd.to_datetime(df_display["Date"]).dt.strftime('%Y-%m-%d')
        except:
            pass
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("No transactions yet.")

# --- TAB 3: DREAM PLANNER (FIXED & INTERACTIVE) ---
with tab_predict:
    st.subheader("🤖 AI Dream Consultant")
    st.info("Tell me your dream, and I will calculate when you can afford it!")
    
    # 1. Inputs
    dream_name = st.text_input("1. What is your dream?", placeholder="e.g. New Phone")
    dream_cost = st.number_input("2. Total Cost (₹)", min_value=0.0, step=500.0)
    save_speed = st.number_input("3. Monthly Savings (₹)", min_value=0.0, step=100.0)
    
    st.write("---")
    
    # 2. Logic (Fixed Triple Quote Error)
    if st.button("🔮 Calculate Date"):
        if dream_cost > 0 and save_speed > 0:
            months = math.ceil(dream_cost / save_speed)
            future_date = date.today() + timedelta(days=months*30)
            fmt_date = future_date.strftime('%B %Y')
            
            # Simple, safe display without complex formatting errors
            st.success(f"🎉 You can afford your **{dream_name}** by **{fmt_date}**!")
            st.write(f"It will take exactly **{months} months** of saving.")
            
            if months > 24:
                st.warning("That is a long time! Try increasing your monthly savings.")
        else:
            st.error("Please enter valid numbers for Cost and Savings.")
