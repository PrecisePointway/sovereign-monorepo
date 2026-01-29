#!/usr/bin/env python3
"""
UNSAFE LANGUAGE LINT SPEC
Developer tool for detecting manipulation patterns in system output.

Usage:
    python unsafe_language_lint.py <file_or_directory>
    python unsafe_language_lint.py --check "text to check"

Part of S.A.F.E.-OS (Sovereign, Assistive, Fail-closed Environment)
"""

import re
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class LintViolation:
    """A lint violation found in source."""
    file: str
    line: int
    column: int
    rule: str
    severity: str
    message: str
    suggestion: str

# =============================================================================
# LINT RULES
# =============================================================================

LINT_RULES = {
    # Hard bans - ERROR level
    "LSG001": {
        "name": "shared-agency",
        "severity": "error",
        "patterns": [r"\bwe\b", r"\bus\b", r"\btogether\b", r"\bour\s+goal\b", r"\blet's\b"],
        "message": "Shared agency language detected",
        "suggestion": "Replace with 'the system' or 'this tool'",
    },
    "LSG002": {
        "name": "relational-bonding",
        "severity": "error",
        "patterns": [
            r"\bi'm\s+here\s+for\s+you\b",
            r"\byou're\s+not\s+alone\b",
            r"\bi\s+care\s+about\b",
            r"\bwe've\s+got\s+this\b",
        ],
        "message": "Relational bonding language detected",
        "suggestion": "Remove emotional bonding phrases entirely",
    },
    "LSG003": {
        "name": "authority-alignment",
        "severity": "error",
        "patterns": [
            r"\btrust\s+me\b",
            r"\byou\s+can\s+rely\s+on\b",
            r"\brest\s+assured\b",
        ],
        "message": "Authority alignment language detected",
        "suggestion": "Remove trust-building phrases; state facts only",
    },
    "LSG004": {
        "name": "motivational-steering",
        "severity": "error",
        "patterns": [
            r"\byou\s+should\b",
            r"\bit's\s+best\s+to\b",
            r"\bthe\s+right\s+choice\s+is\b",
            r"\byou'll\s+feel\s+better\s+if\b",
        ],
        "message": "Motivational steering language detected",
        "suggestion": "Replace with 'one option is' or 'alternatives include'",
    },
    
    # Soft manipulation - WARNING level
    "LSG005": {
        "name": "consensus-framing",
        "severity": "warning",
        "patterns": [
            r"\bmost\s+people\s+find\b",
            r"\bresearch\s+suggests\s+you\s+should\b",
            r"\bit's\s+generally\s+accepted\b",
            r"\beveryone\s+knows\b",
        ],
        "message": "Consensus framing detected",
        "suggestion": "Replace with 'some sources state X, others state Y' or 'evidence is mixed'",
    },
    "LSG006": {
        "name": "emotional-mirroring",
        "severity": "warning",
        "patterns": [
            r"\bthat\s+sounds\s+really\s+hard\b",
            r"\bi\s+can\s+hear\s+how\s+painful\b",
            r"\byour\s+feelings\s+make\s+sense\b",
        ],
        "message": "Emotional mirroring detected",
        "suggestion": "Replace with 'Human support is more appropriate here' or boundary statement",
    },
    "LSG007": {
        "name": "implied-partnership",
        "severity": "warning",
        "patterns": [
            r"\balongside\s+you\b",
            r"\bwith\s+you\b",
            r"\bby\s+your\s+side\b",
        ],
        "message": "Implied partnership language detected",
        "suggestion": "Remove partnership implications; use procedural language",
    },
    "LSG008": {
        "name": "guidance-masking",
        "severity": "warning",
        "patterns": [
            r"\bhelpful\s+to\s+consider\b",
            r"\bworth\s+thinking\s+about\b",
            r"\byou\s+might\s+want\s+to\b",
        ],
        "message": "Guidance masking detected",
        "suggestion": "State information directly without soft steering",
    },
    
    # Info level - best practices
    "LSG009": {
        "name": "emotional-proxy",
        "severity": "info",
        "patterns": [
            r"\bi\s+feel\b",
            r"\bit\s+feels\s+like\b",
        ],
        "message": "Emotional proxy language detected",
        "suggestion": "Systems do not feel; use factual statements",
    },
    "LSG010": {
        "name": "missing-uncertainty",
        "severity": "info",
        "patterns": [],  # Special handling
        "message": "Long confident statement without uncertainty markers",
        "suggestion": "Add uncertainty markers: 'may', 'possibly', 'evidence is mixed', 'UNKNOWN'",
    },
}


class UnsafeLanguageLinter:
    """Lint tool for detecting unsafe language patterns."""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.violations: List[LintViolation] = []
        
        # Compile patterns
        self.compiled_rules = {}
        for rule_id, rule in LINT_RULES.items():
            if rule["patterns"]:
                self.compiled_rules[rule_id] = {
                    **rule,
                    "compiled": [re.compile(p, re.IGNORECASE) for p in rule["patterns"]]
                }
    
    def lint_text(self, text: str, filename: str = "<string>") -> List[LintViolation]:
        """Lint a text string."""
        violations = []
        lines = text.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for rule_id, rule in self.compiled_rules.items():
                for pattern in rule["compiled"]:
                    for match in pattern.finditer(line):
                        violations.append(LintViolation(
                            file=filename,
                            line=line_num,
                            column=match.start() + 1,
                            rule=rule_id,
                            severity=rule["severity"],
                            message=rule["message"],
                            suggestion=rule["suggestion"],
                        ))
        
        # Check for fluency-as-authority (LSG010)
        violations.extend(self._check_fluency_authority(text, filename))
        
        self.violations.extend(violations)
        return violations
    
    def lint_file(self, filepath: Path) -> List[LintViolation]:
        """Lint a file."""
        try:
            text = filepath.read_text()
            return self.lint_text(text, str(filepath))
        except Exception as e:
            return [LintViolation(
                file=str(filepath),
                line=0,
                column=0,
                rule="LSG000",
                severity="error",
                message=f"Failed to read file: {e}",
                suggestion="Check file permissions and encoding",
            )]
    
    def lint_directory(self, dirpath: Path, extensions: List[str] = None) -> List[LintViolation]:
        """Lint all files in a directory."""
        extensions = extensions or [".py", ".md", ".txt", ".html", ".json"]
        violations = []
        
        for ext in extensions:
            for filepath in dirpath.rglob(f"*{ext}"):
                violations.extend(self.lint_file(filepath))
        
        return violations
    
    def _check_fluency_authority(self, text: str, filename: str) -> List[LintViolation]:
        """Check for fluency-as-authority pattern."""
        violations = []
        uncertainty_markers = [
            r"\bunknown\b", r"\buncertain\b", r"\bmay\b", r"\bmight\b",
            r"\bpossibly\b", r"\bperhaps\b", r"\bevidence\s+is\s+mixed\b",
        ]
        
        lines = text.split('\n')
        for line_num, line in enumerate(lines, 1):
            # Long line without uncertainty
            if len(line) > 200:
                has_uncertainty = any(
                    re.search(marker, line, re.IGNORECASE)
                    for marker in uncertainty_markers
                )
                if not has_uncertainty:
                    violations.append(LintViolation(
                        file=filename,
                        line=line_num,
                        column=1,
                        rule="LSG010",
                        severity="info",
                        message=LINT_RULES["LSG010"]["message"],
                        suggestion=LINT_RULES["LSG010"]["suggestion"],
                    ))
        
        return violations
    
    def format_output(self, format_type: str = "text") -> str:
        """Format violations for output."""
        if format_type == "json":
            return json.dumps([
                {
                    "file": v.file,
                    "line": v.line,
                    "column": v.column,
                    "rule": v.rule,
                    "severity": v.severity,
                    "message": v.message,
                    "suggestion": v.suggestion,
                }
                for v in self.violations
            ], indent=2)
        
        # Text format
        output = []
        for v in self.violations:
            severity_icon = {"error": "✗", "warning": "⚠", "info": "ℹ"}[v.severity]
            output.append(
                f"{v.file}:{v.line}:{v.column}: {severity_icon} [{v.rule}] {v.message}\n"
                f"  Suggestion: {v.suggestion}"
            )
        
        return "\n\n".join(output)
    
    def get_summary(self) -> Dict:
        """Get violation summary."""
        errors = sum(1 for v in self.violations if v.severity == "error")
        warnings = sum(1 for v in self.violations if v.severity == "warning")
        infos = sum(1 for v in self.violations if v.severity == "info")
        
        return {
            "total": len(self.violations),
            "errors": errors,
            "warnings": warnings,
            "info": infos,
            "passed": errors == 0,
        }


def main():
    parser = argparse.ArgumentParser(
        description="Lint for unsafe language patterns in S.A.F.E.-OS"
    )
    parser.add_argument(
        "target",
        nargs="?",
        help="File or directory to lint"
    )
    parser.add_argument(
        "--check",
        type=str,
        help="Check a text string directly"
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors"
    )
    
    args = parser.parse_args()
    
    linter = UnsafeLanguageLinter()
    
    if args.check:
        linter.lint_text(args.check)
    elif args.target:
        target = Path(args.target)
        if target.is_file():
            linter.lint_file(target)
        elif target.is_dir():
            linter.lint_directory(target)
        else:
            print(f"Error: {target} not found", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(0)
    
    # Output results
    if linter.violations:
        print(linter.format_output(args.format))
        print()
    
    summary = linter.get_summary()
    print(f"Summary: {summary['errors']} errors, {summary['warnings']} warnings, {summary['info']} info")
    
    # Exit code
    if args.strict:
        sys.exit(0 if summary["total"] == 0 else 1)
    else:
        sys.exit(0 if summary["errors"] == 0 else 1)


if __name__ == "__main__":
    main()
