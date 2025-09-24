import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="KMRL Train Induction Dashboard", layout="wide")

# -----------------------------
# Helper: Simple Rule-based Assignment
# -----------------------------
def assign_trains(df, forced_service=None):
    results = []
    service_count = 0
    max_service = 15  # assume max 15 trains in service per night

    for _, row in df.iterrows():
        reason = []
        assignment = None

        # Forced override
        if forced_service and row["train_id"] == forced_service:
            assignment = "Service"
            reason.append("Forced into Service")
        else:
            # Rule-based allocation
            if row["fitness_ok"].lower() == "no":
                assignment = "Maintenance"
                reason.append("Fitness Certificate invalid")
            elif row["job_card_open"].lower() == "yes":
                assignment = "Maintenance"
                reason.append("Open Job Card")
            elif row["needs_cleaning"].lower() == "yes":
                assignment = "Standby"
                reason.append("Pending Cleaning")
            elif service_count < max_service:
                assignment = "Service"
                reason.append("Meets all conditions")
                service_count += 1
            else:
                assignment = "Standby"
                reason.append("Service quota filled")

        results.append({
            "train_id": row["train_id"],
            "assignment": assignment,
            "reason": ", ".join(reason),
            "mileage": row["mileage"],
            "branding_need": row["branding_need"]
        })

    return pd.DataFrame(results)

# -----------------------------
# Streamlit UI
# -----------------------------
st.title("🚆 AI-Driven Train Induction Planning – KMRL")
st.markdown("Prototype dashboard (MVP) for internal hackathon round.")

tabs = st.tabs(["📂 Upload & Validate Data", "📊 Induction Plan", "⚡ What-If Scenario"])

# -----------------------------
# Tab 1: Upload
# -----------------------------
with tabs[0]:
    st.header("Upload Train Data")

    st.markdown("""
    **Expected CSV columns:**  
    - train_id  
    - fitness_ok (Yes/No)  
    - job_card_open (Yes/No)  
    - mileage (numeric)  
    - needs_cleaning (Yes/No)  
    - branding_need (High/Low/None)  
    """)

    uploaded = st.file_uploader("Upload nightly CSV", type="csv")

    if uploaded:
        df = pd.read_csv(uploaded)
        st.success("✅ Data uploaded successfully!")
        st.dataframe(df)

        # Quick validation
        st.subheader("Validation Checks")
        issues = []
        if "no" in df["fitness_ok"].str.lower().values:
            issues.append("Some trains have invalid fitness certificates.")
        if "yes" in df["job_card_open"].str.lower().values:
            issues.append("Some trains still have open job-cards.")
        if "yes" in df["needs_cleaning"].str.lower().values:
            issues.append("Some trains require cleaning.")

        if issues:
            for i in issues:
                st.warning("⚠️ " + i)
        else:
            st.info("✅ No major validation issues found.")

# -----------------------------
# Tab 2: Induction Plan
# -----------------------------
with tabs[1]:
    st.header("Optimized Induction Plan")

    if uploaded:
        plan_df = assign_trains(df)
        st.subheader("📋 Allocation Table")
        st.dataframe(plan_df)

        # Charts
        st.subheader("📊 Visualizations")
        col1, col2 = st.columns(2)

        with col1:
            pie = px.pie(plan_df, names="assignment", title="Distribution of Train Assignments")
            st.plotly_chart(pie, use_container_width=True)

        with col2:
            bar = px.bar(plan_df, x="train_id", y="mileage", color="assignment",
                         title="Mileage by Train (Service/Standby/Maintenance)")
            st.plotly_chart(bar, use_container_width=True)
    else:
        st.info("Please upload data first in Tab 1.")

# -----------------------------
# Tab 3: What-If Scenario
# -----------------------------
with tabs[2]:
    st.header("⚡ What-If Scenario Analysis")

    if uploaded:
        train_choice = st.selectbox("Select a train to force into Service", df["train_id"].unique())
        if st.button("Recalculate Plan"):
            new_plan = assign_trains(df, forced_service=train_choice)
            st.success(f"Plan recalculated with Train {train_choice} forced into Service")
            st.dataframe(new_plan)
    else:
        st.info("Please upload data first in Tab 1.")
