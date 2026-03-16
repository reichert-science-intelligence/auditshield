"""
EMR Rule Builder - No-code validation rule builder for HCC documentation
Creates hard stop and soft prompt rules that fire when M.E.A.T. elements are missing
"""
import json

from database import get_db_manager


class EMRRuleBuilder:
    """
    No-code EMR validation rule builder

    Creates "hard stop" and "soft prompt" rules that fire in the EMR
    when providers document HCCs without proper M.E.A.T. elements
    """

    def __init__(self):
        self.db = get_db_manager()

    def create_rule(
        self,
        rule_name: str,
        rule_type: str,
        hcc_codes: list[str],
        required_elements: list[str],
        validation_message: str,
        severity: str = "WARNING",
    ) -> int:
        """
        Create a new EMR validation rule

        Args:
            rule_name: Human-readable rule name
            rule_type: 'HARD_STOP', 'SOFT_PROMPT', or 'ADVISORY'
            hcc_codes: List of HCC codes this rule applies to
            required_elements: M.E.A.T. elements required ['MONITOR', 'EVALUATE', 'ASSESS', 'TREAT']
            validation_message: Message to show provider
            severity: 'CRITICAL', 'WARNING', or 'INFO'

        Returns: rule_id
        """
        condition_logic = {
            "trigger": "HCC_CODED",
            "hcc_codes": hcc_codes,
            "required_meat_elements": required_elements,
            "min_elements_required": len(required_elements),
        }

        param_placeholder = "%s" if self.db.db_type == "postgresql" else "?"

        hcc_codes_param = hcc_codes
        condition_logic_param = json.dumps(condition_logic)

        if self.db.db_type == "sqlite":
            hcc_codes_param = json.dumps(hcc_codes)

        query = f"""
        INSERT INTO emr_validation_rules (
            rule_name, rule_type, hcc_codes, condition_logic,
            validation_message, rule_severity, active, created_by
        ) VALUES (
            {param_placeholder}, {param_placeholder}, {param_placeholder}, {param_placeholder},
            {param_placeholder}, {param_placeholder}, TRUE, 'SYSTEM'
        )
        """

        params = (
            rule_name,
            rule_type,
            hcc_codes_param,
            condition_logic_param,
            validation_message,
            severity,
        )

        if self.db.db_type == "postgresql":
            query += " RETURNING rule_id"
            result = self.db.execute_query(query, params, fetch="one")
            rule_id = result["rule_id"]
        else:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                cursor.execute("SELECT last_insert_rowid()")
                rule_id = cursor.fetchone()[0]
                conn.commit()

        return rule_id

    def create_standard_rules(self) -> list[dict]:
        """Create standard best-practice rules for common HCC categories"""
        standard_rules = [
            {
                "rule_name": "CHF: Require Monitor + Treat Elements",
                "rule_type": "HARD_STOP",
                "hcc_codes": ["HCC 226"],
                "required_elements": ["MONITOR", "TREAT"],
                "validation_message": "CHF Documentation Incomplete: You must document both current symptoms (Monitor) and current medication/treatment plan (Treat) for CHF to be valid for risk adjustment.",
                "severity": "CRITICAL",
            },
            {
                "rule_name": "Diabetes with Complications: Link Required",
                "rule_type": "HARD_STOP",
                "hcc_codes": ["HCC 36", "HCC 37", "HCC 38"],
                "required_elements": ["EVALUATE", "TREAT"],
                "validation_message": "Diabetes Complication Must Be Linked: Document the specific complication (neuropathy, nephropathy, etc.) and its relationship to diabetes. Include recent lab values (Evaluate) and treatment plan (Treat).",
                "severity": "CRITICAL",
            },
            {
                "rule_name": "COPD: Inhaler Documentation Required",
                "rule_type": "SOFT_PROMPT",
                "hcc_codes": ["HCC 280"],
                "required_elements": ["MONITOR", "TREAT"],
                "validation_message": "COPD Documentation Tip: Document current symptoms/status (Monitor) and specify inhaler medications with frequency (Treat) to ensure RADV compliance.",
                "severity": "WARNING",
            },
            {
                "rule_name": "CKD: Stage and GFR Required",
                "rule_type": "HARD_STOP",
                "hcc_codes": ["HCC 326", "HCC 327", "HCC 328", "HCC 329"],
                "required_elements": ["EVALUATE", "ASSESS"],
                "validation_message": "CKD Documentation Incomplete: You must document the specific CKD stage (3, 4, or 5), reference recent GFR value (Evaluate), and note impact on treatment decisions (Assess).",
                "severity": "CRITICAL",
            },
            {
                "rule_name": "Major Depression: Treatment Plan Required",
                "rule_type": "SOFT_PROMPT",
                "hcc_codes": ["HCC 155"],
                "required_elements": ["ASSESS", "TREAT"],
                "validation_message": "MDD Documentation: For Major Depressive Disorder to qualify for risk adjustment, document clinical assessment of current status (Assess) and treatment plan including medications/therapy (Treat).",
                "severity": "WARNING",
            },
            {
                "rule_name": "Morbid Obesity: BMI Required",
                "rule_type": "HARD_STOP",
                "hcc_codes": ["HCC 22"],
                "required_elements": ["MONITOR"],
                "validation_message": "Morbid Obesity requires BMI >=40 (or >=35 with comorbidities) documented in this encounter. Current BMI not found.",
                "severity": "CRITICAL",
            },
            {
                "rule_name": "Active Cancer: Treatment Status Required",
                "rule_type": "HARD_STOP",
                "hcc_codes": ["HCC 17", "HCC 18", "HCC 19", "HCC 20", "HCC 21"],
                "required_elements": ["EVALUATE", "TREAT"],
                "validation_message": "Cancer Documentation: Distinguish 'Active' (under treatment/surveillance) from 'History of' (resolved). Document current treatment status (Evaluate + Treat).",
                "severity": "CRITICAL",
            },
        ]

        created_rules = []
        for rule in standard_rules:
            try:
                rule_id = self.create_rule(**rule)
                created_rules.append(
                    {"rule_id": rule_id, "rule_name": rule["rule_name"]}
                )
            except Exception as e:
                created_rules.append(
                    {"rule_id": None, "rule_name": rule["rule_name"], "error": str(e)}
                )

        return created_rules

    def evaluate_encounter_against_rules(
        self,
        hcc_codes: list[str],
        meat_elements: dict[str, bool],
    ) -> list[dict]:
        """
        Evaluate an encounter against active rules

        Returns list of rule violations
        """
        query = """
        SELECT *
        FROM emr_validation_rules
        WHERE active = TRUE
        """
        all_rules = self.db.execute_query(query, fetch="all")

        violations = []
        for rule in all_rules:
            rule_hcc_codes = rule.get("hcc_codes")
            condition_logic = rule.get("condition_logic")

            if self.db.db_type == "sqlite":
                rule_hcc_codes = (
                    json.loads(rule_hcc_codes) if isinstance(rule_hcc_codes, str) else rule_hcc_codes or []
                )
                condition_logic = (
                    json.loads(condition_logic) if isinstance(condition_logic, str) else condition_logic or {}
                )

            if not rule_hcc_codes or not any(
                hcc in rule_hcc_codes for hcc in (hcc_codes or [])
            ):
                continue

            required_elements = condition_logic.get("required_meat_elements", [])
            missing_elements = []

            for element in required_elements:
                element_key = element.lower()
                if not meat_elements.get(element_key, False):
                    missing_elements.append(element)

            if missing_elements:
                violations.append(
                    {
                        "rule_id": rule["rule_id"],
                        "rule_name": rule["rule_name"],
                        "rule_type": rule["rule_type"],
                        "severity": rule.get("rule_severity", "WARNING"),
                        "message": rule.get("validation_message", ""),
                        "missing_elements": missing_elements,
                    }
                )
                self._increment_rule_trigger(rule["rule_id"])

        return violations

    def _increment_rule_trigger(self, rule_id: int):
        """Increment rule trigger count for analytics"""
        param_placeholder = "%s" if self.db.db_type == "postgresql" else "?"

        ts_expr = (
            "CURRENT_TIMESTAMP"
            if self.db.db_type == "postgresql"
            else "DATETIME('now')"
        )
        query = f"""
        UPDATE emr_validation_rules
        SET trigger_count = trigger_count + 1,
            last_triggered = {ts_expr}
        WHERE rule_id = {param_placeholder}
        """
        self.db.execute_query(query, (rule_id,), fetch="none")

    def get_rule_effectiveness_report(self) -> list[dict]:
        """Get report on which rules are most effective"""
        query = """
        SELECT
            rule_id,
            rule_name,
            rule_type,
            rule_severity,
            trigger_count,
            last_triggered
        FROM emr_validation_rules
        WHERE active = TRUE
        ORDER BY trigger_count DESC
        """
        rules = self.db.execute_query(query, fetch="all")
        return rules or []

    def toggle_rule(self, rule_id: int, active: bool):
        """Enable or disable a rule"""
        param_placeholder = "%s" if self.db.db_type == "postgresql" else "?"

        query = f"""
        UPDATE emr_validation_rules
        SET active = {param_placeholder}
        WHERE rule_id = {param_placeholder}
        """
        self.db.execute_query(query, (active, rule_id), fetch="none")


if __name__ == "__main__":
    builder = EMRRuleBuilder()

    print("Creating standard EMR validation rules...")
    rules = builder.create_standard_rules()

    print(f"\nCreated {len(rules)} rules:")
    for rule in rules:
        status = f"rule_id={rule['rule_id']}" if rule.get("rule_id") else f"error: {rule.get('error', 'unknown')}"
        print(f"   - {rule['rule_name']} ({status})")

    print("\nTesting rule evaluation...")
    violations = builder.evaluate_encounter_against_rules(
        hcc_codes=["HCC 226"],
        meat_elements={
            "monitor": True,
            "evaluate": False,
            "assess": False,
            "treat": False,
        },
    )

    print(f"\nFound {len(violations)} violations:")
    for v in violations:
        print(f"   {v['rule_name']}: Missing {', '.join(v['missing_elements'])}")
