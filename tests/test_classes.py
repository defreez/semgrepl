import semgrepl.main as sm

def test_python_classes_simple():
    config = sm.init("tests/testcases/python/classes/simple.py")
    classes = sm.all_classes(config)
    assert len(classes) == 1
    assert classes[0].name == "Handler"

def test_python_classes_inheritance():
    config = sm.init("tests/testcases/python/classes/inheritance.py")
    classes = sm.classes_by_name(config, "Cat")
    assert len(classes) == 1
    assert classes[0].parent_name == "Animal"

def test_python_classes_package_inheritance():
    """Tests transitive inheritance from external module."""
    config = sm.init("tests/testcases/python/classes/package_inheritance.py")
    classes = sm.all_classes(config)
    hierarchy = sm.class_hierarchy(classes)
    subclasses = sm.subclasses(hierarchy, "flask.views.MethodView")
    assert len(subclasses) == 2
