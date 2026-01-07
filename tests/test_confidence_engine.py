#!/usr/bin/env python3
"""
Unit Tests for Confidence Engine - Production V1.0
===================================================
Comprehensive test suite for confidence scoring and blocking rules.

Target: >95% code coverage

Test Categories:
1. Mapping confidence calculation
2. Aggregation confidence calculation
3. Recovery confidence calculation
4. Formula complexity factors
5. Confidence propagation
6. Blocking rules (DCF, LBO, Comps)
7. Confidence reporting
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.confidence_engine import (
    calculate_mapping_confidence,
    calculate_aggregation_confidence,
    calculate_recovery_confidence,
    get_formula_complexity_factor,
    infer_formula_type,
    propagate_confidence,
    check_blocking_rules,
    generate_confidence_report,
    generate_confidence_breakdown,
    ModelOutput,
    FormulaType,
)
from utils.lineage_graph import MappingSource, AggregationStrategy


class TestMappingConfidence(unittest.TestCase):
    """Test mapping confidence calculations."""

    def test_analyst_brain_mapping(self):
        """Analyst brain mapping should return 1.00 confidence."""
        conf, expl = calculate_mapping_confidence(
            "Analyst Brain", MappingSource.ANALYST_BRAIN, 0
        )
        self.assertEqual(conf, 1.00)
        self.assertIn("highest trust", expl.lower())

    def test_alias_mapping(self):
        """Alias mapping should return 0.95 confidence."""
        conf, expl = calculate_mapping_confidence(
            "Explicit Alias", MappingSource.ALIAS, 0
        )
        self.assertEqual(conf, 0.95)
        self.assertIn("manually curated", expl.lower())

    def test_exact_label_mapping(self):
        """Exact label match should return 0.90 confidence."""
        conf, expl = calculate_mapping_confidence(
            "Exact Label Match", MappingSource.EXACT_LABEL, 0
        )
        self.assertEqual(conf, 0.90)
        self.assertIn("xbrl taxonomy", expl.lower())

    def test_keyword_mapping(self):
        """Keyword match should return 0.70 confidence."""
        conf, expl = calculate_mapping_confidence(
            "Keyword Match", MappingSource.KEYWORD, 0
        )
        self.assertEqual(conf, 0.70)
        self.assertIn("fuzzy", expl.lower())

    def test_hierarchy_mapping_depth_1(self):
        """Hierarchy fallback depth=1 should return 0.65 confidence."""
        conf, expl = calculate_mapping_confidence(
            "Safe Parent Fallback (depth=1)", MappingSource.HIERARCHY, 1
        )
        self.assertAlmostEqual(conf, 0.65, places=2)
        self.assertIn("depth=1", expl)

    def test_hierarchy_mapping_depth_3(self):
        """Hierarchy fallback depth=3 should return 0.55 confidence."""
        conf, expl = calculate_mapping_confidence(
            "Safe Parent Fallback (depth=3)", MappingSource.HIERARCHY, 3
        )
        self.assertAlmostEqual(conf, 0.55, places=2)
        self.assertIn("depth=3", expl)

    def test_hierarchy_mapping_max_depth(self):
        """Hierarchy fallback should cap at 0.50 minimum."""
        conf, expl = calculate_mapping_confidence(
            "Safe Parent Fallback (depth=10)", MappingSource.HIERARCHY, 10
        )
        self.assertEqual(conf, 0.50)  # Capped at minimum

    def test_unmapped(self):
        """Unmapped should return 0.00 confidence."""
        conf, expl = calculate_mapping_confidence(
            "Unmapped", MappingSource.UNMAPPED, 0
        )
        self.assertEqual(conf, 0.00)
        self.assertIn("failed", expl.lower())

    def test_string_parsing_fallback(self):
        """Should parse method string when MappingSource not provided."""
        conf, expl = calculate_mapping_confidence("analyst brain mapping", None, 0)
        self.assertEqual(conf, 1.00)

        conf, expl = calculate_mapping_confidence("keyword match revenue", None, 0)
        self.assertEqual(conf, 0.70)


class TestAggregationConfidence(unittest.TestCase):
    """Test aggregation confidence calculations."""

    def test_total_line_used(self):
        """Total line used should return 0.95 confidence."""
        conf, expl = calculate_aggregation_confidence(
            AggregationStrategy.TOTAL_LINE_USED, has_conflicts=False
        )
        self.assertEqual(conf, 0.95)
        self.assertIn("explicit total", expl.lower())

    def test_component_sum(self):
        """Component sum should return 0.85 confidence."""
        conf, expl = calculate_aggregation_confidence(
            AggregationStrategy.COMPONENT_SUM, has_conflicts=False
        )
        self.assertEqual(conf, 0.85)
        self.assertIn("double-counting prevented", expl.lower())

    def test_single_value(self):
        """Single value should return 0.90 confidence."""
        conf, expl = calculate_aggregation_confidence(
            AggregationStrategy.SINGLE_VALUE, has_conflicts=False
        )
        self.assertEqual(conf, 0.90)
        self.assertIn("no aggregation ambiguity", expl.lower())

    def test_max_value(self):
        """Max value should return 0.60 confidence."""
        conf, expl = calculate_aggregation_confidence(
            AggregationStrategy.MAX_VALUE, has_conflicts=False
        )
        self.assertEqual(conf, 0.60)
        self.assertIn("ambiguous", expl.lower())

    def test_conflicts_penalty(self):
        """Conflicts should reduce confidence by 0.20."""
        conf_no_conflicts, _ = calculate_aggregation_confidence(
            AggregationStrategy.COMPONENT_SUM, has_conflicts=False
        )
        conf_with_conflicts, expl = calculate_aggregation_confidence(
            AggregationStrategy.COMPONENT_SUM, has_conflicts=True
        )
        self.assertEqual(conf_with_conflicts, conf_no_conflicts - 0.20)
        self.assertIn("double-counting", expl.lower())


class TestRecoveryConfidence(unittest.TestCase):
    """Test recovery confidence calculations."""

    def test_attempt_1_strict(self):
        """Attempt 1 (strict) should return 0.95 confidence."""
        conf, expl = calculate_recovery_confidence(1)
        self.assertEqual(conf, 0.95)
        self.assertIn("strict", expl.lower())

    def test_attempt_2_relaxed(self):
        """Attempt 2 (relaxed) should return 0.70 confidence."""
        conf, expl = calculate_recovery_confidence(2)
        self.assertEqual(conf, 0.70)
        self.assertIn("relaxed", expl.lower())

    def test_attempt_3_desperate(self):
        """Attempt 3 (desperate) should return 0.40 confidence."""
        conf, expl = calculate_recovery_confidence(3)
        self.assertEqual(conf, 0.40)
        self.assertIn("desperate", expl.lower())

    def test_failed_recovery(self):
        """Failed recovery (0 or >3) should return 0.00 confidence."""
        conf, expl = calculate_recovery_confidence(0)
        self.assertEqual(conf, 0.00)

        conf, expl = calculate_recovery_confidence(4)
        self.assertEqual(conf, 0.00)


class TestFormulaComplexity(unittest.TestCase):
    """Test formula complexity factors."""

    def test_simple_arithmetic(self):
        """Simple arithmetic should have 1.00 factor."""
        factor, expl = get_formula_complexity_factor(FormulaType.SIMPLE_ARITHMETIC)
        self.assertEqual(factor, 1.00)
        self.assertIn("no degradation", expl.lower())

    def test_multiplication(self):
        """Multiplication should have 0.98 factor."""
        factor, expl = get_formula_complexity_factor(FormulaType.MULTIPLICATION)
        self.assertEqual(factor, 0.98)

    def test_growth_rate(self):
        """Growth rate should have 0.95 factor."""
        factor, expl = get_formula_complexity_factor(FormulaType.GROWTH_RATE)
        self.assertEqual(factor, 0.95)

    def test_wacc(self):
        """WACC should have 0.90 factor."""
        factor, expl = get_formula_complexity_factor(FormulaType.WACC)
        self.assertEqual(factor, 0.90)

    def test_terminal_value(self):
        """Terminal value should have 0.85 factor."""
        factor, expl = get_formula_complexity_factor(FormulaType.TERMINAL_VALUE)
        self.assertEqual(factor, 0.85)

    def test_irr(self):
        """IRR should have 0.80 factor."""
        factor, expl = get_formula_complexity_factor(FormulaType.IRR)
        self.assertEqual(factor, 0.80)

    def test_infer_formula_type(self):
        """Test formula type inference from strings."""
        self.assertEqual(infer_formula_type("A + B"), FormulaType.SIMPLE_ARITHMETIC)
        self.assertEqual(infer_formula_type("A * B"), FormulaType.MULTIPLICATION)
        self.assertEqual(infer_formula_type("growth rate"), FormulaType.GROWTH_RATE)
        self.assertEqual(infer_formula_type("WACC = ..."), FormulaType.WACC)
        self.assertEqual(infer_formula_type("terminal value"), FormulaType.TERMINAL_VALUE)
        self.assertEqual(infer_formula_type("IRR calculation"), FormulaType.IRR)


class TestConfidencePropagation(unittest.TestCase):
    """Test confidence propagation logic."""

    def test_simple_propagation(self):
        """Test basic confidence propagation."""
        sources = [0.90, 0.85]
        transform = 0.95
        conf, expl = propagate_confidence(sources, transform)
        # Expected: min(0.90, 0.85) * 0.95 = 0.85 * 0.95 = 0.8075
        self.assertAlmostEqual(conf, 0.8075, places=4)
        self.assertIn("MIN", expl)

    def test_single_source(self):
        """Test propagation with single source."""
        sources = [0.80]
        transform = 0.90
        conf, expl = propagate_confidence(sources, transform)
        self.assertAlmostEqual(conf, 0.72, places=2)

    def test_empty_sources(self):
        """Test propagation with no sources."""
        conf, expl = propagate_confidence([], 0.90)
        self.assertEqual(conf, 0.00)
        self.assertIn("no source", expl.lower())

    def test_with_formula_complexity(self):
        """Test propagation with formula complexity factor."""
        sources = [0.90]
        transform = 0.95
        formula = "WACC = ..."
        conf, expl = propagate_confidence(sources, transform, formula)
        # Expected: 0.90 * 0.95 * 0.90 (WACC factor) = 0.7695
        self.assertAlmostEqual(conf, 0.7695, places=4)
        self.assertIn("complexity", expl.lower())

    def test_confidence_floor(self):
        """Test that confidence never goes below 0.00."""
        sources = [0.01]
        transform = 0.01
        conf, _ = propagate_confidence(sources, transform)
        self.assertGreaterEqual(conf, 0.00)

    def test_confidence_cap(self):
        """Test that confidence never exceeds minimum source."""
        sources = [0.80, 0.90]
        transform = 2.0  # Artificially high
        conf, _ = propagate_confidence(sources, transform)
        self.assertLessEqual(conf, min(sources))


class TestBlockingRules(unittest.TestCase):
    """Test blocking rule enforcement."""

    def test_dcf_pass(self):
        """Test DCF model passes with good confidence."""
        critical_inputs = {
            "Revenue": 0.85,
            "EBITDA": 0.80,
            "Net Income": 0.75,
            "WACC": 0.85,
        }
        status, blocks, warns = check_blocking_rules("DCF", critical_inputs)
        self.assertEqual(status, "PASS")
        self.assertEqual(len(blocks), 0)
        self.assertEqual(len(warns), 0)

    def test_dcf_warning(self):
        """Test DCF model generates warnings with medium confidence."""
        critical_inputs = {
            "Revenue": 0.70,  # Warning range: 0.60-0.75
            "EBITDA": 0.65,
            "Net Income": 0.55,
            "WACC": 0.75,
        }
        status, blocks, warns = check_blocking_rules("DCF", critical_inputs)
        self.assertEqual(status, "WARNING")
        self.assertEqual(len(blocks), 0)
        self.assertGreater(len(warns), 0)

    def test_dcf_blocked(self):
        """Test DCF model blocked with low confidence."""
        critical_inputs = {
            "Revenue": 0.50,  # Below 0.60 threshold
            "EBITDA": 0.80,
            "Net Income": 0.75,
            "WACC": 0.85,
        }
        status, blocks, warns = check_blocking_rules("DCF", critical_inputs)
        self.assertEqual(status, "BLOCKED")
        self.assertGreater(len(blocks), 0)
        self.assertIn("Revenue", blocks[0])

    def test_dcf_zero_confidence_blocked(self):
        """Test DCF model blocked with zero confidence (missing data)."""
        critical_inputs = {
            "Revenue": 0.00,  # Missing data
            "EBITDA": 0.80,
            "Net Income": 0.75,
            "WACC": 0.85,
        }
        status, blocks, warns = check_blocking_rules("DCF", critical_inputs)
        self.assertEqual(status, "BLOCKED")
        self.assertGreater(len(blocks), 0)
        self.assertIn("zero confidence", blocks[0].lower())

    def test_lbo_pass(self):
        """Test LBO model passes with good confidence."""
        critical_inputs = {
            "EBITDA": 0.80,
            "Debt": 0.85,
            "Interest Expense": 0.80,
            "IRR": 0.70,
        }
        status, blocks, warns = check_blocking_rules("LBO", critical_inputs)
        self.assertEqual(status, "PASS")

    def test_lbo_irr_warning(self):
        """Test LBO model warns with low IRR confidence."""
        critical_inputs = {
            "EBITDA": 0.80,
            "Debt": 0.85,
            "Interest Expense": 0.80,
            "IRR": 0.55,  # Warning range: 0.50-0.65
        }
        status, blocks, warns = check_blocking_rules("LBO", critical_inputs)
        self.assertEqual(status, "WARNING")
        self.assertIn("IRR", str(warns))

    def test_comps_pass(self):
        """Test Comps model passes with good confidence."""
        critical_inputs = {
            "Revenue": 0.85,
            "EBITDA": 0.80,
            "Market Cap": 0.90,
            "Enterprise Value": 0.85,
        }
        status, blocks, warns = check_blocking_rules("COMPS", critical_inputs)
        self.assertEqual(status, "PASS")

    def test_comps_market_cap_blocked(self):
        """Test Comps model blocked with low market cap confidence."""
        critical_inputs = {
            "Revenue": 0.85,
            "EBITDA": 0.80,
            "Market Cap": 0.70,  # Below 0.80 threshold
            "Enterprise Value": 0.85,
        }
        status, blocks, warns = check_blocking_rules("COMPS", critical_inputs)
        self.assertEqual(status, "BLOCKED")
        self.assertIn("Market Cap", blocks[0])

    def test_unknown_model_type(self):
        """Test unknown model type returns blocked."""
        status, blocks, warns = check_blocking_rules("UNKNOWN", {})
        self.assertEqual(status, "BLOCKED")
        self.assertIn("Unknown model type", blocks[0])


class TestConfidenceReporting(unittest.TestCase):
    """Test confidence reporting functions."""

    def test_generate_confidence_report_pass(self):
        """Test generating report for passing model."""
        model = ModelOutput(
            model_type="DCF",
            overall_confidence=0.82,
            critical_inputs={"Revenue": 0.85, "EBITDA": 0.80},
            blocking_status="PASS",
            blocking_reasons=[],
            warning_reasons=[],
        )
        report = generate_confidence_report(model)
        self.assertIn("DCF", report)
        self.assertIn("PASS", report)
        self.assertIn("✓", report)
        self.assertIn("0.82", report)

    def test_generate_confidence_report_warning(self):
        """Test generating report with warnings."""
        model = ModelOutput(
            model_type="LBO",
            overall_confidence=0.65,
            critical_inputs={"EBITDA": 0.70, "IRR": 0.60},
            blocking_status="WARNING",
            blocking_reasons=[],
            warning_reasons=["IRR confidence below recommended threshold"],
        )
        report = generate_confidence_report(model)
        self.assertIn("WARNING", report)
        self.assertIn("⚠", report)
        self.assertIn("IRR", report)

    def test_generate_confidence_report_blocked(self):
        """Test generating report for blocked model."""
        model = ModelOutput(
            model_type="COMPS",
            overall_confidence=0.45,
            critical_inputs={"Revenue": 0.50, "EBITDA": 0.45},
            blocking_status="BLOCKED",
            blocking_reasons=["Revenue confidence below minimum threshold"],
            warning_reasons=[],
        )
        report = generate_confidence_report(model)
        self.assertIn("BLOCKED", report)
        self.assertIn("✗", report)
        self.assertIn("Revenue", report)
        self.assertIn("ACTION REQUIRED", report)

    def test_generate_confidence_breakdown(self):
        """Test generating detailed confidence breakdown."""
        components = {
            "mapping": 0.90,
            "aggregation": 0.85,
        }
        breakdown = generate_confidence_breakdown(1000.0, 0.765, components)
        self.assertIn("1000", breakdown)
        self.assertIn("0.765", breakdown)
        self.assertIn("mapping", breakdown)
        self.assertIn("0.90", breakdown)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def test_none_values_in_propagation(self):
        """Test handling of None values in propagation."""
        sources = [0.90, None, 0.85]
        conf, _ = propagate_confidence(sources, 0.95)
        # Should filter out None and use remaining values
        self.assertAlmostEqual(conf, 0.85 * 0.95, places=2)

    def test_all_none_sources(self):
        """Test propagation with all None sources."""
        sources = [None, None]
        conf, expl = propagate_confidence(sources, 0.95)
        self.assertEqual(conf, 0.00)
        self.assertIn("no valid", expl.lower())

    def test_negative_confidence(self):
        """Test that negative confidence doesn't occur."""
        # Test with penalty that would go negative
        conf, _ = calculate_aggregation_confidence(
            AggregationStrategy.MAX_VALUE, has_conflicts=True
        )
        # 0.60 - 0.20 = 0.40, should not go negative
        self.assertGreaterEqual(conf, 0.00)

    def test_very_low_transform_confidence(self):
        """Test propagation with very low transformation confidence."""
        sources = [0.95]
        transform = 0.01
        conf, _ = propagate_confidence(sources, transform)
        self.assertAlmostEqual(conf, 0.0095, places=4)


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
