import struct
import sys


def read_string(f):
    """Read a length-prefixed UTF-8 string (2-byte big-endian length + bytes)."""
    length = struct.unpack(">H", f.read(2))[0]
    return f.read(length).decode("utf-8")


def read_binary_set(filepath):
    with open(filepath, "rb") as f:
        # Read and verify magic bytes
        magic = f.read(4)
        if magic != b"LEGO":
            print("Error: Not a valid LEGO binary file.")
            return

        # Read set info
        set_id = read_string(f)
        name = read_string(f)
        year = struct.unpack(">H", f.read(2))[0]
        category = read_string(f)

        print(f"Set ID:   {set_id}")
        print(f"Name:     {name}")
        print(f"Year:     {year if year != 0 else 'Unknown'}")
        print(f"Category: {category if category else 'Unknown'}")
        print()

        # Read bricks
        num_bricks = struct.unpack(">I", f.read(4))[0]
        print(f"Bricks ({num_bricks}):")
        print(f"{'Name':<40} {'Color ID':>10} {'Count':>8}")
        print("-" * 60)

        #Read each brick name, color_id, and count
        for _ in range(num_bricks):
            brick_name = read_string(f)
            color_id = struct.unpack(">i", f.read(4))[0]
            count = struct.unpack(">i", f.read(4))[0]
            print(f"{brick_name:<40} {color_id:>10} {count:>8}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python read_binary_set.py <file>")
        sys.exit(1)
    read_binary_set(sys.argv[1])
