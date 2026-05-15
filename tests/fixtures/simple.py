"""
Simple Python file for testing.
"""


def simple_function():
    """A simple function."""
    return 42


def complex_function(x, y):
    """A complex function with multiple branches."""
    if x > 0:
        if y > 0:
            return x + y
        else:
            return x - y
    elif x < 0:
        if y > 0:
            return -x + y
        else:
            return -x - y
    else:
        return 0


class SampleClass:
    """A sample class."""

    def __init__(self, value):
        self.value = value

    def method_a(self):
        """Method A calls method B."""
        return self.method_b() + 1

    def method_b(self):
        """Method B is called by method A."""
        return self.value * 2

    def unused_method(self):
        """This method is never called."""
        return "unused"


if __name__ == "__main__":
    # Test the functions
    print(simple_function())
    print(complex_function(5, 3))
    obj = SampleClass(10)
    print(obj.method_a())