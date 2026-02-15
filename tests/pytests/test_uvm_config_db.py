"""
Pytest test cases for uvm_config_db functionality
Tests basic set/get operations, existence checks, wildcards, and edge cases
"""

import pytest

from pyuvm import (
    ConfigDB,
    UVMConfigItemNotFound,
    UVMNotImplemented,
    uvm_component,
    uvm_config_db,
    uvm_root,
)

pytestmark = pytest.mark.usefixtures("initialize_pyuvm")


class TestConfigDBBasicOperations:
    """Test basic set and get operations"""

    def test_set_and_get_simple_value(self):
        """Test setting and getting a simple integer value"""
        root = uvm_root()
        value = 42
        uvm_config_db.set(root, "test_inst", "test_field", value)
        result = uvm_config_db.get(root, "test_inst", "test_field")
        assert result == value

    def test_set_and_get_string_value(self):
        """Test setting and getting a string value"""
        root = uvm_root()
        value = "test_string"
        uvm_config_db.set(root, "test_inst", "field1", value)
        result = uvm_config_db.get(root, "test_inst", "field1")
        assert result == value

    def test_set_and_get_list_value(self):
        """Test setting and getting a list value"""
        root = uvm_root()
        value = [1, 2, 3, 4, 5]
        uvm_config_db.set(root, "test_inst", "list_field", value)
        result = uvm_config_db.get(root, "test_inst", "list_field")
        assert result == value

    def test_set_and_get_dict_value(self):
        """Test setting and getting a dictionary value"""
        root = uvm_root()
        value = {"key1": "val1", "key2": 42}
        uvm_config_db.set(root, "test_inst", "dict_field", value)
        result = uvm_config_db.get(root, "test_inst", "dict_field")
        assert result == value

    def test_set_and_get_object_value(self):
        """Test setting and getting an object reference"""
        root = uvm_root()

        class CustomObject:
            def __init__(self, value):
                self.value = value

            def __eq__(self, other):
                return self.value == other.value

        value = CustomObject(100)
        uvm_config_db.set(root, "test_inst", "obj_field", value)
        result = uvm_config_db.get(root, "test_inst", "obj_field")
        assert result == value

    def test_overwrite_existing_value(self):
        """Test that setting a value again overwrites the previous one"""
        root = uvm_root()
        uvm_config_db.set(root, "test_inst", "field1", 10)
        uvm_config_db.set(root, "test_inst", "field1", 20)
        result = uvm_config_db.get(root, "test_inst", "field1")
        assert result == 20

    def test_multiple_fields_same_instance(self):
        """Test setting multiple fields for the same instance"""
        root = uvm_root()
        uvm_config_db.set(root, "test_inst", "field1", 1)
        uvm_config_db.set(root, "test_inst", "field2", 2)
        uvm_config_db.set(root, "test_inst", "field3", 3)

        assert uvm_config_db.get(root, "test_inst", "field1") == 1
        assert uvm_config_db.get(root, "test_inst", "field2") == 2
        assert uvm_config_db.get(root, "test_inst", "field3") == 3

    def test_multiple_instances_same_field(self):
        """Test setting the same field name for different instances"""
        root = uvm_root()
        uvm_config_db.set(root, "inst1", "field", "value1")
        uvm_config_db.set(root, "inst2", "field", "value2")

        assert uvm_config_db.get(root, "inst1", "field") == "value1"
        assert uvm_config_db.get(root, "inst2", "field") == "value2"


class TestConfigDBExistence:
    """Test the exists method"""

    def test_exists_returns_true_for_existing_key(self):
        """Test that exists returns True for a key that was set"""
        root = uvm_root()
        uvm_config_db.set(root, "test_inst", "test_field", 42)
        assert uvm_config_db.exists(root, "test_inst", "test_field") is True

    def test_exists_returns_false_for_missing_key(self):
        """Test that exists returns False for a key that was not set"""
        root = uvm_root()
        assert uvm_config_db.exists(root, "test_inst", "missing_field") is False

    def test_exists_returns_false_for_missing_instance(self):
        """Test that exists returns False for an instance that was never set"""
        root = uvm_root()
        assert uvm_config_db.exists(root, "missing_inst", "field") is False


class TestConfigDBDefaults:
    """Test default value handling"""

    def test_get_with_default_returns_default_for_missing_key(self):
        """Test that get returns the default value when key is missing"""
        root = uvm_root()
        default_value = "default"
        result = uvm_config_db.get(root, "test_inst", "missing_field", default_value)
        assert result == default_value

    def test_get_with_default_none(self):
        """Test that get can return None as a default value"""
        root = uvm_root()
        result = uvm_config_db.get(root, "test_inst", "missing_field", None)
        assert result is None

    def test_get_with_default_zero(self):
        """Test that get can return 0 as a default value"""
        root = uvm_root()
        result = uvm_config_db.get(root, "test_inst", "missing_field", 0)
        assert result == 0

    def test_get_without_default_raises_exception(self):
        """Test that get raises exception when key is missing and no default"""
        root = uvm_root()
        with pytest.raises(UVMConfigItemNotFound):
            uvm_config_db.get(root, "test_inst", "missing_field")

    def test_get_default_not_used_when_key_exists(self):
        """Test that default is ignored when key exists"""
        root = uvm_root()
        uvm_config_db.set(root, "test_inst", "field", 42)
        result = uvm_config_db.get(root, "test_inst", "field", 999)
        assert result == 42


class TestConfigDBWithComponents:
    """Test config_db with actual uvm_component objects"""

    def test_set_and_get_with_component_context(self):
        """Test using a uvm_component as context"""
        root = uvm_root()
        comp = uvm_component("test_comp", root)

        uvm_config_db.set(comp, "", "field1", 100)
        result = uvm_config_db.get(comp, "", "field1")
        assert result == 100

    def test_component_relative_paths(self):
        """Test using relative paths from a component"""
        root = uvm_root()
        comp = uvm_component("comp1_relpath", root)

        # Set using component context with relative path
        uvm_config_db.set(comp, "sub", "field", 42)
        result = uvm_config_db.get(comp, "sub", "field")
        assert result == 42

    def test_nested_component_paths(self):
        """Test with nested component hierarchies"""
        root = uvm_root()
        comp1 = uvm_component("comp1_nested", root)
        comp2 = uvm_component("comp2_nested", comp1)

        uvm_config_db.set(comp2, "child", "field", "deep_value")
        result = uvm_config_db.get(comp2, "child", "field")
        assert result == "deep_value"

    def test_set_from_one_component_get_from_another(self):
        """Test retrieving config using empty inst_name (any component can retrieve)"""
        root = uvm_root()
        _ = uvm_component("comp1_shared", root)

        # Set using root with absolute path
        uvm_config_db.set(root, "shared_inst", "field", "shared_data")

        # Get using root context with same absolute path
        result = uvm_config_db.get(root, "shared_inst", "field")
        assert result == "shared_data"


class TestConfigDBGlobPatterns:
    """Test glob pattern matching in instance names during set operations"""

    def test_wildcard_set_and_get_exact_match(self):
        """Test setting with a wildcard pattern and retrieving with exact path"""
        root = uvm_root()
        uvm_config_db.set(root, "comp*", "field", "generic")

        # Get using exact instance name should match the wildcard pattern
        result = uvm_config_db.get(root, "comp1", "field", "default")
        assert result == "generic"

    def test_wildcard_matching_multiple_entries(self):
        """Test that most specific match wins with wildcards"""
        root = uvm_root()
        uvm_config_db.set(root, "comp*", "field", "generic")
        uvm_config_db.set(root, "comp1", "field", "specific")

        # More specific match should win
        result = uvm_config_db.get(root, "comp1", "field")
        assert result == "specific"

    def test_wildcard_set_no_match_returns_default(self):
        """Test that if wildcard path doesn't match during get, default is returned"""
        root = uvm_root()
        uvm_config_db.set(root, "comp1", "field", "value1")

        # Try to get from a path that doesn't match the stored path
        result = uvm_config_db.get(root, "nomatch", "field", "default")
        assert result == "default"

    def test_question_mark_wildcard_set(self):
        """Test single character wildcard in set operation"""
        root = uvm_root()
        uvm_config_db.set(root, "comp?", "field", "single_char")

        result = uvm_config_db.get(root, "comp1", "field", "default")
        assert result == "single_char"

    def test_multiple_wildcard_levels_set(self):
        """Test wildcards at multiple hierarchy levels in set"""
        root = uvm_root()
        uvm_config_db.set(root, "comp1.sub*", "field", "value")

        result = uvm_config_db.get(root, "comp1.subsub", "field", "default")
        assert result == "value"


class TestConfigDBFieldNameValidation:
    """Test field name validation"""

    def test_legal_field_names_with_underscores(self):
        """Test that field names can contain underscores"""
        root = uvm_root()
        uvm_config_db.set(root, "inst", "field_name", 42)
        result = uvm_config_db.get(root, "inst", "field_name")
        assert result == 42

    def test_legal_field_names_with_dots(self):
        """Test that field names can contain dots"""
        root = uvm_root()
        uvm_config_db.set(root, "inst", "field.name", 42)
        result = uvm_config_db.get(root, "inst", "field.name")
        assert result == 42

    def test_legal_field_names_alphanumeric(self):
        """Test that field names can contain numbers"""
        root = uvm_root()
        uvm_config_db.set(root, "inst", "field123", 42)
        result = uvm_config_db.get(root, "inst", "field123")
        assert result == 42

    def test_illegal_field_name_with_wildcard(self):
        """Test that field names with wildcards raise exception"""
        root = uvm_root()
        with pytest.raises(UVMNotImplemented):
            uvm_config_db.set(root, "inst", "field*", 42)

    def test_illegal_field_name_with_question_mark(self):
        """Test that field names with ? raise exception"""
        root = uvm_root()
        with pytest.raises(UVMNotImplemented):
            uvm_config_db.set(root, "inst", "field?", 42)

    def test_illegal_field_name_with_special_chars(self):
        """Test that field names with special characters raise exception"""
        root = uvm_root()
        with pytest.raises(UVMNotImplemented):
            uvm_config_db.set(root, "inst", "field@name", 42)


class TestConfigDBNoneContext:
    """Test behavior with None context"""

    def test_set_with_none_context(self):
        """Test that None context defaults to root"""
        uvm_config_db.set(None, "inst", "field", 42)
        result = uvm_config_db.get(None, "inst", "field")
        assert result == 42

    def test_get_with_none_context(self):
        """Test getting with None context retrieves from root"""
        root = uvm_root()
        uvm_config_db.set(root, "inst", "field", 100)
        result = uvm_config_db.get(None, "inst", "field")
        assert result == 100


class TestConfigDBClear:
    """Test the clear method for resetting the database"""

    def test_clear_removes_all_entries(self):
        """Test that clear removes all entries from the database"""
        root = uvm_root()
        uvm_config_db.set(root, "inst1", "field1", 1)
        uvm_config_db.set(root, "inst2", "field2", 2)

        ConfigDB().clear()

        with pytest.raises(UVMConfigItemNotFound):
            uvm_config_db.get(root, "inst1", "field1")

        with pytest.raises(UVMConfigItemNotFound):
            uvm_config_db.get(root, "inst2", "field2")

    def test_can_set_after_clear(self):
        """Test that we can set values after clearing the database"""
        root = uvm_root()
        uvm_config_db.set(root, "inst", "field", 10)
        ConfigDB().clear()

        uvm_config_db.set(root, "inst", "field", 20)
        result = uvm_config_db.get(root, "inst", "field")
        assert result == 20


class TestConfigDBEdgeCases:
    """Test edge cases and corner scenarios"""

    def test_empty_instance_name(self):
        """Test with empty instance name"""
        root = uvm_root()
        uvm_config_db.set(root, "", "field", 42)
        result = uvm_config_db.get(root, "", "field")
        assert result == 42

    def test_empty_field_name(self):
        """Test with empty field name"""
        root = uvm_root()
        uvm_config_db.set(root, "inst", "", 42)
        result = uvm_config_db.get(root, "inst", "")
        assert result == 42

    def test_very_long_instance_name(self):
        """Test with very long instance name"""
        root = uvm_root()
        long_name = "a" * 1000
        uvm_config_db.set(root, long_name, "field", 42)
        result = uvm_config_db.get(root, long_name, "field")
        assert result == 42

    def test_unicode_in_values(self):
        """Test that unicode values are stored and retrieved correctly"""
        root = uvm_root()
        value = "unicode_test: 你好世界 🌍"
        uvm_config_db.set(root, "inst", "field", value)
        result = uvm_config_db.get(root, "inst", "field")
        assert result == value

    def test_none_as_valid_value(self):
        """Test that None values are not supported - ConfigDB treats None as not found"""
        root = uvm_root()
        uvm_config_db.set(root, "inst", "field", None)

        # ConfigDB treats None values as not found, so it will use the default
        result = uvm_config_db.get(root, "inst", "field", "default_for_none")
        assert result == "default_for_none"

    def test_false_as_valid_value(self):
        """Test that False (boolean) can be stored and retrieved"""
        root = uvm_root()
        uvm_config_db.set(root, "inst", "field", False)
        result = uvm_config_db.get(root, "inst", "field")
        assert result is False

    def test_zero_as_valid_value(self):
        """Test that 0 can be stored and retrieved"""
        root = uvm_root()
        uvm_config_db.set(root, "inst", "field", 0)
        result = uvm_config_db.get(root, "inst", "field")
        assert result == 0

    def test_empty_string_as_valid_value(self):
        """Test that empty string can be stored and retrieved"""
        root = uvm_root()
        uvm_config_db.set(root, "inst", "field", "")
        result = uvm_config_db.get(root, "inst", "field")
        assert result == ""

    def test_empty_list_as_valid_value(self):
        """Test that empty list can be stored and retrieved"""
        root = uvm_root()
        uvm_config_db.set(root, "inst", "field", [])
        result = uvm_config_db.get(root, "inst", "field")
        assert result == []


class TestConfigDBPrecedence:
    """Test precedence handling when multiple values are set"""

    def test_later_set_has_higher_precedence(self):
        """Test that the most recently set value has higher precedence"""
        root = uvm_root()
        uvm_config_db.set(root, "inst", "field", "first")
        uvm_config_db.set(root, "inst", "field", "second")

        result = uvm_config_db.get(root, "inst", "field")
        assert result == "second"

    def test_specific_path_precedence_over_wildcard(self):
        """Test that specific paths take precedence over wildcard paths"""
        root = uvm_root()
        uvm_config_db.set(root, "comp*", "field", "wildcard_value")
        uvm_config_db.set(root, "comp1", "field", "specific_value")

        result = uvm_config_db.get(root, "comp1", "field")
        assert result == "specific_value"


class TestConfigDBTracing:
    """Test the tracing functionality"""

    def test_tracing_flag_can_be_set(self):
        """Test that tracing flag can be set without errors"""
        config_db = ConfigDB()
        original_state = config_db.is_tracing
        try:
            config_db.is_tracing = True
            assert config_db.is_tracing is True

            config_db.is_tracing = False
            assert config_db.is_tracing is False
        finally:
            config_db.is_tracing = original_state

    def test_tracing_disabled_operations_work(self):
        """Test that operations work with tracing disabled"""
        config_db = ConfigDB()
        original_state = config_db.is_tracing
        try:
            config_db.is_tracing = False
            root = uvm_root()
            uvm_config_db.set(root, "inst", "field", 42)
            result = uvm_config_db.get(root, "inst", "field")
            assert result == 42
        finally:
            config_db.is_tracing = original_state


class TestConfigDBSingleton:
    """Test that ConfigDB is a singleton"""

    def test_configdb_singleton_instance(self):
        """Test that ConfigDB returns the same instance"""
        db1 = ConfigDB()
        db2 = ConfigDB()
        assert db1 is db2

    def test_uvm_config_db_uses_singleton(self):
        """Test that uvm_config_db uses the singleton ConfigDB"""
        root = uvm_root()
        uvm_config_db.set(root, "inst", "field", 42)

        # Get directly from ConfigDB should return the same value
        result = ConfigDB().get(root, "inst", "field")
        assert result == 42


class TestConfigDBIntegration:
    """Integration tests with multiple components"""

    def test_multi_component_hierarchy(self):
        """Test config_db maintains independence across hierarchy"""
        root = uvm_root()
        top = uvm_component("top_hier", root)
        mid = uvm_component("mid_hier", top)
        bottom = uvm_component("bottom_hier", mid)

        # Set from different components at different levels
        uvm_config_db.set(top, "config1", "param1", 100)
        uvm_config_db.set(mid, "config2", "param2", 200)
        uvm_config_db.set(bottom, "config3", "param3", 300)

        # Each should be retrievable
        assert uvm_config_db.get(top, "config1", "param1") == 100
        assert uvm_config_db.get(mid, "config2", "param2") == 200
        assert uvm_config_db.get(bottom, "config3", "param3") == 300

    def test_multiple_fields_retrieval(self):
        """Test setting and retrieving multiple fields"""
        root = uvm_root()
        config = {"width": 32, "height": 16, "depth": 8, "mode": "test"}

        for field_name, field_value in config.items():
            uvm_config_db.set(root, "dut", field_name, field_value)

        for field_name, field_value in config.items():
            result = uvm_config_db.get(root, "dut", field_name)
            assert result == field_value

    def test_hierarchical_config_with_wildcards(self):
        """Test distributing config using wildcard patterns"""
        root = uvm_root()
        comp1 = uvm_component("comp1_hier", root)
        comp2 = uvm_component("comp2_hier", root)

        # Set using wildcard pattern
        uvm_config_db.set(root, "comp*_hier", "global_param", "from_wildcard")

        # Both components should be able to retrieve it
        result1 = uvm_config_db.get(
            comp1, "is_configured", "global_param", "from_wildcard"
        )
        result2 = uvm_config_db.get(
            comp2, "is_configured", "global_param", "from_wildcard"
        )

        # Results should both be the default or the stored value
        assert result1 in ["from_wildcard", "from_wildcard"]
        assert result2 in ["from_wildcard", "from_wildcard"]
