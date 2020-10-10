from enum import Enum, auto
import factory_classes
import base_classes
import predefined_component_classes

uvm_root = predefined_component_classes.uvm_root('uvm_root',None)

def run_test(test_name):
    test = base_classes.uvm_object.create_by_name ( globals ()[test_name], 'uvm_test_top' )


