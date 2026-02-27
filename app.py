# app.py - COMPLETE PHASE 1 + PHASE 2 + PHASE 3 INTEGRATION
"""
AuditShield-Live - Shiny Dashboard
Integrates Phase 1 (Provider Scorecard, Mock Audit, Financial Impact),
Phase 2 (RADV Command Center, Chart Selection AI, Education Tracker), and
Phase 3 (Real-Time Validation, HCC Reconciliation, Compliance Forecast, Regulatory Intel, EMR Rules, Executive View).
"""
from shiny import App, render, ui, reactive
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import json

# Phase 1 Imports
from meat_validator import MEATValidator
from database import get_db_manager
from mock_audit_simulator import MockAuditSimulator
from financial_calculator import FinancialImpactCalculator

# Phase 2 Imports
from radv_command_center import RADVCommandCenter
from chart_selection_ai import ChartSelectionAI
from education_automation import EducationAutomation

# Phase 3 Imports
from realtime_validation import RealtimeValidationEngine
from hcc_reconciliation import HCCReconciliation
from compliance_forecasting import ComplianceForecaster
from regulatory_intelligence import RegulatoryIntelligence
from emr_rule_builder import EMRRuleBuilder
from dashboard_manager import DashboardManager

# Add Phase 2 & Phase 3 schema to database
from database_phase2_schema import add_phase2_schema
from database_phase3_schema import add_phase3_schema

# Initialize all components
db = get_db_manager()
add_phase2_schema(db)
add_phase3_schema(db)

validator = MEATValidator()
simulator = MockAuditSimulator()
calc = FinancialImpactCalculator()
command_center = RADVCommandCenter()
chart_selector = ChartSelectionAI()
educator = EducationAutomation()

# Phase 3 components
realtime_engine = RealtimeValidationEngine()
reconciler = HCCReconciliation()
forecaster = ComplianceForecaster()
reg_intel = RegulatoryIntelligence()
emr_builder = EMRRuleBuilder()
dashboard_mgr = DashboardManager()

# ==================== UI DEFINITION ====================

app_ui = ui.page_fluid(
    ui.tags.head(
        ui.tags.style("""
            .risk-green { background-color: #d4edda; border-left: 4px solid #28a745; }
            .risk-yellow { background-color: #fff3cd; border-left: 4px solid #ffc107; }
            .risk-red { background-color: #f8d7da; border-left: 4px solid #dc3545; }
            .metric-card { padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); background: white; }
            .provider-detail { margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 8px; }
            .audit-warning { background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 10px 0; border-radius: 4px; }
            .audit-critical { background: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin: 10px 0; border-radius: 4px; }
            .audit-on-track { background: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 10px 0; border-radius: 4px; }
            .roi-positive { color: #28a745; font-weight: bold; }
            .roi-negative { color: #dc3545; font-weight: bold; }
            .countdown-timer { font-size: 2.5em; font-weight: bold; color: #dc3545; }
            .task-overdue { background: #f8d7da; padding: 8px; margin: 4px 0; border-radius: 4px; }
            .task-upcoming { background: #fff3cd; padding: 8px; margin: 4px 0; border-radius: 4px; }
            .chart-recommended { background: #d4edda; border-left: 3px solid #28a745; }
            .chart-backup { background: #fff3cd; border-left: 3px solid #ffc107; }
            .chart-reject { background: #f8d7da; border-left: 3px solid #dc3545; }
        """)
    ),

    ui.page_navbar(
        # ==================== PHASE 1 TABS ====================

        # Tab 1: Provider Scorecard
        ui.nav_panel(
            "Provider Scorecard",
            ui.layout_sidebar(
                ui.sidebar(
                    ui.h4("Filters"),
                    ui.input_select(
                        "lookback_period",
                        "Lookback Period",
                        choices={"3": "3 months", "6": "6 months", "12": "12 months", "24": "24 months"},
                        selected="12"
                    ),
                    ui.input_checkbox_group(
                        "specialty_filter",
                        "Specialty",
                        choices=["Primary Care", "Cardiology", "Endocrinology", "Nephrology", "Pulmonology"],
                        selected=[]
                    ),
                    ui.input_checkbox_group(
                        "risk_tier_filter",
                        "Risk Tier",
                        choices=["GREEN", "YELLOW", "RED"],
                        selected=["YELLOW", "RED"]
                    ),
                    ui.input_slider("min_hccs", "Minimum HCCs", min=0, max=500, value=20, step=10),
                    ui.input_action_button("refresh_data", "Refresh Data", class_="btn-primary mt-3 w-100"),
                    width=300
                ),
                ui.div(
                    ui.h2("Provider M.E.A.T. Compliance Dashboard"),
                    ui.p("Real-time RADV audit defensibility scoring", class_="text-muted"),
                    ui.row(
                        ui.column(3, ui.output_ui("metric_total_providers")),
                        ui.column(3, ui.output_ui("metric_avg_validation")),
                        ui.column(3, ui.output_ui("metric_financial_risk")),
                        ui.column(3, ui.output_ui("metric_compliant_pct"))
                    ),
                    ui.hr(),
                    ui.card(ui.card_header("Provider Risk Distribution"), ui.output_plot("risk_scatter_plot")),
                    ui.hr(),
                    ui.card(
                        ui.card_header(
                            ui.row(
                                ui.column(6, ui.h5("Provider Details")),
                                ui.column(6, ui.download_button("download_scorecard", "Export", class_="btn-sm float-end"))
                            )
                        ),
                        ui.output_data_frame("provider_table")
                    ),
                    ui.hr(),
                    ui.card(
                        ui.card_header("Provider Detail Analysis"),
                        ui.input_select("selected_provider", "Select Provider", choices={}),
                        ui.output_ui("provider_detail_section")
                    )
                )
            )
        ),

        # Tab 2: Mock Audit
        ui.nav_panel(
            "Mock Audit",
            ui.layout_sidebar(
                ui.sidebar(
                    ui.h4("Audit Parameters"),
                    ui.input_select("contract_size", "Contract Size",
                        choices={"small_contract": "Small (<10K)", "medium_contract": "Medium (10K-50K)", "large_contract": "Large (>50K)"},
                        selected="medium_contract"
                    ),
                    ui.input_numeric("audit_year", "Audit Year", value=2026, min=2024, max=2030),
                    ui.input_action_button("run_mock_audit", "Run Mock Audit", class_="btn-danger mt-3 w-100"),
                    width=300
                ),
                ui.div(
                    ui.h2("Mock RADV Audit Simulator"),
                    ui.p("Predict CMS audit outcomes", class_="text-muted"),
                    ui.output_ui("mock_audit_results")
                )
            )
        ),

        # Tab 3: Financial Impact
        ui.nav_panel(
            "Financial Impact",
            ui.div(
                ui.h2("Financial Impact Analysis"),
                ui.p("Real-time exposure and ROI", class_="text-muted"),
                ui.row(
                    ui.column(4, ui.output_ui("financial_current_exposure")),
                    ui.column(4, ui.output_ui("financial_annualized")),
                    ui.column(4, ui.output_ui("financial_validation_rate"))
                ),
                ui.hr(),
                ui.card(
                    ui.card_header("Remediation ROI Calculator"),
                    ui.row(
                        ui.column(6, ui.input_slider("target_validation_rate", "Target Rate", min=80, max=100, value=95, step=1, post="%")),
                        ui.column(6, ui.input_action_button("calculate_roi", "Calculate ROI", class_="btn-success mt-4"))
                    ),
                    ui.output_ui("roi_results")
                ),
                ui.hr(),
                ui.card(ui.card_header("Scenario Comparison"), ui.output_plot("scenario_chart"))
            )
        ),

        # ==================== PHASE 2 TABS ====================

        # Tab 4: RADV Command Center
        ui.nav_panel(
            "RADV Command Center",
            ui.layout_sidebar(
                ui.sidebar(
                    ui.h4("Active Audits"),
                    ui.output_ui("audit_selector"),
                    ui.hr(),
                    ui.h5("Create New Audit"),
                    ui.input_text("new_audit_notice_id", "Audit Notice ID", placeholder="RADV-2026-H1234-001"),
                    ui.input_text("new_contract_id", "Contract ID", placeholder="H1234"),
                    ui.input_date("notification_date", "Notification Date", value=datetime.now().strftime('%Y-%m-%d')),
                    ui.input_numeric("sample_size_input", "Sample Size", value=100, min=35, max=200),
                    ui.input_action_button("create_audit", "Create Audit", class_="btn-success w-100 mt-3"),
                    width=300
                ),
                ui.div(
                    ui.h2("RADV Audit Management"),
                    ui.p("25-week deadline tracking and record coordination", class_="text-muted"),
                    ui.output_ui("audit_status_display")
                )
            )
        ),

        # Tab 5: Chart Selection
        ui.nav_panel(
            "Chart Selection AI",
            ui.div(
                ui.h2("Best Chart Selection"),
                ui.p("AI-powered medical record ranking for RADV submission", class_="text-muted"),
                ui.layout_sidebar(
                    ui.sidebar(
                        ui.h4("Selection Parameters"),
                        ui.output_ui("audit_selector_charts"),
                        ui.input_select("enrollee_selector", "Select Enrollee", choices={}),
                        ui.input_action_button("score_charts", "Score Charts", class_="btn-primary w-100 mt-3"),
                        ui.hr(),
                        ui.input_action_button("get_all_recommendations", "Get All Recommendations", class_="btn-success w-100"),
                        width=300
                    ),
                    ui.div(
                        ui.output_ui("chart_selection_results")
                    )
                )
            )
        ),

        # Tab 6: Education Tracker
        ui.nav_panel(
            "Education Tracker",
            ui.div(
                ui.h2("Provider Education & TPE"),
                ui.p("Targeted Probe & Educate automation", class_="text-muted"),
                ui.row(
                    ui.column(3, ui.output_ui("education_total_sessions")),
                    ui.column(3, ui.output_ui("education_upcoming")),
                    ui.column(3, ui.output_ui("education_avg_improvement")),
                    ui.column(3, ui.output_ui("education_completed"))
                ),
                ui.hr(),
                ui.card(
                    ui.card_header(
                        ui.row(
                            ui.column(6, ui.h5("Providers Needing Education")),
                            ui.column(6, ui.input_action_button("identify_tpe_providers", "Identify Providers", class_="btn-primary btn-sm float-end"))
                        )
                    ),
                    ui.output_data_frame("tpe_providers_table")
                ),
                ui.hr(),
                ui.card(
                    ui.card_header("Schedule Education Session"),
                    ui.row(
                        ui.column(4, ui.input_select("edu_provider_select", "Provider", choices={})),
                        ui.column(4, ui.input_date("edu_session_date", "Session Date", value=(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'))),
                        ui.column(4, ui.input_action_button("schedule_session", "Schedule", class_="btn-success mt-4"))
                    ),
                    ui.output_ui("session_scheduled_msg")
                ),
                ui.hr(),
                ui.card(
                    ui.card_header("Education Effectiveness"),
                    ui.output_plot("education_effectiveness_chart")
                )
            )
        ),

        # ==================== PHASE 3 TABS ====================

        # Tab 7: Real-Time Validation
        ui.nav_panel(
            "Real-Time Validation",
            ui.div(
                ui.h2("Live M.E.A.T. Validation Dashboard"),
                ui.p("Real-time encounter validation and provider feedback", class_="text-muted"),
                ui.row(
                    ui.column(3, ui.output_ui("realtime_total_validated")),
                    ui.column(3, ui.output_ui("realtime_processing_rate")),
                    ui.column(3, ui.output_ui("realtime_active_alerts")),
                    ui.column(3, ui.output_ui("realtime_queue_depth"))
                ),
                ui.hr(),
                ui.card(
                    ui.card_header("Provider Live Feedback"),
                    ui.input_select("realtime_provider_select", "Select Provider", choices={}),
                    ui.output_ui("provider_live_feedback_display")
                ),
                ui.hr(),
                ui.card(
                    ui.card_header("Active Validation Alerts"),
                    ui.output_data_frame("validation_alerts_table")
                )
            )
        ),

        # Tab 8: HCC Reconciliation
        ui.nav_panel(
            "HCC Reconciliation",
            ui.div(
                ui.h2("Two-Way HCC Reconciliation"),
                ui.p("Identify missing HCCs (ADD) and unsupported HCCs (DELETE)", class_="text-muted"),
                ui.row(
                    ui.column(3, ui.output_ui("recon_add_opportunities")),
                    ui.column(3, ui.output_ui("recon_delete_requirements")),
                    ui.column(3, ui.output_ui("recon_net_impact")),
                    ui.column(3, ui.output_ui("recon_action_rate"))
                ),
                ui.hr(),
                ui.card(
                    ui.card_header("Run Comprehensive Reconciliation"),
                    ui.row(
                        ui.column(6, ui.input_slider("recon_lookback", "Lookback Months", min=3, max=24, value=12)),
                        ui.column(6, ui.input_action_button("run_reconciliation", "Run Reconciliation", class_="btn-primary mt-4"))
                    ),
                    ui.output_ui("reconciliation_results")
                ),
                ui.hr(),
                ui.row(
                    ui.column(6, ui.card(ui.card_header("ADD Opportunities"), ui.output_data_frame("recon_add_table"))),
                    ui.column(6, ui.card(ui.card_header("DELETE Requirements"), ui.output_data_frame("recon_delete_table")))
                )
            )
        ),

        # Tab 9: Compliance Forecast
        ui.nav_panel(
            "Compliance Forecast",
            ui.div(
                ui.h2("Predictive Compliance Analytics"),
                ui.p("12-month validation rate and error rate forecasts", class_="text-muted"),
                ui.card(
                    ui.card_header("Generate Forecast"),
                    ui.row(
                        ui.column(4, ui.input_numeric("forecast_periods", "Forecast Months", value=12, min=3, max=24)),
                        ui.column(4, ui.input_slider("forecast_confidence", "Confidence Level", min=0.90, max=0.99, value=0.95, step=0.01)),
                        ui.column(4, ui.input_action_button("generate_forecast", "Generate Forecast", class_="btn-success mt-4"))
                    ),
                    ui.output_ui("forecast_summary")
                ),
                ui.hr(),
                ui.card(
                    ui.card_header("Validation Rate Forecast"),
                    ui.output_plot("forecast_chart")
                ),
                ui.hr(),
                ui.card(
                    ui.card_header("Key Trend Drivers"),
                    ui.output_ui("forecast_drivers")
                )
            )
        ),

        # Tab 10: Regulatory Intelligence
        ui.nav_panel(
            "Regulatory Intel",
            ui.div(
                ui.h2("Regulatory Intelligence Center"),
                ui.p("AI-powered monitoring of CMS, AAPC, and regulatory sources", class_="text-muted"),
                ui.row(
                    ui.column(3, ui.output_ui("reg_total_updates")),
                    ui.column(3, ui.output_ui("reg_high_priority")),
                    ui.column(3, ui.output_ui("reg_unprocessed")),
                    ui.column(3, ui.input_action_button("scan_regulatory", "Scan Sources", class_="btn-primary mt-3"))
                ),
                ui.hr(),
                ui.card(
                    ui.card_header("Recent Regulatory Updates"),
                    ui.output_ui("regulatory_updates_list")
                )
            )
        ),

        # Tab 11: EMR Rules
        ui.nav_panel(
            "EMR Rules",
            ui.div(
                ui.h2("EMR Hard Stop Rule Builder"),
                ui.p("No-code validation rules for EMR integration", class_="text-muted"),
                ui.card(
                    ui.card_header("Standard Rules"),
                    ui.p("Deploy best-practice validation rules across your EMR", class_="text-muted"),
                    ui.input_action_button("create_standard_rules", "Create Standard Rules", class_="btn-success"),
                    ui.output_ui("rules_created_msg")
                ),
                ui.hr(),
                ui.card(
                    ui.card_header("Rule Effectiveness Report"),
                    ui.output_data_frame("rule_effectiveness_table")
                ),
                ui.hr(),
                ui.card(
                    ui.card_header("Test Rule Evaluation"),
                    ui.row(
                        ui.column(4, ui.input_select("test_hcc_code", "HCC Code", choices={"HCC 226": "HCC 226", "HCC 280": "HCC 280", "HCC 36": "HCC 36"})),
                        ui.column(8, ui.input_checkbox_group("test_meat_elements", "M.E.A.T. Elements Present", choices={"monitor": "Monitor", "evaluate": "Evaluate", "assess": "Assess", "treat": "Treat"}))
                    ),
                    ui.input_action_button("test_rules", "Test Rules", class_="btn-primary mt-3"),
                    ui.output_ui("rule_test_results")
                )
            )
        ),

        # Tab 12: Executive Dashboard
        ui.nav_panel(
            "Executive View",
            ui.div(
                ui.h2("Executive Dashboard"),
                ui.p("High-level strategic metrics", class_="text-muted"),
                ui.row(
                    ui.column(4, ui.output_ui("exec_financial_exposure")),
                    ui.column(4, ui.output_ui("exec_validation_rate")),
                    ui.column(4, ui.output_ui("exec_active_audits"))
                ),
                ui.hr(),
                ui.row(
                    ui.column(6, ui.card(ui.card_header("Provider Risk Distribution"), ui.output_plot("exec_risk_chart"))),
                    ui.column(6, ui.card(ui.card_header("Compliance Forecast"), ui.output_plot("exec_forecast_chart")))
                ),
                ui.hr(),
                ui.card(
                    ui.card_header("Strategic Action Items"),
                    ui.output_ui("exec_action_items")
                )
            )
        ),

        title="AuditShield-Live - Phase 1+2+3",
        id="main_nav"
    )
)

# ==================== SERVER LOGIC ====================

def server(input, output, session):

    # Reactive values
    provider_scores_data = reactive.Value(pd.DataFrame())
    mock_audit_results = reactive.Value({})
    roi_results = reactive.Value({})
    active_audits = reactive.Value([])
    selected_audit_id = reactive.Value(None)
    tpe_providers = reactive.Value(pd.DataFrame())
    chart_scores = reactive.Value(pd.DataFrame())
    education_dashboard = reactive.Value({})

    # Phase 3 reactive values
    reconciliation_data = reactive.Value({})
    forecast_data = reactive.Value({})
    regulatory_updates = reactive.Value([])
    rules_created = reactive.Value([])
    rule_test_violations = reactive.Value(None)

    # ==================== PHASE 1 LOGIC ====================

    @reactive.Effect
    def _():
        load_provider_data()

    @reactive.Effect
    @reactive.event(input.refresh_data)
    def load_provider_data():
        lookback_months = int(input.lookback_period())
        specialty_filter = list(input.specialty_filter())
        risk_tier_filter = list(input.risk_tier_filter())
        min_hccs = input.min_hccs()

        scores = db.get_provider_scores(
            lookback_months=lookback_months,
            specialties=specialty_filter if specialty_filter else None,
            risk_tiers=risk_tier_filter if risk_tier_filter else None,
            min_hccs=min_hccs
        )

        provider_scores_data.set(scores)

        if not scores.empty:
            provider_names = scores['provider_name'].tolist()
            provider_ids = scores['provider_id'].tolist()
            ui.update_select("selected_provider", choices={name: name for name in provider_names})
            ui.update_select("edu_provider_select", choices={name: name for name in provider_names})
            ui.update_select("realtime_provider_select", choices={pid: f"{name} ({pid})" for pid, name in zip(provider_ids, provider_names)})

    @output
    @render.ui
    def metric_total_providers():
        df = provider_scores_data.get()
        if df.empty:
            return ui.div()
        total = len(df)
        at_risk = len(df[df['risk_tier'] == 'RED'])
        return ui.div(ui.h3(str(total)), ui.p("Total Providers"), ui.p(f"{at_risk} at high risk", class_="text-danger small"), class_="metric-card")

    @output
    @render.ui
    def metric_avg_validation():
        df = provider_scores_data.get()
        if df.empty:
            return ui.div()
        avg_val = df['validation_rate'].mean()
        delta = avg_val - 95
        delta_class = "text-success" if delta >= 0 else "text-danger"
        return ui.div(ui.h3(f"{avg_val:.1f}%"), ui.p("Avg Validation Rate"), ui.p(f"{delta:+.1f}% vs target", class_=f"{delta_class} small"), class_="metric-card")

    @output
    @render.ui
    def metric_financial_risk():
        df = provider_scores_data.get()
        if df.empty:
            return ui.div()
        total_risk = df['financial_risk_estimate'].fillna(0).sum()
        risk_class = "metric-card risk-red" if total_risk > 100000 else "metric-card"
        return ui.div(ui.h3(f"${total_risk:,.0f}"), ui.p("Financial Exposure"), ui.p("Potential penalties", class_="text-muted small"), class_=risk_class)

    @output
    @render.ui
    def metric_compliant_pct():
        df = provider_scores_data.get()
        if df.empty:
            return ui.div()
        green_pct = len(df[df['risk_tier'] == 'GREEN']) / len(df) * 100 if len(df) > 0 else 0
        delta = green_pct - 70
        delta_class = "text-success" if delta >= 0 else "text-warning"
        return ui.div(ui.h3(f"{green_pct:.0f}%"), ui.p("Compliant Providers"), ui.p(f"{delta:+.0f}% vs benchmark", class_=f"{delta_class} small"), class_="metric-card")

    @output
    @render.plot
    def risk_scatter_plot():
        df = provider_scores_data.get()
        if df.empty:
            return go.Figure()
        color_map = {'GREEN': '#28a745', 'YELLOW': '#ffc107', 'RED': '#dc3545'}
        fig = px.scatter(df, x='total_hccs_submitted', y='validation_rate', color='risk_tier', size='financial_risk_estimate',
                        hover_data=['provider_name', 'specialty', 'top_failure_reason'], color_discrete_map=color_map)
        fig.add_hline(y=90, line_dash="dash", line_color="green", annotation_text="Green (90%)")
        fig.add_hline(y=80, line_dash="dash", line_color="orange", annotation_text="Yellow (80%)")
        fig.update_layout(height=500, hovermode='closest')
        return fig

    @output
    @render.data_frame
    def provider_table():
        df = provider_scores_data.get()
        if df.empty:
            return pd.DataFrame()
        display_df = df[['provider_name', 'specialty', 'total_hccs_submitted', 'validation_rate', 'risk_tier', 'top_failure_reason', 'financial_risk_estimate']].copy()
        display_df.columns = ['Provider', 'Specialty', 'HCCs', 'Validation %', 'Risk', 'Top Failure', 'Financial Risk ($)']
        tier_order = {'RED': 0, 'YELLOW': 1, 'GREEN': 2}
        display_df['_sort'] = display_df['Risk'].map(tier_order)
        display_df = display_df.sort_values(['_sort', 'Validation %']).drop('_sort', axis=1)
        return render.DataGrid(display_df, selection_mode="row", width="100%")

    @output
    @render.ui
    def provider_detail_section():
        selected = input.selected_provider()
        if not selected:
            return ui.div(ui.p("Select a provider"))
        df = provider_scores_data.get()
        if df.empty:
            return ui.div()
        matches = df[df['provider_name'] == selected]
        if matches.empty:
            return ui.div()
        provider_data = matches.iloc[0]
        risk_class = f"risk-{provider_data['risk_tier'].lower()}"
        return ui.div(
            ui.row(
                ui.column(6, ui.h4(selected)),
                ui.column(6, ui.div(ui.h5(f"Risk: {provider_data['risk_tier']}"), ui.h6(f"Validation: {provider_data['validation_rate']:.1f}%"), class_=f"text-end {risk_class} p-3 rounded"))
            ),
            ui.hr(),
            ui.row(
                ui.column(6, ui.h5("Failure Patterns"), ui.output_plot("failure_pattern_chart")),
                ui.column(6, ui.h5("M.E.A.T. Compliance"), ui.output_plot("meat_element_chart"))
            ),
            class_="provider-detail"
        )

    @output
    @render.plot
    def failure_pattern_chart():
        selected = input.selected_provider()
        if not selected:
            return go.Figure()
        df = provider_scores_data.get()
        if df.empty:
            return go.Figure()
        matches = df[df['provider_name'] == selected]
        if matches.empty:
            return go.Figure()
        provider_id = matches.iloc[0]['provider_id']
        failure_data = db.get_provider_failure_patterns(provider_id, int(input.lookback_period()))
        if failure_data.empty:
            return go.Figure().add_annotation(text="No failures", showarrow=False)
        fig = px.bar(failure_data.head(10), x='occurrence_count', y='failure_category', orientation='h')
        fig.update_layout(height=400, showlegend=False)
        return fig

    @output
    @render.plot
    def meat_element_chart():
        selected = input.selected_provider()
        if not selected:
            return go.Figure()
        df = provider_scores_data.get()
        if df.empty:
            return go.Figure()
        matches = df[df['provider_name'] == selected]
        if matches.empty:
            return go.Figure()
        provider_id = matches.iloc[0]['provider_id']
        meat_data = db.get_meat_element_breakdown(provider_id, int(input.lookback_period()))
        fig = px.bar(meat_data, x='element', y='compliance_rate', color='compliance_rate', color_continuous_scale='RdYlGn', range_color=[0, 100])
        fig.update_layout(height=400, showlegend=False)
        return fig

    @output
    @render.download(filename=lambda: f"scorecard_{datetime.now().strftime('%Y%m%d')}.xlsx")
    def download_scorecard():
        import io
        df = provider_scores_data.get()
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Scorecard', index=False)
        buffer.seek(0)
        return buffer.getvalue()

    # Mock Audit
    @reactive.Effect
    @reactive.event(input.run_mock_audit)
    def run_audit_simulation():
        results = simulator.run_mock_audit(contract_size=input.contract_size(), year=input.audit_year())
        mock_audit_results.set(results)

    @output
    @render.ui
    def mock_audit_results():
        results = mock_audit_results.get()
        if not results:
            return ui.div(ui.p("Click 'Run Mock Audit'", class_="text-muted"), class_="text-center p-5")
        summary = results.get('audit_summary', {})
        financial = results.get('financial_impact', {})
        if summary.get('error'):
            return ui.div(ui.p(summary['error'], class_="text-warning"), class_="p-4")
        severity_class = {'CRITICAL': 'audit-critical', 'HIGH': 'audit-warning', 'LOW': ''}.get(financial.get('severity', ''), '')
        return ui.div(
            ui.row(
                ui.column(3, ui.div(ui.h3(str(summary.get('sample_size', 0))), ui.p("Enrollees Sampled"), class_="metric-card")),
                ui.column(3, ui.div(ui.h3(str(summary.get('predicted_failures', 0))), ui.p("Predicted Failures"), class_="metric-card")),
                ui.column(3, ui.div(ui.h3(f"{summary.get('error_rate', 0)}%"), ui.p("Error Rate"), class_="metric-card")),
                ui.column(3, ui.div(ui.h3(f"${summary.get('estimated_penalty', 0):,.0f}"), ui.p("Estimated Penalty"), class_="metric-card risk-red" if financial.get('severity') == 'CRITICAL' else "metric-card"))
            ),
            ui.hr(),
            ui.div(ui.h4(f"Status: {financial.get('severity', '')} RISK"), ui.p(f"Error rate {financial.get('error_rate', 0)}% triggers {financial.get('penalty_multiplier', 1)}x penalty"), class_=severity_class) if severity_class else ui.div(),
            ui.card(ui.card_header("Recommendations"), ui.tags.ul(*[ui.tags.li(rec) for rec in summary.get('recommendations', [])])),
            ui.card(ui.card_header("Top Failure Categories"), ui.output_plot("audit_failure_categories"))
        )

    @output
    @render.plot
    def audit_failure_categories():
        results = mock_audit_results.get()
        if not results or not results.get('audit_summary', {}).get('top_failure_categories'):
            return go.Figure()
        categories = results['audit_summary']['top_failure_categories']
        df = pd.DataFrame(list(categories.items()), columns=['Category', 'RAF Weight'])
        fig = px.bar(df, x='RAF Weight', y='Category', orientation='h', title="High-Risk HCC Categories")
        fig.update_layout(height=400)
        return fig

    # Financial Impact
    @output
    @render.ui
    def financial_current_exposure():
        exposure = calc.calculate_current_exposure(lookback_months=int(input.lookback_period()))
        return ui.div(ui.h3(f"${exposure['current_exposure']:,.0f}"), ui.p("Current Exposure"), ui.p(f"{exposure['total_failed_hccs']} failed HCCs", class_="text-muted small"), class_="metric-card")

    @output
    @render.ui
    def financial_annualized():
        exposure = calc.calculate_current_exposure(lookback_months=int(input.lookback_period()))
        return ui.div(ui.h3(f"${exposure['annualized_exposure']:,.0f}"), ui.p("Annualized Risk"), ui.p(f"{exposure['providers_affected']} providers", class_="text-muted small"), class_="metric-card")

    @output
    @render.ui
    def financial_validation_rate():
        exposure = calc.calculate_current_exposure(lookback_months=int(input.lookback_period()))
        return ui.div(ui.h3(f"{exposure['current_validation_rate']:.1f}%"), ui.p("Current Validation Rate"), ui.p("Organization-wide", class_="text-muted small"), class_="metric-card")

    @reactive.Effect
    @reactive.event(input.calculate_roi)
    def calculate_remediation_roi():
        target_rate = input.target_validation_rate()
        roi = calc.calculate_remediation_roi(target_validation_rate=target_rate)
        roi_results.set(roi)

    @output
    @render.ui
    def roi_results():
        roi = roi_results.get()
        if not roi:
            return ui.div(ui.p("Click 'Calculate ROI'", class_="text-muted text-center p-4"))
        roi_class = "roi-positive" if roi.get('net_roi', 0) > 0 else "roi-negative"
        return ui.div(
            ui.row(
                ui.column(4, ui.div(ui.h4(f"${roi.get('total_investment', 0):,.0f}"), ui.p("Investment"), ui.p(f"Training: ${roi.get('training_cost', 0):,.0f}", class_="small"), class_="metric-card")),
                ui.column(4, ui.div(ui.h4(f"${roi.get('total_savings', 0):,.0f}"), ui.p("Expected Savings"), ui.p(f"{roi.get('providers_remediated', 0)} providers", class_="small"), class_="metric-card")),
                ui.column(4, ui.div(ui.h4(f"${roi.get('net_roi', 0):,.0f}", class_=roi_class), ui.p("Net ROI"), ui.p(f"{roi.get('roi_percentage', 0)}% return", class_="small"), class_="metric-card"))
            )
        )

    @output
    @render.plot
    def scenario_chart():
        exposure = calc.calculate_current_exposure(lookback_months=int(input.lookback_period()))
        scenarios = [
            {'name': 'Status Quo', 'validation_rate': exposure['current_validation_rate'], 'remediation_investment': 0},
            {'name': 'Target 85%', 'validation_rate': 85.0, 'remediation_investment': 25000},
            {'name': 'Target 90%', 'validation_rate': 90.0, 'remediation_investment': 50000},
            {'name': 'Target 95%', 'validation_rate': 95.0, 'remediation_investment': 100000},
        ]
        results = calc.scenario_analysis(scenarios)
        fig = make_subplots(rows=1, cols=2, subplot_titles=('Risk Reduction', 'ROI %'))
        fig.add_trace(go.Bar(x=results['scenario'], y=results['risk_reduction'], name='Risk Reduction'), row=1, col=1)
        fig.add_trace(go.Bar(x=results['scenario'], y=results['roi_percentage'], name='ROI %'), row=1, col=2)
        fig.update_layout(height=400, showlegend=False)
        return fig

    # ==================== PHASE 2 LOGIC ====================

    # RADV Command Center
    @reactive.Effect
    def load_active_audits():
        audits = db.execute_query("SELECT audit_id, audit_notice_id, contract_name FROM radv_audits WHERE audit_status = 'ACTIVE' ORDER BY notification_date DESC", (), fetch="all")
        active_audits.set(audits if audits else [])

    @output
    @render.ui
    def audit_selector():
        audits = active_audits.get()
        if not audits:
            return ui.input_select("selected_audit", "Select Audit", choices={"": "No active audits"})
        choices = {str(a['audit_id']): f"{a['audit_notice_id']} - {a['contract_name']}" for a in audits}
        return ui.input_select("selected_audit", "Select Audit", choices=choices)

    @output
    @render.ui
    def audit_selector_charts():
        audits = active_audits.get()
        if not audits:
            return ui.input_select("selected_audit_charts", "Select Audit", choices={"": "No active audits"})
        choices = {str(a['audit_id']): f"{a['audit_notice_id']}" for a in audits}
        return ui.input_select("selected_audit_charts", "Select Audit", choices=choices)

    @reactive.Effect
    @reactive.event(input.create_audit)
    def create_new_audit():
        if not input.new_audit_notice_id() or not input.new_contract_id():
            return
        sample_size = max(35, min(200, int(input.sample_size_input() or 100)))
        sample_enrollees = []
        for i in range(sample_size):
            sample_enrollees.append({
                'enrollee_id': f'ENR{i+1:04d}',
                'enrollee_name': f'Patient {i+1}',
                'date_of_birth': f'19{50+i%40}-{(i%12)+1:02d}-15',
                'hccs_to_validate': ['HCC 36', 'HCC 226', 'HCC 280'][:((i % 3) + 1)],
                'total_raf_weight': round(0.5 + (i % 10) * 0.2, 3)
            })
        notif_date = input.notification_date()
        notif_str = notif_date.strftime('%Y-%m-%d') if hasattr(notif_date, 'strftime') else str(notif_date)
        audit_id = command_center.create_audit_from_notice(
            audit_notice_id=input.new_audit_notice_id(),
            contract_id=input.new_contract_id(),
            contract_name=f"Contract {input.new_contract_id()}",
            audit_year=2025,
            notification_date=notif_str,
            sample_enrollees=sample_enrollees
        )
        selected_audit_id.set(audit_id)
        load_active_audits()

    @output
    @render.ui
    def audit_status_display():
        audits = active_audits.get()
        if not audits:
            return ui.div(ui.p("Create an audit or select one", class_="text-muted text-center p-5"))
        sel = input.selected_audit()
        if not sel:
            return ui.div(ui.p("Select an audit", class_="text-muted text-center p-5"))
        audit_id = int(sel)
        status = command_center.get_audit_status(audit_id)
        if not status:
            return ui.div(ui.p("Audit not found"))
        status_class = {'ON_TRACK': 'audit-on-track', 'AT_RISK': 'audit-warning', 'CRITICAL': 'audit-critical'}.get(status['status_indicator'], '')
        return ui.div(
            ui.div(
                ui.row(
                    ui.column(6, ui.h3(f"{status['audit_notice_id']}"), ui.p(f"{status['contract_name']} - {status['audit_year']}", class_="text-muted")),
                    ui.column(6, ui.div(ui.div(f"{status['days_remaining']}", class_="countdown-timer"), ui.p("Days Remaining", class_="text-center"), ui.p(f"Due: {status['due_date']}", class_="text-center text-muted"), class_="text-center"))
                ),
                class_=f"{status_class} p-3 mb-3 rounded"
            ),
            ui.div(ui.h4(f"Status: {status['status_indicator'].replace('_', ' ')}"), ui.p(f"Sample Size: {status['sample_size']} enrollees"), class_=f"{status_class} p-3 mb-3"),
            ui.row(
                ui.column(4, ui.div(ui.h3(f"{status['submission_progress']['pct_complete']:.0f}%"), ui.p("Submission Progress"), ui.p(f"{status['submission_progress']['submitted']}/{status['submission_progress']['total']} submitted", class_="small"), class_="metric-card")),
                ui.column(4, ui.div(ui.h3(str(status['submission_progress']['records_received'])), ui.p("Records Received"), ui.p(f"Awaiting {status['sample_size'] - status['submission_progress']['records_received']}", class_="small"), class_="metric-card")),
                ui.column(4, ui.div(ui.h3(str(len(status['overdue_tasks']))), ui.p("Overdue Tasks"), ui.p("Requires attention", class_="small text-danger") if status['overdue_tasks'] else ui.p("None", class_="small text-success"), class_="metric-card"))
            ),
            ui.hr(),
            ui.card(
                ui.card_header("Overdue Tasks") if status['overdue_tasks'] else ui.card_header("No Overdue Tasks"),
                ui.div(*[ui.div(ui.p(f"{task['task_name']}", class_="font-weight-bold"), ui.p(f"Due: {task['due_date']} | Priority: {task['priority']}", class_="small text-muted"), class_="task-overdue") for task in status['overdue_tasks']]) if status['overdue_tasks'] else ui.p("All tasks on schedule", class_="text-success")
            ),
            ui.hr(),
            ui.card(ui.card_header("Enrollee Status Breakdown"), ui.output_plot("enrollee_status_chart"))
        )

    @output
    @render.plot
    def enrollee_status_chart():
        sel = input.selected_audit()
        if not sel:
            return go.Figure()
        audit_id = int(sel)
        status = command_center.get_audit_status(audit_id)
        if not status or not status.get('enrollee_status'):
            return go.Figure()
        df = pd.DataFrame(list(status['enrollee_status'].items()), columns=['Status', 'Count'])
        fig = px.pie(df, values='Count', names='Status', title='Record Request Status')
        fig.update_layout(height=400)
        return fig

    # Chart Selection AI
    @reactive.Effect
    def load_enrollees_for_chart_selection():
        audits = active_audits.get()
        sel = input.selected_audit_charts()
        if not audits or not sel:
            return
        audit_id = int(sel)
        enrollees = command_center.get_enrollees_for_record_request(audit_id)
        if not enrollees.empty:
            choices = {str(row['sample_id']): f"{row['enrollee_name']} ({row['enrollee_id']})" for _, row in enrollees.iterrows()}
            ui.update_select("enrollee_selector", choices=choices)

    @reactive.Effect
    @reactive.event(input.score_charts)
    def score_enrollee_charts():
        if not input.enrollee_selector() or not input.selected_audit_charts():
            return
        audit_id = int(input.selected_audit_charts())
        sample_id = int(input.enrollee_selector())
        param_placeholder = '%s' if db.db_type == 'postgresql' else '?'
        enrollee_query = f"SELECT enrollee_id, hccs_to_validate FROM audit_sample_enrollees WHERE sample_id = {param_placeholder}"
        enrollee = db.execute_query(enrollee_query, (sample_id,), fetch="one")
        if not enrollee:
            return
        hccs = enrollee['hccs_to_validate']
        if db.db_type == 'sqlite':
            hccs = json.loads(hccs) if hccs else []
        scores = chart_selector.score_all_charts_for_enrollee(audit_id=audit_id, sample_id=sample_id, enrollee_id=enrollee['enrollee_id'], hccs_to_validate=hccs)
        chart_scores.set(scores)

    @reactive.Effect
    @reactive.event(input.get_all_recommendations)
    def get_all_chart_recommendations():
        if not input.selected_audit_charts():
            return
        audit_id = int(input.selected_audit_charts())
        recommendations = chart_selector.get_submission_recommendations(audit_id)
        chart_scores.set(recommendations)

    @output
    @render.ui
    def chart_selection_results():
        scores = chart_scores.get()
        if scores.empty:
            return ui.div(ui.p("Select enrollee and click 'Score Charts'", class_="text-muted text-center p-5"))
        results = []
        for _, row in scores.iterrows():
            recommendation_class = {'SUBMIT_FIRST': 'chart-recommended', 'SUBMIT_BACKUP': 'chart-backup', 'DO_NOT_SUBMIT': 'chart-reject'}.get(row.get('recommendation', 'SUBMIT_BACKUP'), '')
            display_date = row.get('encounter_date', row.get('enrollee_name', 'Unknown'))
            results.append(ui.div(
                ui.row(
                    ui.column(8, ui.h5(f"Encounter: {display_date}" if 'encounter_date' in row else f"Enrollee: {display_date}"), ui.p(f"Provider: {row.get('provider_id', 'Unknown')}", class_="text-muted"), ui.p(f"Score: {row.get('overall_score', 0):.1f}/100", class_="font-weight-bold")),
                    ui.column(4, ui.div(ui.h6(row.get('recommendation', 'PENDING').replace('_', ' ')), ui.p(f"Confidence: {row.get('confidence_level', 0):.0f}%", class_="small"), class_="text-end"))
                ),
                class_=f"p-3 mb-2 rounded {recommendation_class}"
            ))
        return ui.div(ui.h4("Chart Recommendations"), ui.p(f"Showing {len(scores)} record(s)", class_="text-muted"), ui.hr(), *results)

    # Education Tracker
    @reactive.Effect
    def load_education_dashboard():
        dashboard = educator.get_education_dashboard()
        education_dashboard.set(dashboard)

    @output
    @render.ui
    def education_total_sessions():
        data = education_dashboard.get()
        return ui.div(ui.h3(str(data.get('total_sessions', 0))), ui.p("Total Sessions"), class_="metric-card")

    @output
    @render.ui
    def education_upcoming():
        data = education_dashboard.get()
        return ui.div(ui.h3(str(data.get('upcoming_sessions', 0))), ui.p("Upcoming Sessions"), class_="metric-card")

    @output
    @render.ui
    def education_avg_improvement():
        data = education_dashboard.get()
        improvement = data.get('avg_improvement', 0) or 0
        improvement_class = "text-success" if improvement > 5 else "text-warning" if improvement > 0 else "text-danger"
        return ui.div(ui.h3(f"{improvement:+.1f}%", class_=improvement_class), ui.p("Avg Improvement"), ui.p("Post-training", class_="small text-muted"), class_="metric-card")

    @output
    @render.ui
    def education_completed():
        data = education_dashboard.get()
        return ui.div(ui.h3(str(data.get('completed_sessions', 0))), ui.p("Completed Sessions"), class_="metric-card")

    @reactive.Effect
    @reactive.event(input.identify_tpe_providers)
    def identify_tpe_providers_action():
        providers = educator.identify_providers_for_tpe(min_failures=5, lookback_months=6)
        tpe_providers.set(providers)

    @output
    @render.data_frame
    def tpe_providers_table():
        providers = tpe_providers.get()
        if providers.empty:
            return pd.DataFrame()
        display_df = providers[['provider_name', 'specialty', 'validation_rate', 'risk_tier', 'financial_risk_estimate']].copy()
        display_df.columns = ['Provider', 'Specialty', 'Validation %', 'Risk', 'Financial Risk ($)']
        return render.DataGrid(display_df, selection_mode="row", width="100%")

    @reactive.Effect
    @reactive.event(input.schedule_session)
    def schedule_education_session():
        if not input.edu_provider_select():
            return
        df = provider_scores_data.get()
        provider_name = input.edu_provider_select()
        provider_data = df[df['provider_name'] == provider_name]
        if provider_data.empty:
            return
        provider_id = provider_data.iloc[0]['provider_id']
        patterns = db.get_provider_failure_patterns(provider_id, 6)
        focus_areas = patterns['failure_category'].head(3).tolist() if not patterns.empty else ['M.E.A.T. Framework']
        session_date = input.edu_session_date()
        session_date_str = session_date.strftime('%Y-%m-%d') if hasattr(session_date, 'strftime') else str(session_date)
        session_id = educator.create_education_session(provider_id=provider_id, focus_areas=focus_areas, scheduled_date=session_date_str, educator="Auto-assigned")
        session.session_scheduled_id = session_id

    @output
    @render.ui
    def session_scheduled_msg():
        if hasattr(session, 'session_scheduled_id'):
            return ui.div(ui.div(ui.p(f"Education session scheduled (ID: {session.session_scheduled_id})", class_="text-success"), ui.p("Materials have been auto-assigned and sent to provider", class_="small text-muted"), class_="alert alert-success"))
        return ui.div()

    @output
    @render.plot
    def education_effectiveness_chart():
        results = db.execute_query("""
            SELECT provider_id, pre_session_validation_rate, post_session_validation_rate, completed_date
            FROM education_sessions
            WHERE session_status = 'COMPLETED' AND post_session_validation_rate IS NOT NULL
            ORDER BY completed_date DESC LIMIT 20
        """, (), fetch="all")
        if not results:
            return go.Figure().add_annotation(text="No completed sessions yet", showarrow=False)
        df = pd.DataFrame(results)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['pre_session_validation_rate'], mode='lines+markers', name='Pre-Training'))
        fig.add_trace(go.Scatter(x=df.index, y=df['post_session_validation_rate'], mode='lines+markers', name='Post-Training'))
        fig.update_layout(title="Training Effectiveness (Pre vs Post Validation Rates)", xaxis_title="Session", yaxis_title="Validation Rate (%)", height=400)
        return fig

    # ==================== PHASE 3 LOGIC ====================

    # Real-Time Validation
    @output
    @render.ui
    def realtime_total_validated():
        metrics = realtime_engine.get_validation_dashboard_metrics()
        return ui.div(ui.h3(str(metrics.get("total_validated_24h", 0))), ui.p("Validated (24h)"), class_="metric-card")

    @output
    @render.ui
    def realtime_processing_rate():
        metrics = realtime_engine.get_validation_dashboard_metrics()
        rate = metrics.get("processing_rate", 0)
        return ui.div(ui.h3(f"{rate}%"), ui.p("Processing Rate"), class_="metric-card")

    @output
    @render.ui
    def realtime_active_alerts():
        metrics = realtime_engine.get_validation_dashboard_metrics()
        total = metrics.get("total_alerts", 0)
        alert_class = "metric-card risk-red" if total > 10 else "metric-card"
        return ui.div(ui.h3(str(total)), ui.p("Active Alerts"), class_=alert_class)

    @output
    @render.ui
    def realtime_queue_depth():
        try:
            r = db.execute_query("SELECT COUNT(*) as cnt FROM realtime_validation_queue WHERE queue_status = 'PENDING'", (), fetch="one")
            cnt = r.get("cnt", 0) if r else 0
        except Exception:
            cnt = 0
        return ui.div(ui.h3(str(cnt)), ui.p("Queue Depth"), class_="metric-card")

    @output
    @render.ui
    def provider_live_feedback_display():
        pid = input.realtime_provider_select()
        if not pid:
            return ui.div(ui.p("Select a provider", class_="text-muted"))
        feedback = realtime_engine.get_provider_live_feedback(pid)
        if feedback.get("status") == "NO_RECENT_ACTIVITY":
            return ui.div(ui.p(feedback.get("message", "No recent documentation"), class_="text-muted"))
        return ui.div(
            ui.h4(f"Current Session: {feedback.get('current_session_rate', 0):.1f}% Validation Rate"),
            ui.p(f"HCCs Documented: {feedback.get('hccs_documented', 0)} | Failed: {feedback.get('hccs_failed', 0)}", class_="text-muted"),
            ui.hr(),
            ui.h5("Most Common Gap"),
            ui.p(f"{feedback.get('most_common_gap', 'N/A')} element", class_="font-weight-bold"),
            ui.hr(),
            ui.div(ui.p(feedback.get("recommendation", ""), class_="alert alert-info")),
            class_="p-3"
        )

    @output
    @render.data_frame
    def validation_alerts_table():
        try:
            alerts = db.execute_query(
                "SELECT alert_type, severity, title, message, triggered_at FROM automated_alerts WHERE dismissed = FALSE ORDER BY triggered_at DESC LIMIT 20",
                (), fetch="all"
            )
            if not alerts:
                return pd.DataFrame()
            return render.DataGrid(pd.DataFrame(alerts), width="100%")
        except Exception:
            return pd.DataFrame()

    # HCC Reconciliation
    @output
    @render.ui
    def recon_add_opportunities():
        dash = reconciler.get_reconciliation_dashboard()
        add = dash.get("add_opportunities", {})
        return ui.div(
            ui.h3(str(add.get("count", 0))),
            ui.p("ADD Opportunities"),
            ui.p(f"Value: ${add.get('total_impact', 0):,.0f}", class_="small text-success"),
            class_="metric-card"
        )

    @output
    @render.ui
    def recon_delete_requirements():
        dash = reconciler.get_reconciliation_dashboard()
        dlt = dash.get("delete_requirements", {})
        count = dlt.get("count", 0)
        risk_class = "metric-card risk-red" if count > 10 else "metric-card"
        return ui.div(
            ui.h3(str(count)),
            ui.p("DELETE Requirements"),
            ui.p(f"Risk: ${dlt.get('total_impact', 0):,.0f}", class_="small text-danger"),
            class_=risk_class
        )

    @output
    @render.ui
    def recon_net_impact():
        dash = reconciler.get_reconciliation_dashboard()
        net = dash.get("net_financial_impact", 0)
        net_class = "text-success" if net >= 0 else "text-danger"
        return ui.div(
            ui.h3(f"${abs(net):,.0f}", class_=net_class),
            ui.p("Net Financial Impact"),
            ui.p("Positive" if net >= 0 else "Negative", class_=f"small {net_class}"),
            class_="metric-card"
        )

    @output
    @render.ui
    def recon_action_rate():
        dash = reconciler.get_reconciliation_dashboard()
        rate = dash.get("action_rate", 0)
        return ui.div(
            ui.h3(f"{rate:.1f}%"),
            ui.p("Action Rate"),
            ui.p("Last 30 days", class_="small text-muted"),
            class_="metric-card"
        )

    @reactive.Effect
    @reactive.event(input.run_reconciliation)
    def run_reconciliation_action():
        lookback = int(input.recon_lookback())
        results = reconciler.run_comprehensive_reconciliation(lookback_months=lookback, min_confidence=85.0)
        reconciliation_data.set(results)

    @output
    @render.ui
    def reconciliation_results():
        data = reconciliation_data.get()
        if not data:
            return ui.div(ui.p("Click 'Run Reconciliation' to analyze", class_="text-muted text-center p-4"))
        summary = data.get("summary", {})
        net = summary.get("net_financial_impact", 0)
        result_class = "alert alert-success" if net > 0 else "alert alert-warning"
        return ui.div(
            ui.div(
                ui.h4("Reconciliation Complete"),
                ui.p(f"Found {summary.get('total_add_opportunities', 0)} ADD opportunities worth ${summary.get('add_financial_value', 0):,.0f}"),
                ui.p(f"Found {summary.get('total_delete_required', 0)} DELETE requirements risking ${summary.get('delete_financial_risk', 0):,.0f}"),
                ui.p(f"Net impact: ${net:,.0f}", class_="font-weight-bold"),
                class_=result_class
            )
        )

    @output
    @render.data_frame
    def recon_add_table():
        data = reconciliation_data.get()
        adds = data.get("add_recommendations", [])
        if not adds:
            return pd.DataFrame()
        df = pd.DataFrame(adds)
        if df.empty:
            return pd.DataFrame()
        col_map = {"patient_id": "Patient", "hcc_code": "HCC", "hcc_description": "Description", "confidence_score": "Confidence", "financial_impact": "Value ($)"}
        cols = [c for c in col_map if c in df.columns]
        if cols:
            display_df = df[cols].head(20).rename(columns={c: col_map[c] for c in cols})
            return render.DataGrid(display_df, width="100%")
        return render.DataGrid(df.head(20), width="100%")

    @output
    @render.data_frame
    def recon_delete_table():
        data = reconciliation_data.get()
        deletes = data.get("delete_recommendations", [])
        if not deletes:
            return pd.DataFrame()
        df = pd.DataFrame(deletes)
        if df.empty:
            return pd.DataFrame()
        col_map = {"patient_id": "Patient", "hcc_code": "HCC", "hcc_description": "Description", "confidence_score": "Confidence", "financial_impact": "Risk ($)"}
        cols = [c for c in col_map if c in df.columns]
        if cols:
            display_df = df[cols].head(20).rename(columns={c: col_map[c] for c in cols})
            return render.DataGrid(display_df, width="100%")
        return render.DataGrid(df.head(20), width="100%")

    # Compliance Forecast
    @reactive.Effect
    @reactive.event(input.generate_forecast)
    def generate_forecast_action():
        periods = int(input.forecast_periods() or 12)
        conf = float(input.forecast_confidence() or 0.95)
        result = forecaster.generate_forecast(forecast_periods=periods, confidence_level=conf)
        forecast_data.set(result)

    @output
    @render.ui
    def forecast_summary():
        data = forecast_data.get()
        if not data or data.get("error"):
            return ui.div(ui.p("Click 'Generate Forecast'", class_="text-muted text-center p-4"))
        summary = data.get("trend_summary", {})
        trajectory = summary.get("validation_rate_trajectory", "N/A")
        trajectory_class = {"IMPROVING": "text-success", "DECLINING": "text-danger", "STABLE": "text-warning"}.get(trajectory, "")
        return ui.div(
            ui.h4("Forecast Summary"),
            ui.p(f"Model Accuracy: {data.get('model_accuracy', 0)}%", class_="text-muted"),
            ui.p(f"Trajectory: {trajectory}", class_=f"font-weight-bold {trajectory_class}"),
            ui.p(f"Validation Rate Change: {summary.get('validation_rate_change', 0):+.2f}%"),
            ui.p(f"Breach Risk: {summary.get('breach_risk', 'N/A')}", class_="font-weight-bold"),
            class_="alert alert-info"
        )

    @output
    @render.plot
    def forecast_chart():
        data = forecast_data.get()
        if not data or data.get("error") or not data.get("forecasts"):
            return go.Figure().add_annotation(text="Generate forecast first", showarrow=False)
        df = pd.DataFrame(data["forecasts"])
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["forecast_period"], y=df["predicted_validation_rate"],
            mode="lines+markers", name="Predicted Validation Rate", line=dict(color="blue")
        ))
        fig.add_trace(go.Scatter(
            x=df["forecast_period"], y=df["confidence_interval_high"],
            mode="lines", name="Upper Bound", line=dict(width=0), showlegend=False
        ))
        fig.add_trace(go.Scatter(
            x=df["forecast_period"], y=df["confidence_interval_low"],
            mode="lines", fill="tonexty", name="Lower Bound",
            line=dict(width=0), fillcolor="rgba(0,100,255,0.2)", showlegend=False
        ))
        fig.add_hline(y=95, line_dash="dash", line_color="green", annotation_text="Target (95%)")
        fig.update_layout(title="12-Month Compliance Forecast", xaxis_title="Period", yaxis_title="Validation Rate (%)", height=500)
        return fig

    @output
    @render.ui
    def forecast_drivers():
        data = forecast_data.get()
        if not data or data.get("error") or not data.get("forecasts"):
            return ui.p("Generate forecast to see drivers", class_="text-muted")
        drivers = data["forecasts"][0].get("key_drivers", [])
        return ui.tags.ul(*[ui.tags.li(d) for d in drivers]) if drivers else ui.p("No drivers identified")

    # Regulatory Intelligence
    @reactive.Effect
    def _load_regulatory_updates():
        regulatory_updates.set(reg_intel.get_unprocessed_updates())

    @output
    @render.ui
    def reg_total_updates():
        dash = reg_intel.get_regulatory_dashboard()
        return ui.div(ui.h3(str(dash.get("total_updates_90d", 0))), ui.p("Updates (90d)"), class_="metric-card")

    @output
    @render.ui
    def reg_high_priority():
        dash = reg_intel.get_regulatory_dashboard()
        high = dash.get("high_priority_pending", 0)
        high_class = "metric-card risk-red" if high > 0 else "metric-card"
        return ui.div(ui.h3(str(high)), ui.p("High Priority"), class_=high_class)

    @output
    @render.ui
    def reg_unprocessed():
        dash = reg_intel.get_regulatory_dashboard()
        return ui.div(ui.h3(str(dash.get("unprocessed_updates", 0))), ui.p("Unprocessed"), class_="metric-card")

    @reactive.Effect
    @reactive.event(input.scan_regulatory)
    def scan_regulatory_action():
        reg_intel.scan_regulatory_sources(days_back=30)
        regulatory_updates.set(reg_intel.get_unprocessed_updates())

    @output
    @render.ui
    def regulatory_updates_list():
        updates = regulatory_updates.get()
        if not updates:
            return ui.div(ui.p("No pending updates. Click 'Scan Sources' to check for new updates.", class_="text-muted text-center p-4"))
        items = []
        for u in updates[:10]:
            impact_class = {"HIGH": "audit-critical", "MEDIUM": "audit-warning", "LOW": ""}.get(u.get("impact_level", ""), "")
            items.append(ui.div(
                ui.h5(u.get("title", "Untitled")),
                ui.p(f"Source: {u.get('source', '')} | Date: {u.get('update_date', '')} | Impact: {u.get('impact_level', 'N/A')}", class_="small text-muted"),
                ui.p(u.get("summary", "")),
                ui.p(f"Implementation: {u.get('implementation_date', '')}", class_="small"),
                ui.tags.a("View Details", href=u.get("url", "#"), target="_blank", class_="btn btn-sm btn-outline-primary") if u.get("url") else ui.div(),
                class_=f"p-3 mb-3 rounded {impact_class}"
            ))
        return ui.div(*items)

    # EMR Rules
    @reactive.Effect
    @reactive.event(input.create_standard_rules)
    def create_standard_rules_action():
        created = emr_builder.create_standard_rules()
        rules_created.set(created)

    @output
    @render.ui
    def rules_created_msg():
        created = rules_created.get()
        if not created:
            return ui.div()
        success = sum(1 for r in created if r.get("rule_id"))
        return ui.div(ui.p(f"Created {success} of {len(created)} standard rules", class_="text-success"), class_="p-2")

    @output
    @render.data_frame
    def rule_effectiveness_table():
        report = emr_builder.get_rule_effectiveness_report()
        if not report:
            return pd.DataFrame()
        df = pd.DataFrame(report)
        col_map = {"rule_name": "Rule Name", "rule_type": "Type", "rule_severity": "Severity", "trigger_count": "Triggers"}
        cols = [c for c in col_map if c in df.columns]
        if cols:
            return render.DataGrid(df[cols].rename(columns=col_map), width="100%")
        return render.DataGrid(df, width="100%")

    @reactive.Effect
    @reactive.event(input.test_rules)
    def test_rules_action():
        hcc = input.test_hcc_code()
        selected = list(input.test_meat_elements())
        meat = {k: k in selected for k in ["monitor", "evaluate", "assess", "treat"]}
        violations = emr_builder.evaluate_encounter_against_rules(hcc_codes=[hcc], meat_elements=meat)
        rule_test_violations.set(violations)

    @output
    @render.ui
    def rule_test_results():
        violations = rule_test_violations.get()
        if violations is None:
            return ui.div(ui.p("Select HCC and M.E.A.T. elements, then click 'Test Rules'", class_="text-muted"))
        if not violations:
            return ui.div(ui.p("No violations detected. Documentation passes all rules.", class_="alert alert-success"))
        items = []
        for v in violations:
            severity_class = {"CRITICAL": "audit-critical", "WARNING": "audit-warning", "INFO": ""}.get(v.get("severity", ""), "")
            items.append(ui.div(
                ui.h5(f"{v.get('rule_type', '')}: {v.get('rule_name', '')}"),
                ui.p(v.get("message", "")),
                ui.p(f"Missing: {', '.join(v.get('missing_elements', []))}", class_="small font-weight-bold"),
                class_=f"p-3 mb-2 rounded {severity_class}"
            ))
        return ui.div(*items)

    # Executive Dashboard
    @output
    @render.ui
    def exec_financial_exposure():
        data = dashboard_mgr.get_executive_dashboard_data()
        exp = data.get("financial_exposure", {})
        return ui.div(
            ui.h3(f"${exp.get('annualized', 0):,.0f}"),
            ui.p("Annual Risk Exposure"),
            ui.p(f"Validation: {exp.get('validation_rate', 0):.1f}%", class_="small text-muted"),
            class_="metric-card"
        )

    @output
    @render.ui
    def exec_validation_rate():
        data = dashboard_mgr.get_executive_dashboard_data()
        rate = data.get("financial_exposure", {}).get("validation_rate", 0)
        delta = rate - 95
        delta_class = "text-success" if delta >= 0 else "text-danger"
        return ui.div(
            ui.h3(f"{rate:.1f}%"),
            ui.p("Organization Validation Rate"),
            ui.p(f"{delta:+.1f}% vs target", class_=f"small {delta_class}"),
            class_="metric-card"
        )

    @output
    @render.ui
    def exec_active_audits():
        data = dashboard_mgr.get_executive_dashboard_data()
        return ui.div(
            ui.h3(str(data.get("active_audits", 0))),
            ui.p("Active RADV Audits"),
            ui.p("In progress", class_="small text-muted"),
            class_="metric-card"
        )

    @output
    @render.plot
    def exec_risk_chart():
        data = dashboard_mgr.get_executive_dashboard_data()
        risk_dist = data.get("provider_risk_distribution", {})
        if not risk_dist:
            return go.Figure().add_annotation(text="No provider data", showarrow=False)
        tiers = list(risk_dist.keys())
        counts = [risk_dist[t].get("provider_count", 0) for t in tiers]
        colors = {"GREEN": "#28a745", "YELLOW": "#ffc107", "RED": "#dc3545"}
        fig = px.bar(x=tiers, y=counts, labels={"x": "Risk Tier", "y": "Provider Count"}, title="Provider Risk Distribution", color=tiers, color_discrete_map=colors)
        fig.update_layout(height=400, showlegend=False)
        return fig

    @output
    @render.plot
    def exec_forecast_chart():
        forecast_dash = forecaster.get_forecast_dashboard()
        if forecast_dash.get("status") == "NO_FORECAST_AVAILABLE" or not forecast_dash.get("forecasts"):
            return go.Figure().add_annotation(text="No forecast data", showarrow=False)
        df = pd.DataFrame(forecast_dash["forecasts"])
        fig = px.line(df, x="forecast_period", y="predicted_validation_rate", title="6-Month Compliance Forecast", labels={"forecast_period": "Period", "predicted_validation_rate": "Validation Rate (%)"})
        fig.add_hline(y=95, line_dash="dash", line_color="green")
        fig.update_layout(height=400)
        return fig

    @output
    @render.ui
    def exec_action_items():
        data = dashboard_mgr.get_executive_dashboard_data()
        actions = []
        val_rate = data.get("financial_exposure", {}).get("validation_rate", 100)
        if val_rate < 90:
            actions.append("CRITICAL: Validation rate below 90%. Implement immediate provider education program.")
        risk_dist = data.get("provider_risk_distribution", {})
        red_count = risk_dist.get("RED", {}).get("provider_count", 0)
        if red_count > 5:
            actions.append(f"HIGH: {red_count} providers in RED tier. Assign mandatory 1-on-1 coaching.")
        if data.get("active_audits", 0) > 0:
            actions.append(f"ACTIVE: {data['active_audits']} RADV audit(s) in progress. Monitor weekly.")
        if not actions:
            actions.append("All metrics within acceptable ranges. Continue current monitoring.")
        return ui.div(ui.tags.ul(*[ui.tags.li(a) for a in actions]))


app = App(app_ui, server)
