import os

filepath = r'E:\OrderSync - Dev\frontend\public\login\login.html'
with open(filepath, 'rb') as f:
    b = f.read()

# Let's decode it manually handling errors to find the specific bytes
try:
    text = b.decode('utf-8')
    print("No errors decoding UTF-8")
except UnicodeDecodeError as e:
    print(f"Unicode Decode Error at byte {e.start}: {e}")
    bad_bytes = b[max(0, e.start - 5):e.end + 5]
    print(f"Context surrounding bad bytes: {bad_bytes}")
    print(f"Hex of context: {bad_bytes.hex()}")

