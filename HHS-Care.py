from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from statsmodels.tsa.holtwinters import ExponentialSmoothing


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    repo_root = Path(__file__).resolve().parent
    candidates = [
        repo_root / "processed_dataset_with_new_columns.csv",
        repo_root.parent / "processed_dataset_with_new_columns.csv",
        repo_root / "HHS_Unaccompanied_Alien_Children_Program.csv",
        repo_root / "data" / "HHS_Unaccompanied_Alien_Children_Program.csv",
        repo_root.parent / "HHS_Unaccompanied_Alien_Children_Program.csv",
    ]

    for path in candidates:
        if path.exists():
            df = pd.read_csv(path)
            return df

    raise FileNotFoundError("Unable to find the HHS dataset CSV in the repository or workspace.")


@st.cache_data(show_spinner=False)
def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [col.strip() for col in df.columns]

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)

    numeric_columns = [
        "Children apprehended and placed in CBP custody*",
        "Children in CBP custody",
        "Children transferred out of CBP custody",
        "Children in HHS Care",
        "Children discharged from HHS Care",
    ]

    for column in numeric_columns:
        df[column] = (
            df[column]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.replace("$", "", regex=False)
            .str.strip()
        )
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)

    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    df["DayOfWeek"] = df["Date"].dt.dayofweek

    df["CBP_to_HHS_Transfer_Rate"] = (
        df["Children transferred out of CBP custody"] / df["Children in CBP custody"].replace(0, pd.NA)
    ).fillna(0)
    df["HHS_Discharge_Rate"] = (
        df["Children discharged from HHS Care"] / df["Children in HHS Care"].replace(0, pd.NA)
    ).fillna(0)
    df["Backlog_Accumulation_Rate"] = df["Children in HHS Care"].pct_change().fillna(0) * 100
    df["Daily_Net_Accumulation"] = (
        df["Children apprehended and placed in CBP custody*"] - df["Children discharged from HHS Care"]
    )
    df["Combined_Backlog"] = (
        df["Children in CBP custody"] + df["Children in HHS Care"] - df["Children discharged from HHS Care"]
    )

    return df


def style_plot(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=30, b=10),
        font=dict(color="#e5e7eb"),
    )
    return fig


def build_threshold_bar(total_entries: int, total_transfers: int, total_discharges: int, avg_transfer_rate: float, avg_discharge_rate: float, transfer_threshold: float, discharge_threshold: float) -> go.Figure:
    max_flow = max(total_entries, total_transfers, total_discharges, 1)
    apprehended_score = min(total_entries / max_flow, 1.0)
    transfer_score = min(avg_transfer_rate / transfer_threshold if transfer_threshold > 0 else 0.0, 1.0)
    discharge_score = min(avg_discharge_rate / discharge_threshold if discharge_threshold > 0 else 0.0, 1.0)

    fig = go.Figure(
        go.Bar(
            x=[apprehended_score, transfer_score, discharge_score],
            y=["Apprehended", "Transfer", "Discharge"],
            orientation="h",
            marker=dict(color=["#8ecae6", "#f6e58d", "#90ee90"], line=dict(width=0)),
            hovertemplate="%{y}: %{x:.2%}<extra></extra>",
        )
    )
    fig.update_layout(
        height=220,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(range=[0, 1], title="Relative level", showgrid=False, zeroline=False),
        yaxis=dict(autorange="reversed", showgrid=False),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return style_plot(fig)


def render_kpi_card(title: str, value: str, subtitle: str, color: str) -> None:
    st.markdown(
        f"<div style='border:1px solid {color}; border-left:5px solid {color}; border-radius:8px; background:rgba(248,250,252,0.06); padding:12px 14px; min-height:120px;'>"
        f"<div style='font-size:0.85rem; color:#94a3b8; margin-bottom:6px;'>{title}</div>"
        f"<div style='font-size:1.3rem; font-weight:700; color:#f8fafc;'>{value}</div>"
        f"<div style='font-size:0.82rem; color:#cbd5e1; margin-top:6px;'>{subtitle}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def build_dashboard(df: pd.DataFrame) -> None:
    st.set_page_config(page_title="HHS Care Analytics", page_icon="📊", layout="wide")
    repo_root = Path(__file__).resolve().parent.parent
    logo_candidates = [
        repo_root / "Screenshot 2026-07-11 181430.png",
        repo_root / "logo.png",
        repo_root / "assets" / "logo.png",
    ]
    # Fallback to SVG if no PNG is present
    svg_candidates = [
        repo_root / "logo.svg",
        repo_root / "assets" / "logo.svg",
    ]
    if logo_path is None:
        logo_path = next((path for path in svg_candidates if path.exists()), None)
    logo_path = next((path for path in logo_candidates if path.exists()), None)

    header_col1, header_col2 = st.columns([0.45, 9.55], vertical_alignment="center")
    with header_col1:
        if logo_path is not None:
            st.image(str(logo_path), width=48)
    with header_col2:
        st.markdown(
            "<h1 style='margin:0; padding:0; font-size:1.7rem; line-height:1.0;'>Care Transition Efficiency & Placement Outcome Analytics</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='margin:6px 0 0 0; font-size:0.95rem; color:#94a3b8;'>Interactive monitoring for care pipeline flow, transfer efficiency, backlog pressure, and outcome trends.</div>",
            unsafe_allow_html=True,
        )

    with st.sidebar:
        st.header("Controls")
        start_date = st.date_input(
            "Start date",
            value=df["Date"].min().date(),
            min_value=df["Date"].min().date(),
            max_value=df["Date"].max().date(),
        )
        end_date = st.date_input(
            "End date",
            value=df["Date"].max().date(),
            min_value=df["Date"].min().date(),
            max_value=df["Date"].max().date(),
        )
        metric_view = st.radio("Metric display", ["Absolute counts", "Ratios"], horizontal=True)
        st.divider()
        st.subheader("Threshold alerts")
        transfer_threshold = st.slider("Transfer rate alert threshold", 0.0, 1.0, 0.60, 0.01)
        discharge_threshold = st.slider("Discharge rate alert threshold", 0.0, 0.3, 0.03, 0.005)
        backlog_threshold = st.slider("Backlog change alert threshold (%)", 0.0, 50.0, 10.0, 0.5)

    filtered_df = df[(df["Date"].dt.date >= start_date) & (df["Date"].dt.date <= end_date)].copy()

    if filtered_df.empty:
        st.warning("No data is available for the selected date range.")
        return

    total_entries = int(filtered_df["Children apprehended and placed in CBP custody*"].sum())
    total_transfers = int(filtered_df["Children transferred out of CBP custody"].sum())
    total_discharges = int(filtered_df["Children discharged from HHS Care"].sum())
    avg_transfer_rate = float(filtered_df["CBP_to_HHS_Transfer_Rate"].mean())
    avg_discharge_rate = float(filtered_df["HHS_Discharge_Rate"].mean())
    avg_cbp_custody = float(filtered_df["Children in CBP custody"].mean())
    throughput_rate = total_discharges / total_entries if total_entries else 0.0
    backlog_change = float(filtered_df["Backlog_Accumulation_Rate"].mean())
    peak_backlog = int(filtered_df["Children in HHS Care"].max())
    peak_cbp_backlog = int(filtered_df["Children in CBP custody"].max())
    cbp_entry_loss = max(total_entries - total_transfers, 0)
    hhs_care_loss = max(total_transfers - total_discharges, 0)

    alerts = []
    if avg_transfer_rate < transfer_threshold:
        alerts.append(("Transfer efficiency", f"Transfer rate {avg_transfer_rate:.1%} is below the {transfer_threshold:.0%} alert threshold."))
    if avg_discharge_rate < discharge_threshold:
        alerts.append(("Discharge efficiency", f"Discharge rate {avg_discharge_rate:.1%} is below the {discharge_threshold:.0%} alert threshold."))
    if backlog_change > backlog_threshold:
        alerts.append(("Backlog pressure", f"Backlog change {backlog_change:.1f}% is above the {backlog_threshold:.1f}% alert threshold."))

    st.subheader("Operational alerts")
    if alerts:
        for title, message in alerts:
            st.warning(f"{title}: {message}")
    else:
        st.success("No alert conditions are currently triggered for the selected period.")

    st.subheader("Key performance indicators")

    primary_kpis = [
        ("Transfer Efficiency Ratio", f"{avg_transfer_rate:.1%}", "Mean CBP → HHS transfer rate from the selected window.", "#f6e58d"),
        ("Discharge Effectiveness Index", f"{avg_discharge_rate:.1%}", "Mean HHS discharge rate from the selected window.", "#90ee90"),
        ("Pipeline Throughput", f"{throughput_rate:.1%}", "Total discharges ÷ total entries for the selected window.", "#8ecae6"),
        ("Backlog Accumulation Rate", f"{backlog_change:.1f}%", "Mean backlog change rate from the selected window.", "#ffb703"),
        ("Outcome Stability Score", f"{(1 - abs(backlog_change / 100)):.1%}", "1 - |backlog rate| to reflect outcome consistency.", "#a8dadc"),
    ]

    primary_cols = st.columns(5)
    for column, (name, value, description, color) in zip(primary_cols, primary_kpis):
        with column:
            render_kpi_card(name, value, description, color)

    st.subheader("Supporting operational metrics")
    support_kpis = [
        ("Total Entries", f"{total_entries:,}", "Total apprehensions recorded in the selected window.", "#f6e58d"),
        ("Total Transfers", f"{total_transfers:,}", "Total children transferred out of CBP custody.", "#90ee90"),
        ("Total Discharges", f"{total_discharges:,}", "Total children discharged from HHS care.", "#8ecae6"),
        ("Avg CBP Custody", f"{avg_cbp_custody:,.0f}", "Average number of children in CBP custody.", "#ffb703"),
        ("Peak HHS Backlog", f"{peak_backlog:,}", "Maximum HHS care backlog recorded in the selected window.", "#a8dadc"),
        ("Peak CBP Backlog", f"{peak_cbp_backlog:,}", "Maximum CBP custody backlog recorded in the selected window.", "#cdb4db"),
        ("CBP Entry Loss", f"{cbp_entry_loss:,}", "Entries not transferred out of CBP custody.", "#8ecae6"),
        ("HHS Care Loss", f"{hhs_care_loss:,}", "Transfers not yet discharged from HHS care.", "#f6e58d"),
    ]

    support_cols = st.columns(4)
    for index, (name, value, description, color) in enumerate(support_kpis):
        with support_cols[index % 4]:
            render_kpi_card(name, value, description, color)


    st.subheader("1. Care Pipeline Flow Visualization")
    st.plotly_chart(
        build_threshold_bar(
            total_entries,
            total_transfers,
            total_discharges,
            avg_transfer_rate,
            avg_discharge_rate,
            transfer_threshold,
            discharge_threshold,
        ),
        use_container_width=True,
    )

    flow_df = pd.DataFrame(
        {
            "Stage": ["Apprehended", "Transferred to HHS", "Discharged"],
            "Count": [total_entries, total_transfers, total_discharges],
        }
    )
    funnel_fig = px.funnel(
        flow_df,
        x="Count",
        y="Stage",
        title="Care pipeline flow",
        color_discrete_sequence=["#8ecae6", "#f6e58d", "#90ee90"],
    )
    flow_series_fig = px.line(
        filtered_df,
        x="Date",
        y=["Children apprehended and placed in CBP custody*", "Children discharged from HHS Care"],
        title="Entry vs. discharge trend",
        labels={"value": "Children", "variable": "Metric"},
        color_discrete_sequence=["#8ecae6", "#90ee90"],
    )
    left, right = st.columns(2)
    left.plotly_chart(style_plot(funnel_fig), use_container_width=True)
    right.plotly_chart(style_plot(flow_series_fig), use_container_width=True)

    st.subheader("2. Transfer & Discharge Efficiency Panels")
    transfer_fig = px.line(
        filtered_df,
        x="Date",
        y="CBP_to_HHS_Transfer_Rate",
        title="CBP to HHS transfer rate",
        labels={"CBP_to_HHS_Transfer_Rate": "Transfer rate"},
    )
    transfer_fig.update_traces(line=dict(color="#f6e58d", width=3), marker=dict(color="#f6e58d"))
    transfer_fig.add_hline(y=transfer_threshold, line_dash="dot", line_color="red", annotation_text="Alert threshold")
    transfer_fig.update_traces(mode="lines+markers")

    discharge_fig = px.line(
        filtered_df,
        x="Date",
        y="HHS_Discharge_Rate",
        title="HHS discharge rate",
        labels={"HHS_Discharge_Rate": "Discharge rate"},
    )
    discharge_fig.update_traces(line=dict(color="#90ee90", width=3), marker=dict(color="#90ee90"))
    discharge_fig.add_hline(y=discharge_threshold, line_dash="dot", line_color="red", annotation_text="Alert threshold")
    discharge_fig.update_traces(mode="lines+markers")

    left2, right2 = st.columns(2)
    left2.plotly_chart(style_plot(transfer_fig), use_container_width=True)
    right2.plotly_chart(style_plot(discharge_fig), use_container_width=True)

    st.subheader("3. Bottleneck Detection Charts")
    backlog_fig = px.line(
        filtered_df,
        x="Date",
        y="Backlog_Accumulation_Rate",
        title="Backlog accumulation rate",
        labels={"Backlog_Accumulation_Rate": "Backlog change (%)"},
    )
    backlog_fig.add_hline(y=backlog_threshold, line_dash="dot", line_color="red", annotation_text="Alert threshold")
    backlog_fig.update_traces(mode="lines+markers")

    net_accumulation_fig = px.bar(
        filtered_df,
        x="Date",
        y="Daily_Net_Accumulation",
        title="Daily net accumulation",
        labels={"Daily_Net_Accumulation": "Net change in children"},
    )
    net_accumulation_fig.update_traces(marker_color="rgba(31, 119, 180, 0.7)")

    left3, right3 = st.columns(2)
    left3.plotly_chart(style_plot(backlog_fig), use_container_width=True)
    right3.plotly_chart(style_plot(net_accumulation_fig), use_container_width=True)

    st.subheader("4. Outcome Trend Analysis")
    outcome_fig = px.line(
        filtered_df,
        x="Date",
        y=["CBP_to_HHS_Transfer_Rate", "HHS_Discharge_Rate"],
        title="Transfer and discharge outcome trends",
        labels={"value": "Rate", "variable": "Metric"},
        color_discrete_sequence=["#f6e58d", "#90ee90"],
    )
    outcome_fig.update_traces(mode="lines+markers")
    st.plotly_chart(style_plot(outcome_fig), use_container_width=True)

    st.subheader("5. Forecasting & Control Charts")
    forecast_periods = st.slider("Forecast horizon (days)", 7, 90, 30, 7)
    forecast_series = filtered_df.set_index("Date")["Children in HHS Care"].astype(float)
    if len(forecast_series) >= 3:
        model = ExponentialSmoothing(forecast_series, trend="add", seasonal=None, initialization_method="estimated")
        fitted_model = model.fit(optimized=True)
        forecast_values = fitted_model.forecast(forecast_periods)

        forecast_index = pd.date_range(forecast_series.index[-1] + pd.Timedelta(days=1), periods=forecast_periods, freq="D")
        forecast_df = pd.DataFrame({"Date": forecast_index, "Forecast": forecast_values.values})
        historical_df = pd.DataFrame({"Date": forecast_series.index, "Observed": forecast_series.values})

        forecast_fig = px.line(historical_df, x="Date", y="Observed", title="Observed backlog vs. forecast")
        forecast_fig.add_scatter(x=forecast_df["Date"], y=forecast_df["Forecast"], mode="lines+markers", name="Forecast")
        st.plotly_chart(style_plot(forecast_fig), use_container_width=True)

        mean_value = float(forecast_series.mean())
        std_value = float(forecast_series.std())
        ucl = mean_value + (3 * std_value)
        lcl = max(0, mean_value - (3 * std_value))
        control_df = historical_df.copy()
        control_df["Mean"] = mean_value
        control_df["UCL"] = ucl
        control_df["LCL"] = lcl
        control_fig = px.line(control_df, x="Date", y=["Observed", "Mean", "UCL", "LCL"], title="Backlog control chart")
        st.plotly_chart(style_plot(control_fig), use_container_width=True)
    else:
        st.info("Forecasting requires at least three observations in the selected range.")

    st.subheader("Full dataset")
    st.dataframe(filtered_df.reset_index(drop=True), use_container_width=True, height=500)


def main() -> None:
    df = preprocess_data(load_data())
    build_dashboard(df)


if __name__ == "__main__":
    main()
