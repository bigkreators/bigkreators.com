#!/usr/bin/env python3
import os
from dotenv import load_dotenv

load_dotenv()

print("Token Configuration:")
print("-" * 40)
print(f"OLD Token: 8gA6fYY29dSeg6KvxkbZyXsS4wkUBS4GheAM1Cckj4yP")
print(f"NEW Token: pDcf4inBQfDKu6aPh3hSJE98am5ckJ2pYBRTrABAEkG")
print("-" * 40)
print(f"ENV Token: {os.getenv('TOKEN_MINT_ADDRESS')}")
print("-" * 40)

if os.getenv('TOKEN_MINT_ADDRESS') == 'pDcf4inBQfDKu6aPh3hSJE98am5ckJ2pYBRTrABAEkG':
    print("✅ Using NEW token with metadata!")
else:
    print("❌ Still using old token - update your .env file!")
