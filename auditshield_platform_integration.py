"""
AuditShield — Platform Hub integration (v3.1)
Exposes register_session and record_finding for app.py insertions.
Uses supabase_platform for platform_sessions and cross_app_findings.
"""
from __future__ import annotations

from supabase_platform import insert_cross_app_finding, insert_platform_session


def register_session(app_name: str = "auditshield", session_id: str | None = None, **kwargs) -> None:
    """Register a session in platform_sessions. Fire-and-forget; silent on failure."""
    insert_platform_session(app_name=app_name, session_id=session_id, **kwargs)


def record_finding(
    source_app: str = "auditshield",
    finding_type: str = "hcc_flag",
    title: str = "",
    description: str | None = None,
    severity: str = "medium",
    session_id: str | None = None,
    **kwargs,
) -> None:
    """
    Record a finding in cross_app_findings. Fire-and-forget; silent on failure.
    session_id: platform_sessions.id (UUID) if available; omit or None if not.
    """
    insert_cross_app_finding(
        source_app=source_app,
        finding_type=finding_type,
        title=title,
        description=description,
        severity=severity,
        session_id=None,  # cross_app_findings.session_id expects platform_sessions.id UUID
        **kwargs,
    )
