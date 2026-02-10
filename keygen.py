from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import base64

# Generate Private Key
private_key = ed25519.Ed25519PrivateKey.generate()

# Derive Public Key
public_key = private_key.public_key()

# Export for storage
private_hex = private_key.private_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PrivateFormat.Raw,
    encryption_algorithm=serialization.NoEncryption()
).hex()

public_hex = public_key.public_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PublicFormat.Raw
).hex()

print(f"--- SERVER SIDE (Private Key) ---\n{private_hex}\n")
print(f"--- CLIENT SIDE (Public Key) ---\n{public_hex}")