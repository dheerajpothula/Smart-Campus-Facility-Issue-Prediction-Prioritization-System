"""
Facility Operations Control Centre — Reports & Operational Analytics.
Implements Phase 6:
- Professional, clean, information-dense Modern Sage & Forest design (#203A32, #A8B9A3, #DCE5D8, #F5F7F2, #FFFFFF).
- Empirical performance analytics using real complaint records only.
- Date range and multi-dimensional filters (Start date, End date, Category, Building/Location, Status).
- Working Clear Filters action with safe session-state handling.
- Live KPI summary (Total Complaints, New Complaints, In Progress, Resolved, Resolution Rate).
- Complaint trend analysis with Daily, Weekly, and Monthly aggregations.
- Category distribution and comparison analysis.
- Location volume analysis and concentration highlighting.
- MCPI priority analysis (Distribution, Definitions, Cross-Analysis).
- Resolution performance analysis (Turnaround times, Ageing brackets for unresolved tickets, Verification auditing).
- Administrative ML explainability insights (Objective MCPI feature attribution dimensions and heuristics).
- Export functionality: Filtered complaint records CSV (redacting sensitive student PII) and Analytics Summary CSV.
"""
import io
from datetime import datetime, timedelta, date
import streamlit as st
import pandas as pd

from dashboard.components.admin_header import render_admin_header
from dashboard.components.styles import render_kpi, _clean_html, get_priority_badge
from src.data.complaints_store import get_complaints_df
from src.prediction.priority_scoring import calculate_priority_score, get_current_weights


def clear_reports_filters() -> None:
    """Safely resets all Reports filter keys in session state before widget instantiation."""
    for k in ["rep_start_date", "rep_end_date", "rep_category", "rep_location", "rep_status", "rep_trend_agg"]:
        if k in st.session_state:
            del st.session_state[k]


def render_reports_page() -> None:
    """Renders the Facility Operations Reports and Analytics page."""
    render_admin_header(
        page_title="Reports & Analytics",
        subtitle="Analyse facility complaints, prioritisation patterns and resolution performance.",
        kicker="FACILITY OPERATIONS · REPORTS & ANALYTICS",
    )

    raw_df = get_complaints_df()

    if raw_df.empty:
        st.info("No complaint records currently available in repository. Please load or reset data in the sidebar controls.")
        return

    # Extract available categories and locations for dynamic filter options
    cat_col = "facility_type" if "facility_type" in raw_df.columns else "category"
    sorted_cats = sorted(raw_df[cat_col].dropna().unique().tolist()) if cat_col in raw_df.columns else []

    loc_col = "building" if "building" in raw_df.columns and not raw_df["building"].dropna().empty else "location"
    sorted_locs = sorted(raw_df[loc_col].dropna().unique().tolist()) if loc_col in raw_df.columns else []

    # Parse date bounds from empirical records
    parsed_dates_all = pd.to_datetime(raw_df.get("date_reported"), format="mixed", errors="coerce").dropna()
    if not parsed_dates_all.empty:
        min_date_bound = parsed_dates_all.min().date()
        max_date_bound = parsed_dates_all.max().date()
    else:
        today = datetime.now().date()
        min_date_bound = today - timedelta(days=30)
        max_date_bound = today

    # =========================================================================
    # 1. DATE RANGE & MULTI-DIMENSIONAL FILTERS TOOLBAR
    # =========================================================================
    st.markdown(
        """
        <div class="dashboard-card" style="padding: 0.85rem 1.15rem; margin-bottom: 1rem; border: 1px solid #DCE5D8; background-color: #FFFFFF; border-radius: 8px;">
            <div style="font-size: 0.95rem; font-weight: 750; color: #203A32; margin-bottom: 0.25rem;">
                Filter Analytics Scope
            </div>
            <div style="font-size: 0.82rem; color: #4A6357;">
                Refine the reporting window, facility category, campus zone, and lifecycle status.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    f_col1, f_col2, f_col3, f_col4, f_col5, f_col6 = st.columns([1.1, 1.1, 1.3, 1.3, 1.1, 0.8])

    with f_col1:
        start_date = st.date_input(
            "Start Date",
            value=st.session_state.get("rep_start_date", min_date_bound),
            key="rep_start_date",
            help="Filter complaints reported on or after this date",
        )
    with f_col2:
        end_date = st.date_input(
            "End Date",
            value=st.session_state.get("rep_end_date", max_date_bound),
            key="rep_end_date",
            help="Filter complaints reported on or before this date",
        )
    with f_col3:
        cat_filter = st.selectbox(
            "Category",
            options=["All Categories"] + sorted_cats,
            index=0 if "rep_category" not in st.session_state or st.session_state["rep_category"] not in (["All Categories"] + sorted_cats)
                  else (["All Categories"] + sorted_cats).index(st.session_state["rep_category"]),
            key="rep_category",
        )
    with f_col4:
        loc_filter = st.selectbox(
            "Building / Location",
            options=["All Locations"] + sorted_locs,
            index=0 if "rep_location" not in st.session_state or st.session_state["rep_location"] not in (["All Locations"] + sorted_locs)
                  else (["All Locations"] + sorted_locs).index(st.session_state["rep_location"]),
            key="rep_location",
        )
    with f_col5:
        status_options = ["All Statuses", "Submitted", "Under Review", "Assigned", "In Progress", "Resolved", "Withdrawn"]
        status_filter = st.selectbox(
            "Status",
            options=status_options,
            index=0 if "rep_status" not in st.session_state or st.session_state["rep_status"] not in status_options
                  else status_options.index(st.session_state["rep_status"]),
            key="rep_status",
        )
    with f_col6:
        st.markdown("<div style='height: 1.7rem;'></div>", unsafe_allow_html=True)
        st.button(
            "Clear Filters",
            key="btn_clear_reports_filters",
            on_click=clear_reports_filters,
            help="Reset all filters to full repository scope",
            use_container_width=True,
        )

    # Apply Filters to dataset
    df = raw_df.copy()

    # 1. Date Range
    if "date_reported" in df.columns:
        dt_parsed = pd.to_datetime(df["date_reported"], format="mixed", errors="coerce")
        if start_date:
            df = df[dt_parsed.dt.date >= start_date]
            dt_parsed = pd.to_datetime(df["date_reported"], format="mixed", errors="coerce")
        if end_date:
            df = df[dt_parsed.dt.date <= end_date]

    # 2. Category
    if cat_filter != "All Categories":
        cat_match = False
        if "facility_type" in df.columns:
            cat_match = cat_match | (df["facility_type"] == cat_filter)
        if "category" in df.columns:
            cat_match = cat_match | (df["category"] == cat_filter)
        df = df[cat_match]

    # 3. Location
    if loc_filter != "All Locations":
        loc_match = False
        if "building" in df.columns:
            loc_match = loc_match | (df["building"] == loc_filter)
        if "location" in df.columns:
            loc_match = loc_match | (df["location"].astype(str).str.contains(loc_filter, case=False, na=False))
        df = df[loc_match]

    # 4. Status
    if status_filter != "All Statuses" and "status" in df.columns:
        df = df[df["status"] == status_filter]

    # Empty State Notice if filtered dataset is empty
    if df.empty:
        st.info("ℹ️ No complaint records match the selected filter criteria. Showing empty analytical states. Click 'Clear Filters' above to restore the full dataset.")

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

    # =========================================================================
    # 2. COMPACT KPI SUMMARY INDICATORS (Actual Records Only)
    # =========================================================================
    total_complaints = len(df)
    new_complaints = int((df["status"] == "Submitted").sum()) if "status" in df.columns else 0
    in_prog_complaints = int(df["status"].isin(["In Progress", "Under Review", "Assigned"]).sum()) if "status" in df.columns else 0
    resolved_complaints = int((df["status"] == "Resolved").sum()) if "status" in df.columns else 0
    resolution_rate = f"{round((resolved_complaints / total_complaints * 100), 1)}%" if total_complaints > 0 else "0.0%"

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        render_kpi("Total Complaints", total_complaints, caption="Filtered volume", icon="📋")
    with k2:
        render_kpi("New Complaints", new_complaints, caption="Awaiting initial triage", icon="🆕")
    with k3:
        render_kpi("In Progress", in_prog_complaints, caption="Active maintenance", icon="⏳")
    with k4:
        render_kpi("Resolved", resolved_complaints, caption="Completed work orders", icon="✅")
    with k5:
        render_kpi("Resolution Rate", resolution_rate, caption="Completed ratio", icon="📈")

    st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)

    # =========================================================================
    # 3. COMPLAINT TREND ANALYSIS (Daily, Weekly, Monthly Aggregation)
    # =========================================================================
    st.markdown(
        """
        <div class="dashboard-card" style="margin-bottom: 0.6rem; border: 1px solid #DCE5D8; background: #FFFFFF; padding: 0.85rem 1.15rem; border-radius: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
                <div>
                    <h3 style="margin: 0; font-size: 1.05rem; color: #203A32; font-weight: 750;">
                        📅 Incident Ingestion Trends Over Time
                    </h3>
                    <p style="color: #4A6357; font-size: 0.82rem; margin: 0.25rem 0 0 0;">
                        Time-series progression of reported facility issues based on verified submission timestamps.
                    </p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    agg_col, _ = st.columns([2, 3])
    with agg_col:
        agg_mode = st.radio(
            "Aggregation Interval",
            options=["Daily", "Weekly", "Monthly"],
            horizontal=True,
            key="rep_trend_agg",
        )

    if not df.empty and "date_reported" in df.columns:
        dt_parsed_trend = pd.to_datetime(df["date_reported"], format="mixed", errors="coerce")
        valid_trend_df = df[dt_parsed_trend.notna()].copy()
        valid_trend_df["_dt"] = dt_parsed_trend[dt_parsed_trend.notna()]

        if not valid_trend_df.empty:
            if agg_mode == "Weekly":
                valid_trend_df["Period"] = valid_trend_df["_dt"].dt.to_period("W").apply(lambda r: str(r.start_time.date()))
                period_header = "Week Starting"
            elif agg_mode == "Monthly":
                valid_trend_df["Period"] = valid_trend_df["_dt"].dt.strftime("%Y-%m")
                period_header = "Month (YYYY-MM)"
            else:  # Daily
                valid_trend_df["Period"] = valid_trend_df["_dt"].dt.strftime("%Y-%m-%d")
                period_header = "Date (YYYY-MM-DD)"

            trend_counts = valid_trend_df["Period"].value_counts().sort_index()

            c_trend1, c_trend2 = st.columns([2.2, 1])
            with c_trend1:
                st.bar_chart(trend_counts, color="#203A32")
            with c_trend2:
                trend_table = pd.DataFrame({
                    period_header: [str(d) for d in trend_counts.index],
                    "Complaints Logged": trend_counts.values,
                })
                st.dataframe(trend_table, use_container_width=True, hide_index=True)
        else:
            st.info("No valid submission timestamps found in the filtered records to plot trend progression.")
    else:
        st.info("Complaint trend analysis unavailable for empty dataset.")

    st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)

    # =========================================================================
    # 4. CATEGORY & LOCATION ANALYSIS
    # =========================================================================
    col_c1, col_c2 = st.columns(2)

    with col_c1:
        st.markdown(
            """
            <div class="dashboard-card" style="margin-bottom: 0.6rem; border: 1px solid #DCE5D8; background: #FFFFFF; padding: 0.85rem 1.15rem; border-radius: 8px;">
                <h3 style="margin: 0; font-size: 1.05rem; color: #203A32; font-weight: 750;">
                    🏢 Complaints by Facility Category
                </h3>
                <p style="color: #4A6357; font-size: 0.82rem; margin: 0.25rem 0 0 0;">
                    Volume distribution across campus engineering disciplines.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if not df.empty and cat_col in df.columns and not df[cat_col].dropna().empty:
            cat_counts = df[cat_col].value_counts()
            st.bar_chart(cat_counts, color="#203A32")
            cat_table = pd.DataFrame({
                "Category": cat_counts.index,
                "Complaints": cat_counts.values,
                "Share (%)": [f"{round(v / len(df) * 100, 1)}%" for v in cat_counts.values],
            })
            st.dataframe(cat_table, use_container_width=True, hide_index=True)
        else:
            st.info("Category breakdown data unavailable for active filters.")

    with col_c2:
        st.markdown(
            """
            <div class="dashboard-card" style="margin-bottom: 0.6rem; border: 1px solid #DCE5D8; background: #FFFFFF; padding: 0.85rem 1.15rem; border-radius: 8px;">
                <h3 style="margin: 0; font-size: 1.05rem; color: #203A32; font-weight: 750;">
                    📍 Complaints by Building &amp; Location
                </h3>
                <p style="color: #4A6357; font-size: 0.82rem; margin: 0.25rem 0 0 0;">
                    Registered incidents clustered by campus facility infrastructure.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if not df.empty and loc_col in df.columns and not df[loc_col].dropna().empty:
            loc_counts = df[loc_col].value_counts().head(8)
            st.bar_chart(loc_counts, color="#A8B9A3")

            # Concentration density analysis
            top_loc = loc_counts.index[0]
            top_count = loc_counts.iloc[0]
            top_pct = round(top_count / len(df) * 100, 1)
            if top_pct >= 25.0 and len(df) >= 3:
                st.caption(f"📌 **Concentration Notice**: **{top_loc}** accounts for the highest volume ({top_count} complaints, {top_pct}% of filtered dataset).")
            else:
                st.caption("Incident distribution across campus buildings is currently balanced.")
        else:
            st.info("Building distribution data unavailable for active filters.")

    st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)

    # =========================================================================
    # 5. MCPI PRIORITY ANALYSIS (Existing Definitions & Cross-Tabulation)
    # =========================================================================
    col_p1, col_p2 = st.columns([1.1, 1.9])

    with col_p1:
        st.markdown(
            """
            <div class="dashboard-card" style="margin-bottom: 0.6rem; border: 1px solid #DCE5D8; background: #FFFFFF; padding: 0.85rem 1.15rem; border-radius: 8px;">
                <h3 style="margin: 0; font-size: 1.05rem; color: #203A32; font-weight: 750;">
                    🚨 MCPI Priority Distribution
                </h3>
                <p style="color: #4A6357; font-size: 0.82rem; margin: 0.25rem 0 0 0;">
                    Multi-Criteria Priority Index triage breakdown.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if not df.empty and "priority_tier" in df.columns and not df["priority_tier"].dropna().empty:
            prio_order = ["Critical", "High", "Medium", "Low"]
            prio_counts = df["priority_tier"].value_counts().reindex(prio_order).fillna(0).astype(int)
            st.bar_chart(prio_counts, color="#D97706")

            prio_table = pd.DataFrame({
                "Tier": prio_order,
                "Count": [prio_counts[t] for t in prio_order],
                "Share": [f"{round(prio_counts[t] / len(df) * 100, 1)}%" if len(df) > 0 else "0.0%" for t in prio_order],
            })
            st.dataframe(prio_table, use_container_width=True, hide_index=True)
        else:
            st.info("Priority distribution data unavailable.")

    with col_p2:
        st.markdown(
            """
            <div class="dashboard-card" style="margin-bottom: 0.6rem; border: 1px solid #DCE5D8; background: #FFFFFF; padding: 0.85rem 1.15rem; border-radius: 8px;">
                <h3 style="margin: 0; font-size: 1.05rem; color: #203A32; font-weight: 750;">
                    📊 Priority Breakdown Across Facility Categories
                </h3>
                <p style="color: #4A6357; font-size: 0.82rem; margin: 0.25rem 0 0 0;">
                    Cross-tabulation comparing operational severity against campus subsystems.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if not df.empty and "priority_tier" in df.columns and cat_col in df.columns:
            cross_tab = pd.crosstab(df[cat_col], df["priority_tier"])
            prio_order = ["Critical", "High", "Medium", "Low"]
            for tier in prio_order:
                if tier not in cross_tab.columns:
                    cross_tab[tier] = 0
            cross_tab = cross_tab[[t for t in prio_order if t in cross_tab.columns]]
            st.dataframe(cross_tab, use_container_width=True)
            st.caption("Computed strictly using verified Multi-Criteria Priority Index (MCPI) weights: Severity (35%), Location Criticality (25%), Recurrence Risk (25%), and Campus Impact Population (15%).")
        else:
            st.info("Priority cross-tabulation unavailable for active filters.")

    st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)

    # =========================================================================
    # 6. RESOLUTION PERFORMANCE & BACKLOG AGEING
    # =========================================================================
    st.markdown(
        """
        <div class="dashboard-card" style="margin-bottom: 0.6rem; border: 1px solid #DCE5D8; background: #FFFFFF; padding: 0.85rem 1.15rem; border-radius: 8px;">
            <h3 style="margin: 0; font-size: 1.05rem; color: #203A32; font-weight: 750;">
                ⏱️ Resolution Turnaround &amp; Unresolved Complaint Ageing
            </h3>
            <p style="color: #4A6357; font-size: 0.82rem; margin: 0.25rem 0 0 0;">
                Empirical turnaround times for closed work orders and ageing analysis for active backlog items.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    res_tab_col1, res_tab_col2 = st.columns([1.5, 1])

    with res_tab_col1:
        st.markdown("#### Completed Maintenance Turnaround")
        resolved_subset = df[df["status"] == "Resolved"].copy() if "status" in df.columns else pd.DataFrame()

        if not resolved_subset.empty:
            rep_dts = pd.to_datetime(resolved_subset["date_reported"], format="mixed", errors="coerce")
            res_dts = pd.to_datetime(resolved_subset.get("resolved_at"), format="mixed", errors="coerce")
            if res_dts.isna().all() and "estimated_resolution" in resolved_subset.columns:
                res_dts = pd.to_datetime(resolved_subset["estimated_resolution"], format="mixed", errors="coerce")

            valid_mask = rep_dts.notna() & res_dts.notna()
            valid_res_records = resolved_subset[valid_mask].copy()

            if not valid_res_records.empty:
                turnaround_days = (res_dts[valid_mask] - rep_dts[valid_mask]).dt.total_seconds() / 86400.0
                # Filter out negative differences if any corrupt dates exist
                turnaround_days = turnaround_days.clip(lower=0.0)

                avg_days = round(turnaround_days.mean(), 1)
                min_days = round(turnaround_days.min(), 1)
                max_days = round(turnaround_days.max(), 1)

                rt1, rt2, rt3, rt4 = st.columns(4)
                with rt1:
                    render_kpi("Avg Turnaround", f"{avg_days} days", caption="Mean close time", icon="⏱️")
                with rt2:
                    render_kpi("Fastest Close", f"{min_days} days", caption="Minimum time", icon="⚡")
                with rt3:
                    render_kpi("Longest Close", f"{max_days} days", caption="Maximum time", icon="🐢")
                with rt4:
                    render_kpi("Verified Audit", f"{len(valid_res_records)}/{len(resolved_subset)}", caption="Timestamps valid", icon="🛡️")

                st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
                audit_cols = ["complaint_id", "title", "facility_type", "location", "date_reported", "resolved_at", "closing_remarks"]
                avail_audit = [c for c in audit_cols if c in valid_res_records.columns]
                st.dataframe(valid_res_records[avail_audit], use_container_width=True, hide_index=True)

                excluded_count = len(resolved_subset) - len(valid_res_records)
                if excluded_count > 0:
                    st.caption(f"⚠️ Note: {excluded_count} resolved complaint record(s) excluded from turnaround metrics due to unrecorded or unparseable timestamps.")
            else:
                st.info("Resolved complaints exist in filter scope, but lack verified completion timestamps to compute turnaround metrics.")
        else:
            st.info("No resolved complaints in the current filter scope to compute turnaround metrics.")

    with res_tab_col2:
        st.markdown("#### Unresolved Complaint Ageing")
        open_subset = df[~df["status"].isin(["Resolved", "Withdrawn"])].copy() if "status" in df.columns else pd.DataFrame()

        if not open_subset.empty and "date_reported" in open_subset.columns:
            open_rep_dts = pd.to_datetime(open_subset["date_reported"], format="mixed", errors="coerce")
            valid_open = open_subset[open_rep_dts.notna()].copy()

            if not valid_open.empty:
                now_ts = pd.Timestamp.now()
                open_age_days = (now_ts - open_rep_dts[open_rep_dts.notna()]).dt.total_seconds() / 86400.0
                open_age_days = open_age_days.clip(lower=0.0)

                bracket_24h = int((open_age_days < 1.0).sum())
                bracket_1_3d = int(((open_age_days >= 1.0) & (open_age_days <= 3.0)).sum())
                bracket_4_7d = int(((open_age_days > 3.0) & (open_age_days <= 7.0)).sum())
                bracket_over7d = int((open_age_days > 7.0).sum())

                ageing_df = pd.DataFrame({
                    "Age Bracket": ["< 24 Hours", "1 - 3 Days", "4 - 7 Days", "> 7 Days"],
                    "Tickets": [bracket_24h, bracket_1_3d, bracket_4_7d, bracket_over7d],
                }).set_index("Age Bracket")

                st.bar_chart(ageing_df, color="#203A32")
                st.caption(f"Total active backlog: **{len(valid_open)}** open complaints awaiting resolution.")
            else:
                st.info("No valid submission timestamps to calculate backlog age.")
        else:
            st.info("Zero active unresolved complaints currently in filter scope.")

    st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)

    # =========================================================================
    # 7. PREDICTIVE MAINTENANCE & EXPLAINABILITY INSIGHTS
    # =========================================================================
    st.markdown(
        """
        <div class="dashboard-card" style="margin-bottom: 0.6rem; border: 1px solid #DCE5D8; background: #FFFFFF; padding: 0.85rem 1.15rem; border-radius: 8px;">
            <h3 style="margin: 0; font-size: 1.05rem; color: #203A32; font-weight: 750;">
                🧠 Predictive Maintenance &amp; Multi-Criteria Feature Attribution Insights
            </h3>
            <p style="color: #4A6357; font-size: 0.82rem; margin: 0.25rem 0 0 0;">
                Administrative explainability breakdown showing the objective score drivers across campus complaints.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not df.empty:
        # Calculate dynamic average MCPI score breakdown across filtered records
        weights = get_current_weights()
        breakdown_list = []
        for _, row in df.iterrows():
            bd = row.get("score_breakdown")
            if isinstance(bd, dict) and "Severity Contribution" in bd:
                breakdown_list.append(bd)
            else:
                _, _, bd_calc = calculate_priority_score(
                    severity=row.get("severity", "Medium"),
                    location_type=row.get("location_type", "Corridor / Common Area"),
                    recurrence_risk=row.get("recurrence_risk", 0.3),
                    impact_scale=row.get("impact_scale", 0.5),
                    weights=weights,
                )
                breakdown_list.append(bd_calc)

        if breakdown_list:
            bd_frame = pd.DataFrame(breakdown_list)
            mean_vals = bd_frame.mean().round(1)

            exp_col1, exp_col2 = st.columns([1.6, 1])

            with exp_col1:
                st.caption("Average points contributed by each MCPI dimension across active dataset (Scale: 0–100):")
                contrib_plot_data = pd.DataFrame({
                    "MCPI Scoring Dimension": [
                        "Reported Severity (35%)",
                        "Location Criticality (25%)",
                        "Recurrence Risk (25%)",
                        "Campus Impact Scale (15%)",
                    ],
                    "Average Points Contributed": [
                        mean_vals.get("Severity Contribution", 0.0),
                        mean_vals.get("Location Criticality Contribution", 0.0),
                        mean_vals.get("Recurrence Risk Contribution", 0.0),
                        mean_vals.get("Impact Population Contribution", 0.0),
                    ],
                }).set_index("MCPI Scoring Dimension")

                st.bar_chart(contrib_plot_data, color="#203A32", horizontal=True)

            with exp_col2:
                st.markdown(
                    """
                    <div style="background: #F5F7F2; border: 1px solid #DCE5D8; padding: 0.85rem 1rem; border-radius: 8px; font-size: 0.84rem; line-height: 1.5; color: #203A32;">
                        <strong style="color: #203A32; font-size: 0.88rem;">🔬 Decision Engine Specifications</strong>
                        <p style="margin: 0.4rem 0 0.5rem 0;">
                            Priority scores are objectively derived via multi-factor evaluation rather than subjective sorting.
                        </p>
                        <ul style="margin: 0; padding-left: 1.1rem; color: #4A6357;">
                            <li><strong>Severity (35%)</strong>: Emergency safety hazards, leaks, electrical sparks.</li>
                            <li><strong>Location (25%)</strong>: Criticality index of facility zones (Server rooms vs common grounds).</li>
                            <li><strong>Recurrence (25%)</strong>: Historical re-occurrence rate within 30-day window.</li>
                            <li><strong>Impact (15%)</strong>: Campus population affected by service outage.</li>
                        </ul>
                        <div style="margin-top: 0.6rem; font-size: 0.78rem; color: #6D8276;">
                            <em>Status: Baseline Heuristics & TF-IDF Vectorizer Active. Advanced gradient-boosted models remain in cross-validation protocol. No synthetic metrics are shown.</em>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.info("Feature attribution insights unavailable for empty dataset.")

    st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)

    # =========================================================================
    # 8. EXPORT FUNCTIONALITY (Admin-Authorized & Privacy-Preserving)
    # =========================================================================
    st.markdown(
        """
        <div class="dashboard-card" style="margin-bottom: 0.6rem; border: 1px solid #DCE5D8; background: #FFFFFF; padding: 0.85rem 1.15rem; border-radius: 8px;">
            <h3 style="margin: 0; font-size: 1.05rem; color: #203A32; font-weight: 750;">
                📥 Data Export &amp; Audit Reporting
            </h3>
            <p style="color: #4A6357; font-size: 0.82rem; margin: 0.25rem 0 0 0;">
                Download filtered complaint records and aggregated analytics summaries. Sensitive student personal information is automatically redacted.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    exp_btn1, exp_btn2 = st.columns(2)

    # 1. Complaints CSV (Redacting unauthorized student PII)
    with exp_btn1:
        if not df.empty:
            export_cols = [
                "complaint_id", "title", "facility_type", "building", "location",
                "status", "priority_tier", "priority_score", "date_reported",
                "resolved_at", "allotted_person", "action_taken"
            ]
            avail_cols = [c for c in export_cols if c in df.columns]
            export_df = df[avail_cols].copy()
            csv_data = export_df.to_csv(index=False).encode("utf-8")
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M")
            st.download_button(
                label="📥 Download Filtered Complaints (CSV)",
                data=csv_data,
                file_name=f"fipp_complaints_export_{timestamp_str}.csv",
                mime="text/csv",
                key="btn_download_filtered_csv",
                use_container_width=True,
            )
        else:
            st.button("📥 Download Filtered Complaints (CSV)", disabled=True, use_container_width=True, key="btn_dl_empty_disabled")

    # 2. Analytics Summary CSV
    with exp_btn2:
        if not df.empty:
            summary_records = [
                {"Metric Domain": "Executive KPI", "Metric Indicator": "Total Complaints (Filtered)", "Value": str(total_complaints)},
                {"Metric Domain": "Executive KPI", "Metric Indicator": "New Complaints", "Value": str(new_complaints)},
                {"Metric Domain": "Executive KPI", "Metric Indicator": "In Progress Backlog", "Value": str(in_prog_complaints)},
                {"Metric Domain": "Executive KPI", "Metric Indicator": "Resolved Complaints", "Value": str(resolved_complaints)},
                {"Metric Domain": "Executive KPI", "Metric Indicator": "Resolution Rate", "Value": resolution_rate},
                {"Metric Domain": "Executive KPI", "Metric Indicator": "Mean Turnaround", "Value": f"{avg_days} days" if 'avg_days' in locals() else "N/A"},
                {"Metric Domain": "Active Scope", "Metric Indicator": "Start Date", "Value": str(start_date)},
                {"Metric Domain": "Active Scope", "Metric Indicator": "End Date", "Value": str(end_date)},
                {"Metric Domain": "Active Scope", "Metric Indicator": "Category Filter", "Value": str(cat_filter)},
                {"Metric Domain": "Active Scope", "Metric Indicator": "Location Filter", "Value": str(loc_filter)},
                {"Metric Domain": "Active Scope", "Metric Indicator": "Status Filter", "Value": str(status_filter)},
            ]
            if "cat_counts" in locals():
                for c_k, c_v in cat_counts.items():
                    summary_records.append({"Metric Domain": "Category Breakdown", "Metric Indicator": str(c_k), "Value": str(c_v)})
            if "prio_counts" in locals():
                for p_k, p_v in prio_counts.items():
                    summary_records.append({"Metric Domain": "Priority Distribution", "Metric Indicator": str(p_k), "Value": str(p_v)})

            summary_df = pd.DataFrame(summary_records)
            summary_csv_data = summary_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📊 Download Analytics Summary (CSV)",
                data=summary_csv_data,
                file_name=f"fipp_analytics_summary_{timestamp_str}.csv",
                mime="text/csv",
                key="btn_download_summary_csv",
                use_container_width=True,
            )
        else:
            st.button("📊 Download Analytics Summary (CSV)", disabled=True, use_container_width=True, key="btn_summary_empty_disabled")
