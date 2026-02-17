"""
Comprehensive pytest tests for uvm_root find and find_all methods.

Tests cover:
- Basic find_all functionality with various patterns
- Basic find functionality and first match behavior
- Wildcard patterns in component names
- Component hierarchy traversal
- Edge cases and error conditions
- IEEE UVM standard compliance
"""

import pytest

from pyuvm import uvm_component, uvm_root


@pytest.fixture(autouse=True)
def reset_uvm_state():
    """Automatically reset UVM state before and after each test."""
    uvm_component.clear_components()
    uvm_root.clear_singletons()


@pytest.fixture()
def simple_hierarchy():
    """Create a simple component hierarchy for testing.

    Structure:
        root
        ├── env (uvm_component)
        │   ├── agent (uvm_component)
        │   │   └── driver (uvm_component)
        │   └── monitor (uvm_component)
        └── test (uvm_component)
    """
    root = uvm_root()
    env = uvm_component("env", root)
    agent = uvm_component("agent", env)
    driver = uvm_component("driver", agent)
    monitor = uvm_component("monitor", env)
    test = uvm_component("test", root)

    yield {
        "root": root,
        "env": env,
        "agent": agent,
        "driver": driver,
        "monitor": monitor,
        "test": test,
    }


@pytest.fixture()
def complex_hierarchy():
    """Create a complex component hierarchy with multiple similar names.

    Structure:
        root
        ├── env (uvm_component)
        │   ├── ahb_agent_0 (uvm_component)
        │   │   ├── ahb_driver (uvm_component)
        │   │   └── ahb_monitor (uvm_component)
        │   ├── ahb_agent_1 (uvm_component)
        │   │   ├── ahb_driver (uvm_component)
        │   │   └── ahb_monitor (uvm_component)
        │   └── apb_agent (uvm_component)
        │       ├── apb_driver (uvm_component)
        │       └── apb_monitor (uvm_component)
        └── coverage_collector (uvm_component)
    """
    root = uvm_root()
    env = uvm_component("env", root)

    # AHB agents
    ahb_agent_0 = uvm_component("ahb_agent_0", env)
    ahb_driver_0 = uvm_component("ahb_driver", ahb_agent_0)
    ahb_monitor_0 = uvm_component("ahb_monitor", ahb_agent_0)

    ahb_agent_1 = uvm_component("ahb_agent_1", env)
    ahb_driver_1 = uvm_component("ahb_driver", ahb_agent_1)
    ahb_monitor_1 = uvm_component("ahb_monitor", ahb_agent_1)

    # APB agent
    apb_agent = uvm_component("apb_agent", env)
    apb_driver = uvm_component("apb_driver", apb_agent)
    apb_monitor = uvm_component("apb_monitor", apb_agent)

    # Coverage collector
    coverage = uvm_component("coverage_collector", root)

    yield {
        "root": root,
        "env": env,
        "ahb_agent_0": ahb_agent_0,
        "ahb_driver_0": ahb_driver_0,
        "ahb_monitor_0": ahb_monitor_0,
        "ahb_agent_1": ahb_agent_1,
        "ahb_driver_1": ahb_driver_1,
        "ahb_monitor_1": ahb_monitor_1,
        "apb_agent": apb_agent,
        "apb_driver": apb_driver,
        "apb_monitor": apb_monitor,
        "coverage": coverage,
    }


class TestFindAllBasicFunctionality:
    """Test basic find_all functionality."""

    def test_find_all_exact_match(self, simple_hierarchy):
        """Test finding a component by exact name."""
        result = simple_hierarchy["root"].find_all("env")
        assert len(result) == 1
        assert result == [simple_hierarchy["env"]]

    def test_find_all_nested_exact_match(self, simple_hierarchy):
        """Test finding a nested component by full path."""
        result = simple_hierarchy["root"].find_all("env.agent")
        assert len(result) == 1
        assert result == [simple_hierarchy["agent"]]

    def test_find_all_deep_nested_exact_match(self, simple_hierarchy):
        """Test finding a deeply nested component by full path."""
        result = simple_hierarchy["root"].find_all("env.agent.driver")
        assert len(result) == 1
        assert result == [simple_hierarchy["driver"]]

    def test_find_all_no_match(self, simple_hierarchy):
        """Test finding a non-existent component."""
        result = simple_hierarchy["root"].find_all("nonexistent")
        assert len(result) == 0

    def test_find_all_wrong_path(self, simple_hierarchy):
        """Test finding with an incorrect path."""
        result = simple_hierarchy["root"].find_all("env.nonexistent.driver")
        assert len(result) == 0

    def test_find_all_empty_hierarchy(self):
        """Test find_all on empty hierarchy."""
        root = uvm_root()
        result = root.find_all("anything")
        assert len(result) == 0


class TestFindAllWildcardPatterns:
    """Test find_all with wildcard patterns."""

    def test_find_all_asterisk_wildcard_end(self, simple_hierarchy):
        """Test * wildcard at end of pattern."""
        result = simple_hierarchy["root"].find_all("env*")
        assert len(result) == 4
        assert simple_hierarchy["env"] in result
        assert simple_hierarchy["agent"] in result
        assert simple_hierarchy["driver"] in result
        assert simple_hierarchy["monitor"] in result

    def test_find_all_asterisk_wildcard_start(self, simple_hierarchy):
        """Test * wildcard at start of pattern."""
        result = simple_hierarchy["root"].find_all("*itor")
        # Should match 'monitor'
        assert len(result) == 1
        assert result == [simple_hierarchy["monitor"]]

    def test_find_all_asterisk_wildcard_middle(self, complex_hierarchy):
        """Test * wildcard in middle of pattern."""
        result = complex_hierarchy["root"].find_all("*ahb_agent_*")
        # Should match ahb_agent_0, ahb_agent_1
        assert len(result) == 6
        assert complex_hierarchy["ahb_agent_0"] in result
        assert complex_hierarchy["ahb_driver_0"] in result
        assert complex_hierarchy["ahb_monitor_0"] in result
        assert complex_hierarchy["ahb_agent_1"] in result
        assert complex_hierarchy["ahb_driver_1"] in result
        assert complex_hierarchy["ahb_monitor_1"] in result

    def test_find_all_asterisk_all_names(self, simple_hierarchy):
        """Test * wildcard matching all components."""
        result = simple_hierarchy["root"].find_all("*")
        # Should match all non-root components
        assert len(result) == 5
        assert simple_hierarchy["test"] in result
        assert simple_hierarchy["env"] in result
        assert simple_hierarchy["agent"] in result
        assert simple_hierarchy["driver"] in result
        assert simple_hierarchy["monitor"] in result

    def test_find_all_question_mark_wildcard(self, complex_hierarchy):
        """Test ? wildcard matching single character."""
        result = complex_hierarchy["root"].find_all("*.ahb_agent_?")
        # Should match ahb_agent_0 and ahb_agent_1
        assert len(result) == 2
        assert complex_hierarchy["ahb_agent_0"] in result
        assert complex_hierarchy["ahb_agent_1"] in result

    def test_find_all_question_mark_no_match(self, simple_hierarchy):
        """Test ? wildcard when string length doesn't match."""
        result = simple_hierarchy["root"].find_all("env?")
        # Should not match 'env' (needs exactly one more char)
        assert len(result) == 0

    def test_find_all_multiple_wildcards(self, complex_hierarchy):
        """Test multiple wildcards in pattern."""
        result = complex_hierarchy["root"].find_all("*.*.*driver")
        assert len(result) == 3
        assert complex_hierarchy["ahb_driver_0"] in result
        assert complex_hierarchy["ahb_driver_1"] in result
        assert complex_hierarchy["apb_driver"] in result


class TestFindAllHierarchyPatterns:
    """Test find_all with hierarchy-based patterns."""

    def test_find_all_single_dot_wildcard(self, simple_hierarchy):
        """Test wildcard matching single hierarchy level."""
        result = simple_hierarchy["root"].find_all("env.*.driver")
        # Should match env.agent.driver
        assert len(result) == 1
        assert result == [simple_hierarchy["driver"]]

    def test_find_all_multiple_level_wildcard(self, simple_hierarchy):
        """Test * wildcard matching multiple hierarchy levels."""
        result = simple_hierarchy["root"].find_all("env.*")
        assert len(result) == 3
        assert simple_hierarchy["agent"] in result
        assert simple_hierarchy["driver"] in result
        assert simple_hierarchy["monitor"] in result

    def test_find_all_start_with_dot_wildcard(self, simple_hierarchy):
        """Test matching all components when starting with *."""
        result = simple_hierarchy["root"].find_all("*.*")
        assert len(result) == 3
        assert simple_hierarchy["agent"] in result
        assert simple_hierarchy["driver"] in result
        assert simple_hierarchy["monitor"] in result

    def test_find_all_complex_hierarchy_pattern(self, complex_hierarchy):
        """Test complex pattern in hierarchy."""
        result = complex_hierarchy["root"].find_all("env.ahb_agent_0.*")
        assert len(result) == 2
        assert complex_hierarchy["ahb_driver_0"] in result
        assert complex_hierarchy["ahb_monitor_0"] in result


class TestFindAllRegexPatterns:
    """Test find_all with regular expression patterns."""

    def test_find_all_regex_alternation(self, complex_hierarchy):
        """Test regex with alternation."""
        result = complex_hierarchy["root"].find_all(r"/^env\.(ahb|apb)_.*_0$/")
        assert len(result) == 1
        assert result == [complex_hierarchy["ahb_agent_0"]]

    def test_find_all_regex_character_class(self, complex_hierarchy):
        """Test regex with character class."""
        result = complex_hierarchy["root"].find_all(r"/env\.ahb_[a-z]*_[0-1]$/")
        assert len(result) == 2
        assert complex_hierarchy["ahb_agent_0"] in result
        assert complex_hierarchy["ahb_agent_1"] in result

    def test_find_all_regex_any_character(self, simple_hierarchy):
        """Test regex with . (any character)."""
        result = simple_hierarchy["root"].find_all(r"/^env.agent$/")
        assert len(result) == 1
        assert result == [simple_hierarchy["agent"]]

    def test_find_all_regex_quantifier(self, complex_hierarchy):
        """Test regex with quantifier."""
        result = complex_hierarchy["root"].find_all(r"/.*\.ahb_[a-z]+_[0-9]+/")
        assert len(result) >= 2
        assert complex_hierarchy["ahb_agent_0"] in result
        assert complex_hierarchy["ahb_agent_1"] in result


class TestFindAllSubtreeSearch:
    """Test find_all with subtree starting point."""

    def test_find_all_from_subtree_root(self, simple_hierarchy):
        """Test finding components starting from a subtree."""
        result = simple_hierarchy["root"].find_all("*", simple_hierarchy["env"])
        assert len(result) == 4
        assert simple_hierarchy["agent"] in result
        assert simple_hierarchy["driver"] in result
        assert simple_hierarchy["monitor"] in result
        assert simple_hierarchy["env"] in result

    def test_find_all_from_subtree_no_root_in_results(self, simple_hierarchy):
        """Test that root is not included when searching from subtree."""
        result = simple_hierarchy["root"].find_all("*", simple_hierarchy["agent"])
        # Should only find driver under agent
        assert len(result) == 2
        assert simple_hierarchy["agent"] in result
        assert simple_hierarchy["driver"] in result

    def test_find_all_from_subtree_no_matches(self, simple_hierarchy):
        """Test find_all from subtree with no matches."""
        result = simple_hierarchy["root"].find_all(
            "nonexistent", simple_hierarchy["env"]
        )
        assert len(result) == 0


class TestFindBasicFunctionality:
    """Test basic find functionality."""

    def test_find_exact_match(self, simple_hierarchy):
        """Test finding a component by exact name."""
        result = simple_hierarchy["root"].find("env")
        assert result is not None
        assert result.get_name() == "env"

    def test_find_nested_exact_match(self, simple_hierarchy):
        """Test finding a nested component."""
        result = simple_hierarchy["root"].find("env.agent")
        assert result == simple_hierarchy["agent"]

    def test_find_nonexistent_returns_none(self, simple_hierarchy):
        """Test find returns None for non-existent component."""
        result = simple_hierarchy["root"].find("nonexistent")
        assert result is None

    def test_find_wrong_path_returns_none(self, simple_hierarchy):
        """Test find returns None for wrong path."""
        result = simple_hierarchy["root"].find("env.wrong.path")
        assert result is None


class TestFindMultipleMatches:
    """Test find behavior when multiple components match."""

    def test_find_returns_first_match(self, simple_hierarchy):
        """Test find returns first match when multiple match."""
        result = simple_hierarchy["root"].find("*")
        # Should return one of the top-level components (first match)
        assert result is not None
        assert result.get_name() in ["env", "test", "agent", "driver", "monitor"]

    def test_find_with_wildcard_multiple_matches(self, simple_hierarchy):
        """Test find returns first match with wildcard."""
        result = simple_hierarchy["root"].find("*.*.driver")
        assert result == simple_hierarchy["driver"]


class TestFindAllComplexScenarios:
    """Test find_all with complex scenarios."""

    def test_find_all_case_sensitive(self, simple_hierarchy):
        """Test that find_all is case-sensitive."""
        result = simple_hierarchy["root"].find_all("Env")
        assert len(result) == 0

    def test_find_all_full_path_requirement(self, simple_hierarchy):
        """Test that patterns match against full path."""
        result = simple_hierarchy["root"].find_all("*.agent")
        assert len(result) == 1
        assert result == [simple_hierarchy["agent"]]

    def test_find_all_multiple_components_same_name(self, complex_hierarchy):
        """Test finding multiple components with same name in different locations."""
        result = complex_hierarchy["root"].find_all("*driver")
        # Should find all components ending with 'driver'
        assert len(result) == 3  # ahb_driver from agent_0, agent_1, and apb_driver
        assert complex_hierarchy["ahb_driver_0"] in result
        assert complex_hierarchy["ahb_driver_1"] in result
        assert complex_hierarchy["apb_driver"] in result

    def test_find_all_empty_pattern_does_not_match(self, simple_hierarchy):
        """Test that empty pattern doesn't match."""
        result = simple_hierarchy["root"].find_all("")
        assert len(result) == 0


class TestFindIEEUVMCompliance:
    """Test IEEE 1800.2 UVM standard compliance."""

    def test_find_all_returns_list_type(self, simple_hierarchy):
        """Test find_all returns a list."""
        result = simple_hierarchy["root"].find_all("env")
        assert isinstance(result, list)

    def test_find_all_contains_uvm_components(self, simple_hierarchy):
        """Test find_all returns uvm_component instances."""
        result = simple_hierarchy["root"].find_all("env.*")
        assert all(isinstance(comp, uvm_component) for comp in result)

    def test_find_returns_uvm_component_or_none(self, simple_hierarchy):
        """Test find returns uvm_component or None."""
        result1 = simple_hierarchy["root"].find("env")
        result2 = simple_hierarchy["root"].find("nonexistent")
        assert isinstance(result1, uvm_component)
        assert result2 is None

    def test_find_full_name_as_match_criterion(self, simple_hierarchy):
        """Test that full_name is used as the matching criterion per IEEE standard."""
        # The full_name includes the hierarchy path
        result = simple_hierarchy["root"].find_all("env.agent.driver")
        assert len(result) == 1
        assert result[0].get_full_name() == "env.agent.driver"


class TestFindEdgeCases:
    """Test edge cases."""

    def test_find_single_component_hierarchy(self):
        """Test find with only root."""
        root = uvm_root()
        result = root.find("anything")
        assert result is None

    def test_find_all_single_component_hierarchy(self):
        """Test find_all with only root."""
        root = uvm_root()
        result = root.find_all("*")
        assert len(result) == 0
        assert result == list()

    def test_find_after_component_removal(self, simple_hierarchy):
        """Test find after modifying hierarchy."""
        # Clear children to simulate removal
        simple_hierarchy["env"].clear_children()
        result = simple_hierarchy["root"].find("env.agent")
        assert result is None

    def test_find_all_preserves_hierarchy_structure(self, complex_hierarchy):
        """Test that find_all results maintain proper parent-child relationships."""
        result = complex_hierarchy["root"].find_all("*.ahb_*")
        # All driver components should have env as ancestor
        assert len(result) == 6
        for comp in result:
            assert "env" in comp.get_full_name()
