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
    assert classes[0].parent == "Animal"
