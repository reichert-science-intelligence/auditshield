# audit_trail.py
# ─────────────────────────────────────────────────────────────
# RADV Audit Trail — Google Sheets + Supabase Parallel Write
# AuditShield-Live | reichert-science-intelligence
# Phase 1: Writes to both backends when SUPABASE_URL/KEY set
# Brand: Purple #4A3E8F | Gold #D4AF37 | Green #10b981
# ─────────────────────────────────────────────────────────────

import os
import json
import gspread
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Optional
from google.oauth2.service_account import Credentials

# Supabase parallel write (Phase 1) — optional if env vars set
try:
    from supabase import create_client
    _SUPABASE_AVAILABLE = True
except ImportError:
    _SUPABASE_AVAILABLE = False

# ── Google Sheets Scopes ──────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# ── Sheet Column Schema ───────────────────────────────────────
AUDIT_COLUMNS = [
    "audit_id",
    "timestamp",
    "session_user",
    "measure_code",
    "measure_name",
    "hcc_codes",
    "gaps_flagged",
    "meat_status",        # M.E.A.T. validation result
    "radv_risk_score",
    "claude_summary",
    "audit_status",       # OPEN | REVIEWED | CLOSED
    "last_updated"
]


# ─────────────────────────────────────────────────────────────
# CONNECTION MANAGER
# ─────────────────────────────────────────────────────────────

class AuditTrailDB:
    """
    Manages all read/write operations to the Google Sheets
    audit trail backend for AuditShield-Live.

    Credentials loaded from:
      - HuggingFace Space Secret: GSHEETS_CREDS_JSON  (production)
      - Local file: service_account.json               (dev)
    """

    def __init__(self):
        self.client = None
        self.sheet = None
        self.connected = False
        self.last_error = None
        self._connect()

    def _connect(self):
        try:
            # ── Load credentials (HF Secret or local file) ──
            creds_json = os.environ.get("GSHEETS_CREDS_JSON")

            if creds_json:
                # HuggingFace Spaces: stored as Space Secret
                creds_dict = json.loads(creds_json)
                creds = Credentials.from_service_account_info(
                    creds_dict, scopes=SCOPES
                )
            elif os.path.exists("service_account.json"):
                # Local development fallback
                creds = Credentials.from_service_account_file(
                    "service_account.json", scopes=SCOPES
                )
            else:
                raise FileNotFoundError(
                    "No credentials found. Set GSHEETS_CREDS_JSON "
                    "as a HuggingFace Space Secret."
                )

            self.client = gspread.authorize(creds)

            # ── Open sheet by env var or default name ──
            sheet_id = os.environ.get("AUDIT_SHEET", "AuditShield_RADV_Audit_Trail")

            try:
                workbook = self.client.open(sheet_id)
            except gspread.SpreadsheetNotFound:
                # Auto-create if missing (first run)
                workbook = self.client.create(sheet_id)

            self.sheet = workbook.sheet1
            self._ensure_headers()
            self.connected = True

        except Exception as e:
            self.connected = False
            self.last_error = str(e)

    def _ensure_headers(self):
        """Write column headers if sheet is empty."""
        existing = self.sheet.row_values(1)
        if not existing:
            self.sheet.insert_row(AUDIT_COLUMNS, index=1)

    def status(self) -> dict:
        return {
            "connected": self.connected,
            "error": self.last_error,
            "timestamp": datetime.now(timezone(timedelta(hours=-5))).strftime("%I:%M:%S %p EST")
        }


# ─────────────────────────────────────────────────────────────
# AUDIT OPERATIONS
# ─────────────────────────────────────────────────────────────

def push_audit_record(db: AuditTrailDB, record: dict) -> dict:
    """
    Append a single RADV audit record to Google Sheets.

    record keys (all optional except measure_code):
        session_user, measure_code, measure_name,
        hcc_codes, gaps_flagged, meat_status,
        radv_risk_score, claude_summary, audit_status

    Returns: { success, audit_id, timestamp, error }
    """
    if not db.connected:
        return {
            "success": False,
            "error": f"Cloud disconnected: {db.last_error}"
        }

    try:
        now = datetime.now(timezone(timedelta(hours=-5)))
        audit_id = f"AUD-{now.strftime('%Y%m%d-%H%M%S')}"

        row = [
            audit_id,
            now.strftime("%Y-%m-%d %H:%M:%S"),
            record.get("session_user", "Analyst"),
            record.get("measure_code", ""),
            record.get("measure_name", ""),
            ", ".join(record.get("hcc_codes", [])),
            record.get("gaps_flagged", 0),
            record.get("meat_status", "PENDING"),
            record.get("radv_risk_score", 0.0),
            record.get("claude_summary", "")[:500],   # cap at 500 chars
            record.get("audit_status", "OPEN"),
            now.strftime("%Y-%m-%d %H:%M:%S")
        ]

        db.sheet.append_row(row)

        # Phase 1: Supabase parallel write (fire-and-forget)
        _push_audit_to_supabase(audit_id, row)

        return {
            "success": True,
            "audit_id": audit_id,
            "timestamp": now.strftime("%I:%M:%S %p EST"),
            "error": None
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def _push_audit_to_supabase(audit_id: str, row: list) -> None:
    """Parallel write to Supabase if configured. Silent on failure."""
    if not _SUPABASE_AVAILABLE:
        return
    url, key = os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY")
    if not url or not key:
        return
    try:
        client = create_client(url, key)
        client.table("audit_trail").insert({
            "audit_id": audit_id,
            "timestamp": row[1],
            "session_user": row[2],
            "measure_code": row[3],
            "measure_name": row[4],
            "hcc_codes": row[5],
            "gaps_flagged": row[6],
            "meat_status": row[7],
            "radv_risk_score": row[8],
            "claude_summary": row[9],
            "audit_status": row[10],
            "last_updated": row[11],
        }).execute()
    except Exception:
        pass  # non-blocking; Sheets is source of truth


def fetch_recent_audits(db: AuditTrailDB, n: int = 10) -> pd.DataFrame:
    """
    Pull the most recent N audit records from Google Sheets.
    Returns a formatted DataFrame for ui.render.data_frame.
    """
    if not db.connected:
        return pd.DataFrame(columns=AUDIT_COLUMNS)

    try:
        records = db.sheet.get_all_records()
        df = pd.DataFrame(records)

        if df.empty:
            return df

        # Most recent first, cap at n rows
        df = df.sort_values("timestamp", ascending=False).head(n)

        # Format for display
        display_cols = [
            "audit_id", "timestamp", "measure_code",
            "gaps_flagged", "meat_status",
            "radv_risk_score", "audit_status"
        ]
        return df[display_cols].reset_index(drop=True)

    except Exception as e:
        return pd.DataFrame({"Error": [str(e)]})


def update_audit_status(
    db: AuditTrailDB,
    audit_id: str,
    new_status: str
) -> dict:
    """
    Update a record's audit_status field by audit_id.
    new_status: OPEN | REVIEWED | CLOSED
    """
    if not db.connected:
        return {"success": False, "error": "Cloud disconnected"}

    try:
        cell = db.sheet.find(audit_id)
        if not cell:
            return {"success": False, "error": f"{audit_id} not found"}

        # audit_status is column 11 (1-indexed)
        status_col = AUDIT_COLUMNS.index("audit_status") + 1
        updated_col = AUDIT_COLUMNS.index("last_updated") + 1

        db.sheet.update_cell(cell.row, status_col, new_status)
        db.sheet.update_cell(
            cell.row, updated_col,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        return {"success": True, "audit_id": audit_id, "status": new_status}

    except Exception as e:
        return {"success": False, "error": str(e)}
