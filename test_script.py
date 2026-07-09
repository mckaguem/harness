#!/usr/bin/env python3
"""
Test script for bash execution via execute_bash tool.
"""
def test_function(name):
    """Returns a greeting string for the given name."""
    return f"Hello, {name}! Welcome from test_function."

def main():
    print("Hello from test script!")
    print(f"Current directory: {__file__}")
    # Call the new function
    greeting = test_function("User")
    print(greeting)
    return 0

if __name__ == "__main__":
    main()