"""
Comprehensive pytest tests for uvm_is_match function.

Tests cover:
- Exact string matching
- Globbing patterns with wildcards (*, ?, +)
- Regular expression patterns (delimited by /)
- Edge cases and special characters
- IEEE UVM standard pattern matching behavior
"""

from pyuvm._utility_classes import uvm_is_match


class TestUVMIsMatchExactMatching:
    """Test exact string matching without wildcards."""

    def test_exact_match_simple_string(self):
        """Test matching an exact simple string."""
        assert uvm_is_match("hello", "hello") is True

    def test_exact_match_with_numbers(self):
        """Test matching strings containing numbers."""
        assert uvm_is_match("test123", "test123") is True

    def test_exact_match_with_underscores(self):
        """Test matching strings with underscores."""
        assert uvm_is_match("test_name", "test_name") is True

    def test_exact_match_with_dots(self):
        """Test matching strings with dots (hierarchy paths)."""
        assert uvm_is_match("top.env.agent", "top.env.agent") is True

    def test_exact_no_match_different_case(self):
        """Test that exact matching is case-sensitive."""
        assert uvm_is_match("Hello", "hello") is False

    def test_exact_no_match_different_string(self):
        """Test non-matching exact strings."""
        assert uvm_is_match("hello", "world") is False

    def test_exact_no_match_substring(self):
        """Test that substring doesn't match."""
        assert uvm_is_match("hello", "hello_world") is False

    def test_exact_empty_strings(self):
        """Test matching empty strings."""
        assert uvm_is_match("", "") is True


class TestUVMIsMatchAsteriskWildcard:
    """Test asterisk (*) wildcard matching (zero or more characters)."""

    def test_asterisk_match_zero_characters(self):
        """Test * matching zero characters."""
        assert uvm_is_match("test*", "test") is True

    def test_asterisk_match_single_character(self):
        """Test * matching single character."""
        assert uvm_is_match("test*", "testa") is True

    def test_asterisk_match_multiple_characters(self):
        """Test * matching multiple characters."""
        assert uvm_is_match("test*", "test_name_here") is True

    def test_asterisk_at_start(self):
        """Test * at start of pattern."""
        assert uvm_is_match("*test", "my_test") is True
        assert uvm_is_match("*test", "test") is True

    def test_asterisk_at_end(self):
        """Test * at end of pattern."""
        assert uvm_is_match("test*", "test_value") is True
        assert uvm_is_match("test*", "test") is True

    def test_asterisk_in_middle(self):
        """Test * in middle of pattern."""
        assert uvm_is_match("test*_name", "test_item_name") is True
        assert uvm_is_match("test*_name", "test__name") is True

    def test_multiple_asterisks(self):
        """Test multiple * wildcards."""
        assert uvm_is_match("*test*", "my_test_name") is True
        assert uvm_is_match("*test*", "test") is True
        assert uvm_is_match("test*_*_end", "test_middle_value_end") is True

    def test_asterisk_no_match_missing_literal(self):
        """Test * doesn't match missing literal characters."""
        assert uvm_is_match("test*_name", "test_name_wrong") is False

    def test_asterisk_matches_dots(self):
        """Test * matches dots in hierarchy."""
        assert uvm_is_match("top.*.*", "top.env.agent") is True
        assert uvm_is_match("*.*.*", "a.b.c") is True

    def test_asterisk_only(self):
        """Test pattern with only *."""
        assert uvm_is_match("*", "anything") is True
        assert uvm_is_match("*", "") is True


class TestUVMIsMatchPlusWildcard:
    """Test plus (+) wildcard matching (one or more characters)."""

    def test_plus_match_single_character(self):
        """Test + matching single character."""
        assert uvm_is_match("test+", "testa") is True

    def test_plus_match_multiple_characters(self):
        """Test + matching multiple characters."""
        assert uvm_is_match("test+", "test_name_here") is True

    def test_plus_no_match_zero_characters(self):
        """Test + not matching zero characters."""
        assert uvm_is_match("test+", "test") is False

    def test_plus_at_start(self):
        """Test + at start of pattern."""
        assert uvm_is_match("+test", "my_test") is True
        assert uvm_is_match("+test", "test") is False

    def test_plus_at_end(self):
        """Test + at end of pattern."""
        assert uvm_is_match("test+", "test_value") is True
        assert uvm_is_match("test+", "test") is False

    def test_plus_in_middle(self):
        """Test + in middle of pattern."""
        assert uvm_is_match("test+_name", "test_item_name") is True
        assert uvm_is_match("test+_name", "test__name") is True

    def test_multiple_plus_wildcards(self):
        """Test multiple + wildcards."""
        assert uvm_is_match("+test+", "my_test_name") is True
        assert uvm_is_match("+test+", "1test2") is True
        assert uvm_is_match("+test+", "test") is False

    def test_plus_no_match_missing_literal(self):
        """Test + doesn't match missing literal characters."""
        assert uvm_is_match("test+_name", "test_name_wrong") is False


class TestUVMIsMatchQuestionMarkWildcard:
    """Test question mark (?) wildcard matching (exactly one character)."""

    def test_question_mark_single_character(self):
        """Test ? matching exactly one character."""
        assert uvm_is_match("test?", "testa") is True
        assert uvm_is_match("test?", "testX") is True

    def test_question_mark_no_match_zero_characters(self):
        """Test ? not matching zero characters."""
        assert uvm_is_match("test?", "test") is False

    def test_question_mark_no_match_multiple_characters(self):
        """Test ? not matching multiple characters."""
        assert uvm_is_match("test?", "test_ab") is False

    def test_question_mark_at_start(self):
        """Test ? at start of pattern."""
        assert uvm_is_match("?test", "atest") is True
        assert uvm_is_match("?test", "test") is False

    def test_question_mark_in_middle(self):
        """Test ? in middle of pattern."""
        assert uvm_is_match("test?name", "testa_name") is False
        assert uvm_is_match("test?name", "testaname") is True

    def test_multiple_question_marks(self):
        """Test multiple ? wildcards."""
        assert uvm_is_match("??test??", "01test45") is True
        assert uvm_is_match("??test??", "test") is False
        assert uvm_is_match("???", "abc") is True

    def test_question_mark_matches_any_character(self):
        """Test ? matches any single character including special."""
        assert uvm_is_match("test?", "test_") is True
        assert uvm_is_match("test?", "test.") is True


class TestUVMIsMatchMixedWildcards:
    """Test combinations of different wildcards."""

    def test_asterisk_and_question_mark(self):
        """Test * and ? together."""
        assert uvm_is_match("test*?", "test_a") is True
        assert uvm_is_match("test*?", "test_multiple_x") is True
        assert uvm_is_match("test*?", "test") is False

    def test_asterisk_and_plus(self):
        """Test * and + together."""
        assert uvm_is_match("test*+", "test_a") is True
        assert uvm_is_match("test*+", "test_multiple") is True
        assert uvm_is_match("test*+", "test") is False

    def test_plus_and_question_mark(self):
        """Test + and ? together."""
        assert uvm_is_match("test+?", "testa_") is True
        assert uvm_is_match("test+?", "testa") is False
        assert uvm_is_match("test+?", "test_a") is True

    def test_all_wildcards_combined(self):
        """Test all wildcards in one pattern."""
        assert uvm_is_match("*test+?*", "my_test_value_end") is True
        assert uvm_is_match("*test+?*", "test_a") is True


class TestUVMIsMatchRegularExpression:
    """Test regular expression patterns (delimited by /)."""

    def test_regex_simple_pattern(self):
        """Test simple regex pattern."""
        assert uvm_is_match("/^test/", "test") is True
        assert uvm_is_match("/test$/", "test") is True

    def test_regex_with_alternation(self):
        """Test regex with alternation."""
        assert uvm_is_match("/^(test|check)$/", "test") is True
        assert uvm_is_match("/^(test|check)$/", "check") is True
        assert uvm_is_match("/^(test|check)$/", "other") is False

    def test_regex_character_class(self):
        """Test regex with character classes."""
        assert uvm_is_match("/[0-9]+/", "123") is True
        assert uvm_is_match("/[a-z]+/", "hello") is True
        assert uvm_is_match("/[A-Z]/", "H") is True

    def test_regex_escaped_special_chars(self):
        """Test regex with escaped special characters."""
        assert uvm_is_match(r"/\d+/", "123") is True
        assert uvm_is_match(r"/\w+/", "word123") is True

    def test_regex_quantifiers(self):
        """Test regex with standard quantifiers."""
        assert uvm_is_match("/test{3}/", "testtt") is True
        assert uvm_is_match("/a{2,4}/", "aaa") is True

    def test_regex_anchors(self):
        """Test regex with anchors."""
        assert uvm_is_match("/^test/", "test_name") is False
        assert uvm_is_match("/test$/", "my_test") is False
        assert uvm_is_match("/^test$/", "test") is True
        assert uvm_is_match("/^test$/", "test_extra") is False

    def test_regex_dot_wildcard(self):
        """Test regex with . wildcard (any character)."""
        assert uvm_is_match("/t.st/", "test") is True
        assert uvm_is_match("/t.st/", "txst") is True
        assert uvm_is_match("/t.st/", "t_st") is True

    def test_regex_no_match(self):
        """Test regex pattern that doesn't match."""
        assert uvm_is_match("/^[0-9]+$/", "abc") is False


class TestUVMIsMatchHierarchyPatterns:
    """Test patterns for UVM component hierarchy matching."""

    def test_hierarchy_exact_path(self):
        """Test exact hierarchy path matching."""
        assert uvm_is_match("top.env.agent", "top.env.agent") is True

    def test_hierarchy_single_level_wildcard(self):
        """Test single level wildcard in hierarchy."""
        assert uvm_is_match("top.*.agent", "top.env.agent") is True
        assert uvm_is_match("top.*.agent", "top.my_env.agent") is True
        assert uvm_is_match("top.*.agent", "top.agent") is False

    def test_hierarchy_multiple_level_wildcard(self):
        """Test multiple level wildcard in hierarchy."""
        assert uvm_is_match("top.*", "top.env.agent") is True
        assert uvm_is_match("top.*", "top.env.agent.driver") is True
        assert uvm_is_match("*agent", "top.env.agent") is True

    def test_hierarchy_question_mark_level(self):
        """Test question mark in single hierarchy component."""
        assert uvm_is_match("top.env?.agent", "top.env1.agent") is True
        assert uvm_is_match("top.env?.agent", "top.envX.agent") is True
        assert uvm_is_match("top.env?.agent", "top.env.agent") is False

    def test_hierarchy_complex_pattern(self):
        """Test complex hierarchy patterns."""
        assert uvm_is_match("*.env.*.driver", "top.env.ahb.driver") is True
        assert uvm_is_match("top.*.*.driver", "top.env.ahb.driver") is True


class TestUVMIsMatchSpecialCharacters:
    """Test handling of special characters."""

    def test_special_chars_in_string(self):
        """Test exact matching with special characters."""
        assert uvm_is_match("test_name", "test_name") is True
        assert uvm_is_match("test-name", "test-name") is True
        assert uvm_is_match("test.name", "test.name") is True

    def test_parentheses_literal(self):
        """Test parentheses as literal characters."""
        assert uvm_is_match("func()", "func()") is True

    def test_brackets_literal(self):
        """Test brackets as literal characters."""
        assert uvm_is_match("array[0]", "array[0]") is True

    def test_asterisk_escaping_in_literal(self):
        """Test that * in pattern is treated as wildcard."""
        assert uvm_is_match("test*", "test") is True
        assert uvm_is_match("test*", "test*") is True  # * matches *

    def test_plus_literal_at_end(self):
        """Test + as wildcard character."""
        assert uvm_is_match("test+", "test_") is True
        assert uvm_is_match("test+", "test+") is True  # + matches itself


class TestUVMIsMatchEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_pattern_empty_string(self):
        """Test empty pattern with empty string."""
        assert uvm_is_match("", "") is True

    def test_empty_pattern_nonempty_string(self):
        """Test empty pattern with non-empty string."""
        assert uvm_is_match("", "anything") is False

    def test_very_long_string(self):
        """Test matching very long strings."""
        long_str = "a" * 1000
        assert uvm_is_match("a*", long_str) is True
        assert uvm_is_match("a+", long_str) is True
        assert uvm_is_match("*", long_str) is True

    def test_many_wildcards(self):
        """Test pattern with many wildcards."""
        assert uvm_is_match("*?*?*?*", "a1b2c3d4") is True

    def test_consecutive_asterisks(self):
        """Test consecutive asterisks in pattern."""
        assert uvm_is_match("**", "") is True
        assert uvm_is_match("**", "anything") is True
        assert uvm_is_match("test**end", "test_middle_end") is True

    def test_consecutive_plus(self):
        """Test consecutive plus in pattern."""
        assert uvm_is_match("test++end", "test__end") is True


class TestUVMIsMatchIEEECompliance:
    """Test IEEE 1800.2 UVM standard compliance."""

    def test_uvm_find_all_style_matching(self):
        """Test patterns suitable for UVM find_all operations."""
        # Matching all drivers in environment
        assert uvm_is_match("top.env.*.driver", "top.env.ahb.driver") is True
        assert uvm_is_match("top.env.*.driver", "top.env.apb.driver") is True

        # Matching all agents
        assert uvm_is_match("top.env.*agent", "top.env.ahb_agent") is True

    def test_uvm_lookup_style_matching(self):
        """Test patterns suitable for UVM lookup operations."""
        # Exact component lookup
        assert uvm_is_match(".top.env.agent", ".top.env.agent") is True

    def test_uvm_component_hierarchy_matching(self):
        """Test standard UVM component name matching."""
        # Test standard UVM naming conventions
        assert uvm_is_match("*_env", "my_env") is True
        assert uvm_is_match("*_agent*", "ahb_agent_0") is True
        assert uvm_is_match("*", "any_component_name") is True

    def test_wildcard_precedence_most_specific_first(self):
        """Test that more specific patterns match first (IEEE requirement)."""
        # This tests the concept that more specific patterns should be considered
        assert uvm_is_match("a.b.c", "a.b.c") is True  # Exact match most specific
        assert uvm_is_match("a.b.*", "a.b.c") is True  # Wildcard less specific
