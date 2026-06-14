"""Show that `count += 1` is NOT a single instruction.

Run:
    python bytecode_demo.py
"""
import dis


def increment(counter):
    counter[0] += 1


def increment_attr(obj):
    obj.x += 1


print("=== counter[0] += 1 ===")
dis.dis(increment)

print("\n=== obj.x += 1 ===")
dis.dis(increment_attr)

print("\nNotice: each increment is several bytecodes.")
print("The interpreter can switch threads between any two of them.")
