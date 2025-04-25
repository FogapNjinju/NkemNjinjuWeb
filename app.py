import streamlit as st
import pandas as pd
import datetime
import os
import plotly.express as px
from PIL import Image
import zipfile
import io

# Define file paths
tenants_file = "tenants.csv"
payments_file = "payments.csv"
receipts_folder = "receipts"

# Initialize CSV files and folders if not present
def init_files():
    if not os.path.exists(tenants_file):
        df = pd.DataFrame(columns=["Tenant ID", "Name", "Apartment", "Phone", "Location", "Registration Date"])
        df.to_csv(tenants_file, index=False)
    if not os.path.exists(payments_file):
        df = pd.DataFrame(columns=["Tenant ID", "Month", "Amount", "Date", "Receipt", "Location"])
        df.to_csv(payments_file, index=False)
    if not os.path.exists(receipts_folder):
        os.makedirs(receipts_folder)

init_files()

def load_data():
    tenants = pd.read_csv(tenants_file)
    payments = pd.read_csv(payments_file)
    return tenants, payments

def save_tenant(tenant_id, name, apartment, phone, location):
    tenants = pd.read_csv(tenants_file)
    registration_date = datetime.datetime.now().strftime("%Y-%m")
    new_tenant = pd.DataFrame([{
        "Tenant ID": tenant_id,
        "Name": name,
        "Apartment": apartment,
        "Phone": phone,
        "Location": location,
        "Registration Date": registration_date
    }])
    tenants = pd.concat([tenants, new_tenant], ignore_index=True)
    tenants.to_csv(tenants_file, index=False)

def save_payment(tenant_id, month, amount, receipt_img, location):
    payments = pd.read_csv(payments_file)
    receipt_path = ""
    if receipt_img is not None:
        receipt_filename = f"{tenant_id}_{month}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        receipt_path = os.path.join(receipts_folder, receipt_filename)
        with open(receipt_path, "wb") as f:
            f.write(receipt_img.getbuffer())
    new_payment = pd.DataFrame([{
        "Tenant ID": tenant_id,
        "Month": month,
        "Amount": amount,
        "Date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "Receipt": receipt_path,
        "Location": location
    }])
    payments = pd.concat([payments, new_payment], ignore_index=True)
    payments.to_csv(payments_file, index=False)

def delete_tenant(tenant_id):
    tenants = pd.read_csv(tenants_file)
    tenants = tenants[tenants["Tenant ID"] != tenant_id]
    tenants.to_csv(tenants_file, index=False)

def delete_payment(payment_index):
    payments = pd.read_csv(payments_file)
    receipt_path = payments.loc[payment_index, "Receipt"]
    if pd.notna(receipt_path) and os.path.exists(receipt_path):
        os.remove(receipt_path)
    payments.drop(index=payment_index, inplace=True)
    payments.to_csv(payments_file, index=False)

def get_due_months(tenant_id, registration_date, rent_amount=100):
    current_month = datetime.datetime.now().strftime("%Y-%m")
    date_range = pd.date_range(start=registration_date, end=current_month, freq='MS').strftime("%Y-%m")
    payments = pd.read_csv(payments_file)
    paid_months = payments[payments["Tenant ID"] == tenant_id]["Month"].unique()
    due_months = [m for m in date_range if m not in paid_months]
    total_due = len(due_months) * rent_amount
    return due_months, total_due

# Styling
st.set_page_config(page_title="Tenant Manager", layout="wide")
with st.sidebar:
    # st.image("https://cdn-icons-png.flaticon.com/512/3940/3940057.png", width=100)
    st.title("🏠 Tenant Manager")
    menu = [
        ("Register Tenant", "fa-user-plus"),
        ("Record Payment", "fa-credit-card"),
        ("Payment Status", "fa-money-check-alt"),
        ("All Tenants", "fa-users"),
        ("Reports & Charts", "fa-chart-bar")
    ]
    choice = st.selectbox("Navigation", [item[0] for item in menu])

st.markdown("""
    <style>
        .reportview-container {
            background: #f5f5f5;
            padding: 1rem;
        }
        .block-container {
            padding: 2rem;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .stButton button {
            background-color: #0072E3;
            color: white;
            border-radius: 10px;
            padding: 0.5em 1.5em;
        }
        .stTextInput > div > div > input {
            border-radius: 10px;
        }
        .stSelectbox select {
            border-radius: 10px;
        }
        .stFileUploader {
            border-radius: 10px;
        }
        h1, h2, h3 {
            color: #0072E3;
        }
        .fa {
            margin-right: 10px;
        }
    </style>
""", unsafe_allow_html=True)

st.title("📋 Nkem-Njinju Tenant Management System")

# Displaying the menu with Font Awesome icons
icon_dict = dict(menu)
icon = icon_dict.get(choice, "fa-cogs")

st.markdown(f"<h3><i class='fas {icon}'></i> {choice}</h3>", unsafe_allow_html=True)

if choice == "Register Tenant":
    st.subheader("📅 Register a New Tenant")
    tenant_id = st.text_input("Tenant ID", help="Enter a unique identifier for the tenant.")
    name = st.text_input("Full Name", help="Enter the full name of the tenant.")
    apartment = st.text_input("Apartment", help="Enter the apartment number or name.")
    phone = st.text_input("Phone Number", help="Enter the phone number of the tenant.")
    location = st.selectbox("Location", ["Checkpoint", "Sossoliso", "Molyko"], help="Select the location of the apartment.")

    if st.button("Register Tenant"):
        if tenant_id and name and apartment:
            save_tenant(tenant_id, name, apartment, phone, location)
            st.success(f"✅ Tenant {name} registered successfully.")
        else:
            st.warning("⚠️ Please fill in all required fields.")

elif choice == "Record Payment":
    st.subheader("💳 Record a Payment")
    tenants, _ = load_data()
    tenant_ids = tenants["Tenant ID"].tolist()
    selected_id = st.selectbox("Select Tenant ID", tenant_ids, help="Select the tenant to record the payment.")

    # Check for the latest paid month of the tenant
    payments = pd.read_csv(payments_file)
    last_payment_month = payments[payments["Tenant ID"] == selected_id]["Month"].max()

    # If the tenant has already made a payment, display the latest paid month
    if last_payment_month:
        st.write(f"Last payment made for month: {last_payment_month}")
    
    # Input for the new payment month
    month = st.text_input("Month (YYYY-MM)", value=datetime.datetime.now().strftime("%Y-%m"), help="Enter the month for the payment (YYYY-MM).")
    
    # Input for amount and receipt
    amount = st.number_input("Amount Paid", min_value=0.0, help="Enter the amount paid for the month.")
    location = st.selectbox("Location", ["Checkpoint", "Sossoliso", "Molyko"], help="Select the payment location.")
    receipt = st.file_uploader("Upload Receipt Image", type=["png", "jpg", "jpeg"], help="Upload the payment receipt as an image.")

    if receipt:
        st.image(receipt, width=100, caption="Receipt Preview")

    if st.button("Save Payment"):
        save_payment(selected_id, month, amount, receipt, location)
        st.success("✅ Payment recorded successfully.")

elif choice == "Payment Status":
    st.subheader("📊 Payment Status Overview")
    tenants, payments = load_data()
    rent_amount = st.number_input("Monthly Rent Amount (default: 100)", value=100, help="Enter the monthly rent amount.")

    current_month = datetime.datetime.now().strftime("%Y-%m")
    st.markdown(f"### 🗓️ Current Month: {current_month}")

    search_term = st.text_input("🔍 Search by Name, Apartment, or Phone", help="Search for tenants by name, apartment, or phone number.")

    if search_term:
        tenants = tenants[tenants.apply(lambda row: search_term.lower() in row.to_string().lower(), axis=1)]

    for _, row in tenants.iterrows():
        registration_month = row.get("Registration Date")
        if pd.isna(registration_month) or registration_month == "":
            registration_month = datetime.datetime.now().strftime("%Y-%m")
        due_months, total_due = get_due_months(row["Tenant ID"], registration_date=registration_month, rent_amount=rent_amount)
        
        # Displaying the tenant's payment status
        with st.expander(f"{row['Name']} - Apartment {row['Apartment']}"):
            st.markdown(f"**Phone:** {row['Phone']}")
            st.markdown(f"**Location:** {row['Location']}")
            st.markdown(f"**Amount Owed:** 💰 {total_due} FCFA for {len(due_months)} month(s)")
            st.markdown(f"**Months Owing:** {', '.join(due_months) if due_months else '✅ None'}")
            if current_month in due_months:
                st.error("❌ Rent overdue for current month")
            else:
                st.success("✅ Rent paid for current month")

elif choice == "All Tenants":
    st.subheader("🏘️ All Tenants by Apartment")
    tenants, payments = load_data()

    search_term = st.text_input("🔍 Search by Name, Apartment or Phone", help="Search for tenants by name, apartment, or phone number.")

    if search_term:
        tenants = tenants[tenants.apply(lambda row: search_term.lower() in row.to_string().lower(), axis=1)]

    grouped = tenants.groupby("Apartment")

    for apartment, group in grouped:
        st.markdown(f"### 🏢 Apartment: {apartment}")
        for _, tenant in group.iterrows():
            tenant_id = tenant["Tenant ID"]
            total_paid = payments[payments["Tenant ID"] == tenant_id]["Amount"].sum()
            st.markdown(f"**{tenant['Name']}** | Phone: {tenant['Phone']} | Location: {tenant['Location']} | Paid: 💵 {total_paid} FCFA")
            if st.button(f"🗑️ Delete {tenant['Name']}", key=f"delete_{tenant_id}"):
                delete_tenant(tenant_id)
                st.success(f"Deleted tenant {tenant['Name']}.")
            st.markdown("---")

elif choice == "Reports & Charts":
    st.subheader("📈 Reports and Visualizations")
    tenants, payments = load_data()

    payments_summary = payments.merge(tenants, on="Tenant ID")
    apartment_summary = payments_summary.groupby("Apartment")["Amount"].sum().reset_index()
    fig = px.bar(apartment_summary, x="Apartment", y="Amount", title="Total Payments by Apartment")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("🧾 Monthly Payment Report")
    if not payments.empty:
        month_selected = st.selectbox("Select Month", sorted(payments["Month"].unique(), reverse=True))
        if month_selected:
            monthly = payments[payments["Month"] == month_selected].merge(tenants, on="Tenant ID")
            for idx, row in monthly.iterrows():
                st.markdown(f"**{row['Name']}** | Amount: {row['Amount']} FCFA | Date: {row['Date']}")
                if 'Receipt' in row and pd.notna(row['Receipt']) and os.path.exists(row['Receipt']):
                    st.image(row['Receipt'], width=300)
                if st.button(f"🗑️ Delete Payment of {row['Name']} ({row['Amount']} FCFA)", key=f"delpay_{idx}"):
                    delete_payment(idx)
                    st.success("Deleted payment record.")
            st.dataframe(monthly[["Tenant ID", "Name", "Apartment", "Amount", "Date"]])
    else:
        st.info("No payments recorded yet.")

    st.subheader("📥 Download All Receipts")
    if os.listdir(receipts_folder):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for filename in os.listdir(receipts_folder):
                filepath = os.path.join(receipts_folder, filename)
                zip_file.write(filepath, arcname=filename)
        zip_buffer.seek(0)
        st.download_button(
            label="⬇️ Download Receipts as ZIP",
            data=zip_buffer,
            file_name="all_receipts.zip",
            mime="application/zip"
        )
    else:
        st.info("No receipts found to download.")
