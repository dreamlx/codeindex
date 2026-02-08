
class Parent:
    """Parent class"""
    pass

class Child(Parent):
    """Child class"""
    def method(self):
        result = add(1, 2)
        return result

def add(x, y):
    """Add function"""
    return x + y
