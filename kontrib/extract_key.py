import json
import base58

# Read the keypair file
with open('kontrib-authority.json', 'r') as f:
    keypair_bytes = json.load(f)

# Convert to base58
private_key_base58 = base58.b58encode(bytes(keypair_bytes)).decode()
print(f"Base58 Private Key: {private_key_base58}")

# The public key is the last 32 bytes
public_key_bytes = keypair_bytes[32:]
public_key_base58 = base58.b58encode(bytes(public_key_bytes)).decode()
print(f"Public Key: {public_key_base58}")
