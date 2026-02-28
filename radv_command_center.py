"""
RADV Command Center - Audit Response Workflow
Manages the entire RADV audit response workflow when CMS sends an audit notice.
"""
import json
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from database import get_db_manager


class RADVCommandCenter:
    """
    Manages the entire RADV audit response workflow

    Key Functions:
    1. Import CMS audit notice and sample list
    2. Track 25-week deadline with milestone tracking
    3. Coordinate record retrieval from providers
    4. Monitor submission progress
    5. Generate status reports
    """

    def __init__(self):
        self.db = get_db_manager()

    def create_audit_from_notice(self,
                                 audit_notice_id: str,
                                 contract_id: str,
                                 contract_name: str,
                                 audit_year: int,
                                 notification_date: str,
                                 sample_enrollees: List[Dict]) -> int:
        """
        Initialize new RADV audit from CMS notice

        Args:
            audit_notice_id: CMS-provided audit ID
            contract_id: Contract H number
            contract_name: Plan name
            audit_year: Payment year being audited
            notification_date: Date audit notice received
            sample_enrollees: List of dicts with enrollee info

        Returns:
            audit_id of created audit
        """

        # Calculate medical record due date (25 weeks from notification)
        notification_dt = datetime.strptime(notification_date, '%Y-%m-%d')
        due_date = notification_dt + timedelta(weeks=25)
        due_date_str = due_date.strftime('%Y-%m-%d')

        param_placeholder = '%s' if self.db.db_type == 'postgresql' else '?'

        # Insert audit record
        audit_query = f"""
        INSERT INTO radv_audits (
            audit_notice_id, contract_id, contract_name, audit_year,
            notification_date, medical_record_due_date, sample_size,
            audit_status
        ) VALUES (
            {param_placeholder}, {param_placeholder}, {param_placeholder}, {param_placeholder},
            {param_placeholder}, {param_placeholder}, {param_placeholder}, 'ACTIVE'
        )
        """

        if self.db.db_type == 'postgresql':
            audit_query += " RETURNING audit_id"
            result = self.db.execute_query(
                audit_query,
                (audit_notice_id, contract_id, contract_name, audit_year,
                 notification_date, due_date_str, len(sample_enrollees)),
                fetch="one"
            )
            audit_id = result['audit_id']
        else:
            # SQLite: must get last_insert_rowid() on same connection as INSERT
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    audit_query,
                    (audit_notice_id, contract_id, contract_name, audit_year,
                     notification_date, due_date_str, len(sample_enrollees))
                )
                conn.commit()
                cursor.execute("SELECT last_insert_rowid()")
                audit_id = cursor.fetchone()[0]

        # Insert sample enrollees
        for enrollee in sample_enrollees:
            self._add_sample_enrollee(audit_id, enrollee)

        # Create audit timeline tasks
        self._generate_audit_tasks(audit_id, notification_dt, due_date)

        return audit_id

    def _add_sample_enrollee(self, audit_id: int, enrollee: Dict):
        """Add an enrollee to the audit sample"""

        param_placeholder = '%s' if self.db.db_type == 'postgresql' else '?'

        # Handle HCC list (array in PostgreSQL, JSON string in SQLite)
        hccs = enrollee.get('hccs_to_validate', [])
        if self.db.db_type == 'sqlite':
            hccs = json.dumps(hccs)

        query = f"""
        INSERT INTO audit_sample_enrollees (
            audit_id, enrollee_id, enrollee_name, date_of_birth,
            hccs_to_validate, total_raf_weight
        ) VALUES (
            {param_placeholder}, {param_placeholder}, {param_placeholder}, {param_placeholder},
            {param_placeholder}, {param_placeholder}
        )
        """

        self.db.execute_query(
            query,
            (audit_id, enrollee['enrollee_id'], enrollee.get('enrollee_name'),
             enrollee.get('date_of_birth'), hccs, enrollee.get('total_raf_weight', 0.0)),
            fetch="none"
        )

    def _generate_audit_tasks(self, audit_id: int, start_date: datetime, due_date: datetime):
        """
        Generate standard audit timeline tasks based on CMS RADV process

        Creates tasks for all major milestones
        """

        # Standard RADV timeline milestones
        tasks = [
            {
                'name': 'Review audit notice and sample list',
                'category': 'INITIAL_REVIEW',
                'due_offset_weeks': 1,
                'priority': 'HIGH'
            },
            {
                'name': 'Notify affected providers of record requests',
                'category': 'PROVIDER_NOTIFICATION',
                'due_offset_weeks': 2,
                'priority': 'HIGH'
            },
            {
                'name': 'Request medical records from providers (Batch 1)',
                'category': 'RECORD_REQUEST',
                'due_offset_weeks': 3,
                'priority': 'HIGH'
            },
            {
                'name': 'Follow up on outstanding record requests',
                'category': 'RECORD_REQUEST',
                'due_offset_weeks': 8,
                'priority': 'MEDIUM'
            },
            {
                'name': 'Complete internal chart review and selection',
                'category': 'CHART_REVIEW',
                'due_offset_weeks': 18,
                'priority': 'HIGH'
            },
            {
                'name': 'Prepare CDAT submission package',
                'category': 'SUBMISSION_PREP',
                'due_offset_weeks': 22,
                'priority': 'HIGH'
            },
            {
                'name': 'Final QA review before submission',
                'category': 'QA_REVIEW',
                'due_offset_weeks': 23,
                'priority': 'CRITICAL'
            },
            {
                'name': 'Submit medical records to CMS via CDAT',
                'category': 'SUBMISSION',
                'due_offset_weeks': 25,
                'priority': 'CRITICAL'
            }
        ]

        param_placeholder = '%s' if self.db.db_type == 'postgresql' else '?'

        for task in tasks:
            task_due_date = start_date + timedelta(weeks=task['due_offset_weeks'])

            query = f"""
            INSERT INTO audit_tasks (
                audit_id, task_name, task_category, due_date, priority, status
            ) VALUES (
                {param_placeholder}, {param_placeholder}, {param_placeholder},
                {param_placeholder}, {param_placeholder}, 'PENDING'
            )
            """

            self.db.execute_query(
                query,
                (audit_id, task['name'], task['category'],
                 task_due_date.strftime('%Y-%m-%d'), task['priority']),
                fetch="none"
            )

    def get_audit_status(self, audit_id: int) -> Dict:
        """
        Get comprehensive status of active audit

        Returns dashboard-ready metrics
        """

        param_placeholder = '%s' if self.db.db_type == 'postgresql' else '?'

        # Get audit details
        audit_query = f"""
        SELECT *
        FROM radv_audits
        WHERE audit_id = {param_placeholder}
        """

        audit = self.db.execute_query(audit_query, (audit_id,), fetch="one")

        if not audit:
            return {}

        # Calculate days remaining (defensive: handle None/missing due date)
        due_str = audit.get('medical_record_due_date')
        if due_str is None:
            due_str = datetime.now().strftime('%Y-%m-%d')
        try:
            due_date = datetime.strptime(str(due_str).strip()[:10], '%Y-%m-%d')
        except (ValueError, TypeError):
            due_date = datetime.now()
        days_remaining = max(0, (due_date - datetime.now()).days)
        weeks_remaining = days_remaining / 7 if days_remaining else 0

        # Get enrollee status breakdown
        enrollee_status_query = f"""
        SELECT
            record_request_status,
            COUNT(*) as count
        FROM audit_sample_enrollees
        WHERE audit_id = {param_placeholder}
        GROUP BY record_request_status
        """

        status_counts = self.db.execute_query(enrollee_status_query, (audit_id,), fetch="all")
        status_breakdown = {row['record_request_status']: row['count'] for row in status_counts}

        # Get submission progress
        submission_query = f"""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN submission_status = 'SUBMITTED' THEN 1 ELSE 0 END) as submitted,
            SUM(CASE WHEN records_received_date IS NOT NULL THEN 1 ELSE 0 END) as records_received
        FROM audit_sample_enrollees
        WHERE audit_id = {param_placeholder}
        """

        submission_stats = self.db.execute_query(submission_query, (audit_id,), fetch="one")
        # Defensive: SUM returns NULL when no rows; COUNT returns 0
        total = submission_stats.get('total') or 0
        submitted = submission_stats.get('submitted') or 0
        records_received = submission_stats.get('records_received') or 0

        # Get task progress
        task_query = f"""
        SELECT
            status,
            COUNT(*) as count
        FROM audit_tasks
        WHERE audit_id = {param_placeholder}
        GROUP BY status
        """

        task_counts = self.db.execute_query(task_query, (audit_id,), fetch="all")
        task_breakdown = {row['status']: row['count'] for row in task_counts}

        # Get overdue tasks
        overdue_query = f"""
        SELECT
            task_name,
            due_date,
            priority
        FROM audit_tasks
        WHERE audit_id = {param_placeholder}
        AND status != 'COMPLETED'
        AND due_date < CURRENT_DATE
        ORDER BY priority DESC, due_date ASC
        """
        if self.db.db_type == 'sqlite':
            overdue_query = overdue_query.replace("CURRENT_DATE", "DATE('now')")

        overdue_tasks = self.db.execute_query(overdue_query, (audit_id,), fetch="all")

        return {
            'audit_id': audit_id,
            'audit_notice_id': audit['audit_notice_id'],
            'contract_name': audit['contract_name'],
            'audit_year': audit['audit_year'],
            'notification_date': audit['notification_date'],
            'due_date': audit['medical_record_due_date'],
            'days_remaining': days_remaining,
            'weeks_remaining': round(weeks_remaining, 1),
            'sample_size': audit['sample_size'],
            'enrollee_status': status_breakdown,
            'submission_progress': {
                'total': submission_stats['total'],
                'submitted': submission_stats['submitted'],
                'records_received': submission_stats['records_received'],
                'pct_complete': round(submission_stats['submitted'] / submission_stats['total'] * 100, 1) if submission_stats['total'] > 0 else 0
            },
            'task_progress': task_breakdown,
            'overdue_tasks': overdue_tasks,
            'status_indicator': self._calculate_health_status(days_remaining, submission_stats)
        }

    def _calculate_health_status(self, days_remaining: int, submission_stats: Dict) -> str:
        """
        Determine overall audit health status

        Returns: 'ON_TRACK', 'AT_RISK', or 'CRITICAL'
        """
        total = submission_stats.get('total') or 0
        submitted = submission_stats.get('submitted') or 0
        pct_complete = submitted / total if total > 0 else 0
        pct_time_remaining = days_remaining / (25 * 7)  # 25 weeks total

        # If completion % is ahead of time remaining %, we're on track
        if pct_complete >= (1 - pct_time_remaining):
            return 'ON_TRACK'
        elif days_remaining < 14:  # Less than 2 weeks
            return 'CRITICAL'
        elif pct_complete < 0.5 and pct_time_remaining < 0.3:  # Less than 50% done with 30% time left
            return 'AT_RISK'
        else:
            return 'ON_TRACK'

    def update_record_request_status(self,
                                     sample_id: int,
                                     status: str,
                                     notes: Optional[str] = None):
        """Update status of medical record request for an enrollee"""

        param_placeholder = '%s' if self.db.db_type == 'postgresql' else '?'

        if self.db.db_type == 'postgresql':
            query = f"""
            UPDATE audit_sample_enrollees
            SET record_request_status = {param_placeholder},
                records_received_date = CASE WHEN {param_placeholder} = 'RECEIVED' THEN CURRENT_DATE ELSE records_received_date END,
                notes = COALESCE({param_placeholder}, notes)
            WHERE sample_id = {param_placeholder}
            """
        else:
            query = f"""
            UPDATE audit_sample_enrollees
            SET record_request_status = {param_placeholder},
                records_received_date = CASE WHEN {param_placeholder} = 'RECEIVED' THEN DATE('now') ELSE records_received_date END,
                notes = COALESCE({param_placeholder}, notes)
            WHERE sample_id = {param_placeholder}
            """

        self.db.execute_query(
            query,
            (status, status, notes, sample_id),
            fetch="none"
        )

    def get_enrollees_for_record_request(self, audit_id: int) -> pd.DataFrame:
        """
        Get list of enrollees needing record requests

        Returns DataFrame with provider contact info and HCC lists
        """

        param_placeholder = '%s' if self.db.db_type == 'postgresql' else '?'

        query = f"""
        SELECT
            ase.sample_id,
            ase.enrollee_id,
            ase.enrollee_name,
            ase.date_of_birth,
            ase.hccs_to_validate,
            ase.record_request_status,
            ase.notes
        FROM audit_sample_enrollees ase
        WHERE ase.audit_id = {param_placeholder}
        AND ase.record_request_status IN ('PENDING', 'REQUESTED')
        ORDER BY ase.enrollee_name
        """

        results = self.db.execute_query(query, (audit_id,), fetch="all")

        if not results:
            return pd.DataFrame()

        df = pd.DataFrame(results)

        # Parse HCC arrays for SQLite
        if self.db.db_type == 'sqlite':
            df['hccs_to_validate'] = df['hccs_to_validate'].apply(
                lambda x: json.loads(x) if x else []
            )

        return df

    def complete_task(self, task_id: int, completion_notes: Optional[str] = None):
        """Mark an audit task as completed"""

        param_placeholder = '%s' if self.db.db_type == 'postgresql' else '?'

        date_expr = "CURRENT_DATE" if self.db.db_type == 'postgresql' else "DATE('now')"

        query = f"""
        UPDATE audit_tasks
        SET status = 'COMPLETED',
            completed_date = {date_expr},
            completion_notes = {param_placeholder}
        WHERE task_id = {param_placeholder}
        """

        self.db.execute_query(query, (completion_notes, task_id), fetch="none")

    def get_upcoming_tasks(self, audit_id: int, days_ahead: int = 14) -> pd.DataFrame:
        """Get tasks due in the next N days"""

        param_placeholder = '%s' if self.db.db_type == 'postgresql' else '?'

        future_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')

        query = f"""
        SELECT
            task_id,
            task_name,
            task_category,
            due_date,
            priority,
            status,
            assigned_to
        FROM audit_tasks
        WHERE audit_id = {param_placeholder}
        AND status != 'COMPLETED'
        AND due_date <= {param_placeholder}
        ORDER BY due_date ASC, priority DESC
        """

        results = self.db.execute_query(query, (audit_id, future_date), fetch="all")

        if not results:
            return pd.DataFrame()

        return pd.DataFrame(results)


# ==================== DEMO DATA SEEDER ====================

def seed_demo_audit():
    """Create a demo RADV audit for testing"""

    command_center = RADVCommandCenter()

    # Create sample enrollees
    sample_enrollees = []
    for i in range(100):
        sample_enrollees.append({
            'enrollee_id': f'ENR{i+1:04d}',
            'enrollee_name': f'Patient {i+1}',
            'date_of_birth': f'19{50+i%40}-{(i%12)+1:02d}-15',
            'hccs_to_validate': ['HCC 36', 'HCC 226', 'HCC 280'][:((i % 3) + 1)],
            'total_raf_weight': round(0.5 + (i % 10) * 0.2, 3)
        })

    # Create audit (unique notice ID per run for demo)
    notice_id = f'RADV-2026-H1234-{datetime.now().strftime("%H%M%S")}'
    audit_id = command_center.create_audit_from_notice(
        audit_notice_id=notice_id,
        contract_id='H1234',
        contract_name='HealthPlan Medicare Advantage',
        audit_year=2025,
        notification_date='2026-01-15',
        sample_enrollees=sample_enrollees
    )

    print(f"Created demo audit: {audit_id}")
    print(f"   Sample size: {len(sample_enrollees)}")
    print(f"   Due date: {(datetime.strptime('2026-01-15', '%Y-%m-%d') + timedelta(weeks=25)).strftime('%Y-%m-%d')}")

    return audit_id


if __name__ == "__main__":
    from database_phase2_schema import add_phase2_schema
    from database import get_db_manager

    # Add Phase 2 schema
    db = get_db_manager()
    add_phase2_schema(db)

    # Create demo audit
    audit_id = seed_demo_audit()

    # Show status
    command_center = RADVCommandCenter()
    status = command_center.get_audit_status(audit_id)

    if status:
        print("\nAUDIT STATUS")
        print(f"Days Remaining: {status['days_remaining']}")
        print(f"Submission Progress: {status['submission_progress']['pct_complete']}%")
        print(f"Health Status: {status['status_indicator']}")
    else:
        print("\nCould not retrieve audit status.")
