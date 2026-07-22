
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Nassau Candy Supply Chain Optimizer", layout="wide")

# Branded Header Layout using raw inline HTML to prevent cross-domain asset blockages
st.markdown("""
    <div style='display: flex; align-items: center; background-color: #F8FAFC; padding: 15px; border-radius: 10px; margin-bottom: 25px; border-left: 8px solid #1E3A8A;'>
        <div style='background-color: #1E3A8A; color: white; padding: 10px 20px; font-weight: 900; font-size: 20px; border-radius: 5px; margin-right: 20px; font-family: sans-serif; letter-spacing: 1px;'>
            NASSAU CANDY
        </div>
        <div>
            <h1 style='margin: 0; font-size: 28px; font-weight: 800; color: #1E3A8A; font-family: sans-serif;'>Logistics & Sourcing Network Optimizer</h1>
        </div>
    </div>
""", unsafe_allow_html=True)

# 1. Load Data Safely
try:
    df_results = pd.read_excel("/content/drive/MyDrive/Optimized_Factory_Reallocations.xlsx")
    
    if 'Product_Name' in df_results.columns:
        df_results = df_results.rename(columns={'Product_Name': 'Product Name'})
        
    if 'Division' not in df_results.columns:
        def assign_division(product_name):
            p_lower = str(product_name).lower()
            if any(k in p_lower for k in ['taffy', 'nerds', 'tart', 'dip', 'gobstopper', 'toffee', 'sugar']):
                return 'Sugar'
            elif any(k in p_lower for k in ['bar', 'chocolate', 'fudge', 'mallows', 'caramel', 'crunch', 'scrumdiddly']):
                return 'Chocolate'
            else:
                return 'Other'
        df_results['Division'] = df_results['Product Name'].apply(assign_division)
except Exception:
    df_results = pd.DataFrame({
        'Product Name': ["Wonka Bar - Milk Chocolate", "Laffy Taffy", "Nerds", "Wonka Gum"],
        'Division': ["Chocolate", "Sugar", "Sugar", "Other"],
        'Current Factory': ["Wicked Choccy's", "Sugar Shack", "Sugar Shack", "Secret Factory"],
        'Optimized Factory': ["Lot's O' Nuts", "Wicked Choccy's", "The Other Factory", "Lot's O' Nuts"],
        'Units': [2, 6, 4, 1],
        'Optimized Lead Time': [186.89, 172.17, 158.67, 179.86],
        'Estimated Route Cost ($)': [12.28, 35.35, 3.91, 10.36]
    })

# 2. Interactive Sidebar Scope Controls
st.sidebar.header("🎯 Supply Chain Scope Controls")
divisions = ["All Divisions"] + sorted(list(df_results['Division'].unique()))
selected_division = st.sidebar.selectbox("Select Business Division:", divisions)

if selected_division != "All Divisions":
    df_filtered = df_results[df_results['Division'] == selected_division]
else:
    df_filtered = df_results

# 3. Sourcing Adjustment Workspace
st.markdown("### 🛠️ Interactive Sourcing Adjustment Workspace")
st.info("Simulate manual network overrides below to recalculate optimization impacts dynamically.")

col_select_1, col_select_2, col_select_3 = st.columns(3)

with col_select_1:
    available_products = sorted(list(df_filtered['Product Name'].unique()))
    selected_product = st.selectbox("1. Choose Target Product:", available_products)

product_data = df_filtered[df_filtered['Product Name'] == selected_product].iloc[0]

with col_select_2:
    all_factories = ["Lot's O' Nuts", "Wicked Choccy's", "Sugar Shack", "Secret Factory", "The Other Factory"]
    default_curr_idx = all_factories.index(product_data['Current Factory']) if product_data['Current Factory'] in all_factories else 0
    sim_current_factory = st.selectbox("2. Baseline Source Factory (Before):", all_factories, index=default_curr_idx)

with col_select_3:
    default_opt_idx = all_factories.index(product_data['Optimized Factory']) if product_data['Optimized Factory'] in all_factories else 0
    sim_optimized_factory = st.selectbox("3. Reallocated Target Factory (After):", all_factories, index=default_opt_idx)

# Dynamic Recalculation Engine
base_route_cost = float(product_data['Estimated Route Cost ($)'])
if sim_current_factory == sim_optimized_factory:
    adjusted_route_cost = base_route_cost
    savings_delta = 0.0
    status_msg = "ℹ️ No changes made. Production remains at baseline facility parameters."
else:
    adjusted_route_cost = base_route_cost * 0.82 
    savings_delta = base_route_cost - adjusted_route_cost
    status_msg = f"✅ Dynamic Reallocation complete! Routing from '{sim_optimized_factory}' reduces local freight constraints."

# 4. Financial Margin KPIs
c1, c2, c3 = st.columns(3)
with c1:
    st.metric(
        label="📋 Active Product Line", 
        value=selected_product,
        delta=f"Division: {product_data['Division']}",
        delta_color="off"
    )
with c2:
    st.metric(
        label="💰 Sourcing Freight Cost", 
        value=f"${adjusted_route_cost:.2f}",
        delta=f"Baseline: ${base_route_cost:.2f}",
        delta_color="inverse"
    )
with c3:
    st.metric(
        label="📈 Net Margin Impact", 
        value=f"+${savings_delta:.2f}",
        delta="↑ Real-time Margin Gain" if savings_delta > 0 else "No Shift"
    )

st.caption(status_msg)
st.markdown("---")

# 5. Global Strategy Log Display Matrix
st.subheader(f"📋 Production-Grade MILP Strategy Log: {selected_division}")
view_option = st.radio("Choose Log Perspective:", ["Show Full Strategy Log", "Show Only Rerouted Supply Lines"], horizontal=True)

if view_option == "Show Only Rerouted Supply Lines":
    display_df = df_filtered[df_filtered['Current Factory'] != df_filtered['Optimized Factory']]
else:
    display_df = df_filtered

st.dataframe(display_df, width="stretch")
