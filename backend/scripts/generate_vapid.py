"""
Generate VAPID keys for Web Push notifications.

Usage (from backend/ directory):
    python scripts/generate_vapid.py

Or inside Docker:
    docker-compose exec backend python scripts/generate_vapid.py

Copy the output into your .env file.
"""
import base64
import sys

try:
    from py_vapid import Vapid
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
except ImportError:
    print("ERROR: py_vapid not installed. Run: pip install pywebpush", file=sys.stderr)
    sys.exit(1)

v = Vapid()
v.generate_keys()

# Private key: base64-encode the PEM bytes (single line, safe for .env)
priv_pem: bytes = v.private_pem()
private_key_b64 = base64.b64encode(priv_pem).decode()

# Public key: uncompressed EC point, base64url no-padding (applicationServerKey format)
pub_bytes = v.public_key.public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
public_key_b64url = base64.urlsafe_b64encode(pub_bytes).rstrip(b"=").decode()

print("# Add these lines to backend/.env")
print(f"VAPID_PRIVATE_KEY={private_key_b64}")
print(f"VAPID_PUBLIC_KEY={public_key_b64url}")
print(f"VAPID_CLAIM_EMAIL=admin@yourdomain.com")
