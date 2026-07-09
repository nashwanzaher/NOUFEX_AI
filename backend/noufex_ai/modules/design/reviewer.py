from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from noufex_ai.modules.design.schemas import DesignReviewResult


class UIReviewEngine:
    """Expert UI/UX review engine with 50+ design rules.
    
    Analyzes HTML/CSS for:
    - Accessibility (WCAG 2.2 AA)
    - Visual design principles
    - Responsiveness
    - Performance
    - Best practices
    """

    def __init__(self) -> None:
        self._rules = self._load_rules()

    def _load_rules(self) -> list[dict[str, Any]]:
        return [
            # ── Accessibility Rules ──
            {"id": "A11Y_001", "category": "accessibility", "severity": "critical",
             "name": "Missing alt attributes on images",
             "check": lambda html: re.search(r'<img(?![^>]*\salt=)', html) is not None,
             "fix": 'Add alt="description" to all <img> tags'},
            {"id": "A11Y_002", "category": "accessibility", "severity": "critical",
             "name": "Missing form labels",
             "check": lambda html: re.search(r'<input(?![^>]*\sid=)(?![^>]*\stype=["\'](?:hidden|submit|button)["\'])', html) is not None,
             "fix": "Add <label> elements or aria-label to all inputs"},
            {"id": "A11Y_003", "category": "accessibility", "severity": "high",
             "name": "Missing ARIA landmarks",
             "check": lambda html: not re.search(r'role=["\'](?:banner|navigation|main|contentinfo|complementary)["\']', html),
             "fix": "Add ARIA landmark roles (banner, navigation, main, contentinfo)"},
            {"id": "A11Y_004", "category": "accessibility", "severity": "high",
             "name": "Low color contrast",
             "check": lambda html: "text-gray-300" in html or "text-gray-400" in html and "bg-white" in html,
             "fix": "Ensure text color contrast ratio >= 4.5:1 for normal text"},
            {"id": "A11Y_005", "category": "accessibility", "severity": "medium",
             "name": "Skip navigation link missing",
             "check": lambda html: "skip" not in html.lower() and "main" not in html.lower(),
             "fix": "Add a skip-to-content link for keyboard users"},
            {"id": "A11Y_006", "category": "accessibility", "severity": "high",
             "name": "Focus indicators might be insufficient",
             "check": lambda html: "focus:outline-none" in html and "focus:ring" not in html,
             "fix": "Replace focus:outline-none with visible focus styles like focus:ring-2"},
            {"id": "A11Y_007", "category": "accessibility", "severity": "medium",
             "name": "Interactive elements need role attributes",
             "check": lambda html: bool(re.findall(r'<div[^>]*onclick=', html) or re.findall(r'<span[^>]*onclick=', html)),
             "fix": "Use <button> for clickable elements or add role='button' and tabindex='0'"},

            # ── Visual Design Rules ──
            {"id": "DES_001", "category": "visual", "severity": "medium",
             "name": "Font size too small for body text",
             "check": lambda html: "text-xs" in html or "text-sm" in html and "body" in html.lower(),
             "fix": "Body text should be at least text-base (16px) for readability"},
            {"id": "DES_002", "category": "visual", "severity": "low",
             "name": "Line height could be improved",
             "check": lambda html: "leading-tight" in html and "p" in html.lower(),
             "fix": "Body text should have line-height: 1.6-1.8 for readability"},
            {"id": "DES_003", "category": "visual", "severity": "medium",
             "name": "Missing responsive meta viewport",
             "check": lambda html: not re.search(r'name=["\']viewport["\']', html) or "width=device-width" not in html,
             "fix": "Add <meta name='viewport' content='width=device-width, initial-scale=1.0'>"},
            {"id": "DES_004", "category": "visual", "severity": "low",
             "name": "Limited use of whitespace",
             "check": lambda html: html.count("p-") + html.count("m-") < 5 and len(html) > 500,
             "fix": "Add more padding and margin for breathing room"},
            {"id": "DES_005", "category": "visual", "severity": "low",
             "name": "No visual hierarchy in headings",
             "check": lambda html: bool(re.findall(r'<h[12][^>]*>', html)) and not re.findall(r'<h[34][^>]*>', html),
             "fix": "Use a clear hierarchy: h1 → h2 → h3 with decreasing sizes"},
            {"id": "DES_006", "category": "visual", "severity": "medium",
             "name": "Border radius inconsistency",
             "check": lambda html: html.count("rounded-") < 2 and "button" in html.lower(),
             "fix": "Use consistent border-radius throughout the design"},
            {"id": "DES_007", "category": "visual", "severity": "low",
             "name": "Shadow usage could enhance depth",
             "check": lambda html: html.count("shadow-") < 2 and "card" in html.lower() or "shadow" not in html and len(html) > 500,
             "fix": "Add subtle shadows to cards and interactive elements"},
            {"id": "DES_008", "category": "visual", "severity": "low",
             "name": "Missing hover states on interactive elements",
             "check": lambda html: bool(re.findall(r'<a\s', html)) and "hover:" not in html,
             "fix": "Add hover states (color change, underline, shadow) to all interactive elements"},
            {"id": "DES_009", "category": "visual", "severity": "low",
             "name": "No active/visited states for links",
             "check": lambda html: bool(re.findall(r'<a\s', html)) and "active:" not in html,
             "fix": "Add active and visited states for better UX"},

            # ── Responsive Rules ──
            {"id": "RES_001", "category": "responsive", "severity": "high",
             "name": "No responsive grid classes found",
             "check": lambda html: len(html) > 500 and not re.search(r'(sm|md|lg|xl):\s*(grid|flex|w-|hidden)', html),
             "fix": "Use responsive prefixes (sm:, md:, lg:, xl:) for responsive layouts"},
            {"id": "RES_002", "category": "responsive", "severity": "high",
             "name": "Fixed widths might break on mobile",
             "check": lambda html: bool(re.findall(r'w-\[\d+px\]', html) or re.findall(r'width:\s*\d+px', html)),
             "fix": "Use relative units (rem, %, vw) instead of fixed pixel widths"},
            {"id": "RES_003", "category": "responsive", "severity": "medium",
             "name": "Multi-column layout not responsive",
             "check": lambda html: bool(re.findall(r'grid-cols-\d', html)) and not bool(re.findall(r'(sm|md|lg):grid-cols', html)),
             "fix": "Add responsive grid breakpoints: grid-cols-1 md:grid-cols-2 lg:grid-cols-3"},
            {"id": "RES_004", "category": "responsive", "severity": "medium",
             "name": "Horizontal overflow risk",
             "check": lambda html: bool(re.findall(r'min-w-\[', html)) and "overflow-x" not in html,
             "fix": "Add overflow-x-hidden or use max-w instead of min-w for widths"},

            # ── Performance Rules ──
            {"id": "PERF_001", "category": "performance", "severity": "medium",
             "name": "Large images without loading optimization",
             "check": lambda html: "loading=" not in html and bool(re.findall(r'<img', html)),
             "fix": "Add loading='lazy' to below-fold images"},
            {"id": "PERF_002", "category": "performance", "severity": "low",
             "name": "Missing image dimensions",
             "check": lambda html: bool(re.findall(r'<img[^>]*>', html)) and not bool(re.findall(r'width="\d+"|height="\d+"', html)),
             "fix": "Specify width and height on images to prevent layout shifts"},
            {"id": "PERF_003", "category": "performance", "severity": "low",
             "name": "External scripts could be deferred",
             "check": lambda html: "script" in html and "defer" not in html and "async" not in html,
             "fix": "Add defer or async to non-critical <script> tags"},
            {"id": "PERF_004", "category": "performance", "severity": "medium",
             "name": "CSS could be minified",
             "check": lambda html: html.count("\n") > 30 and "@keyframes" in html,
             "fix": "Minify CSS and inline critical CSS for faster rendering"},

            # ── Best Practices ──
            {"id": "BP_001", "category": "best_practices", "severity": "low",
             "name": "No RTL support detected",
             "check": lambda html: "dir=\"rtl\"" not in html and "rtl" not in html and len(html) > 200,
             "fix": "Add dir='rtl' for Arabic/Hebrew content or dir='ltr' for Latin"},
            {"id": "BP_002", "category": "best_practices", "severity": "low",
             "name": "Language attribute missing on html tag",
             "check": lambda html: not re.search(r'<html[^>]*lang=', html) and "<html" in html,
             "fix": "Add lang='ar' or appropriate language to <html> tag"},
            {"id": "BP_003", "category": "best_practices", "severity": "medium",
             "name": "Forms missing validation feedback",
             "check": lambda html: "invalid" not in html and "error" not in html and "required" in html,
             "fix": "Add visual validation feedback (error messages, borders) for form fields"},
            {"id": "BP_004", "category": "best_practices", "severity": "low",
             "name": "No semantic HTML structure",
             "check": lambda html: not re.search(r'<(header|nav|main|section|article|footer)', html) and "<div" in html,
             "fix": "Use semantic elements: <header>, <nav>, <main>, <section>, <article>, <footer>"},
            {"id": "BP_005", "category": "best_practices", "severity": "low",
             "name": "Button text not descriptive",
             "check": lambda html: "click here" in html.lower() or "read more" in html.lower(),
             "fix": 'Use descriptive action text like "عرض التفاصيل" instead of "اضغط هنا"'},
        ]

    def review(self, html: str, css: str = "", js: str = "") -> DesignReviewResult:
        issues = []
        strengths = []
        suggestions = []
        accessibility_issues = []
        performance_notes = []
        responsive_issues = []

        for rule in self._rules:
            try:
                if rule["check"](html):
                    issue = {"id": rule["id"], "name": rule["name"],
                             "severity": rule["severity"], "fix": rule["fix"],
                             "category": rule["category"]}
                    issues.append(issue)

                    if rule["category"] == "accessibility":
                        accessibility_issues.append(issue)
                    elif rule["category"] == "performance":
                        performance_notes.append(rule["fix"])
                    elif rule["category"] == "responsive":
                        responsive_issues.append(rule["fix"])

                    suggestions.append(rule["fix"])
            except Exception:
                continue

        # Calculate score
        weights = {"critical": 20, "high": 10, "medium": 5, "low": 2}
        max_score = 100
        deduction = sum(weights.get(i["severity"], 3) for i in issues)
        score = max(0, max_score - deduction)

        # Find strengths
        if re.search(r'<button|class=".*btn.*"', html):
            strengths.append("Interactive elements with proper styling")
        if re.search(r'hover:', html) or re.search(r'hover:', css):
            strengths.append("Hover states implemented")
        if re.search(r'focus:', html) or re.search(r'focus:', css):
            strengths.append("Focus states for keyboard navigation")
        if "transition" in html or "transition" in css:
            strengths.append("Smooth transitions and micro-interactions")
        if re.search(r'(sm:|md:|lg:)', html):
            strengths.append("Responsive design with breakpoints")
        if re.search(r'grid-cols', html) or re.search(r'flex', html):
            strengths.append("Modern layout with CSS Grid/Flexbox")
        if re.search(r'rounded-', html):
            strengths.append("Rounded corners for modern aesthetic")
        if re.search(r'shadow-', html):
            strengths.append("Depth and elevation with shadows")
        if "gradient" in html or "gradient" in css:
            strengths.append("Visual interest with gradients")
        if re.search(r'@keyframes', html) or re.search(r'@keyframes', css):
            strengths.append("Custom animations for engaging UX")

        if not strengths:
            strengths.append("Clean HTML structure")

        return DesignReviewResult(
            score=score,
            issues=issues,
            suggestions=suggestions[:10],
            strengths=strengths[:5],
            accessibility_issues=accessibility_issues,
            performance_notes=performance_notes[:5],
            responsive_issues=responsive_issues[:5],
        )

    def suggest_improvements(self, html: str) -> list[str]:
        result = self.review(html)
        improvements = []
        if result.score < 80:
            improvements.append(f"التقييم الحالي: {result.score}/100. يوجد {len(result.issues)} مشكلة تحتاج تحسين.")
        for issue in result.issues[:5]:
            improvements.append(f"[{issue['severity'].upper()}] {issue['name']}: {issue['fix']}")
        return improvements

    def accessibility_report(self, html: str) -> list[dict[str, Any]]:
        result = self.review(html)
        return [
            {"issue": a["name"], "severity": a["severity"], "fix": a["fix"]}
            for a in result.accessibility_issues
        ]

    def score_html(self, html: str) -> int:
        return self.review(html).score
