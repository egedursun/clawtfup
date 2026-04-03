#!/usr/bin/env python3
"""Simple calculator app."""
import sys


def add(a, b):
    return a + b


def subtract(a, b):
    return a - b


def multiply(a, b):
    return a * b


def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


def calculate(expression):
    parts = expression.split()
    if len(parts) != 3:
        raise ValueError(f"Expected '<number> <op> <number>', got: {expression!r}")

    a, op, b = parts
    a, b = float(a), float(b)

    ops = {
        "+": add,
        "-": subtract,
        "*": multiply,
        "/": divide,
    }

    if op not in ops:
        raise ValueError(f"Unknown operator: {op!r}")

    return ops[op](a, b)


def format_result(value):
    if value == int(value):
        return str(int(value))
    return str(value)


def main():
    print("Calculator — type '<number> <op> <number>' or 'quit' to exit")
    while True:
        try:
            sys.stdout.write("> ")
            sys.stdout.flush()
            line = sys.stdin.readline()
            if not line:
                print()
                break
            line = line.strip()
        except KeyboardInterrupt:
            print()
            break

        if line.lower() in ("quit", "exit", "q"):
            break

        if not line:
            continue

        try:
            result = calculate(line)
            print(format_result(result))
        except ValueError as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
