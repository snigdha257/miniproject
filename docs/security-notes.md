# Security Notes for Secure Masking

- `generate_key()` produces a Fernet encryption key that must be saved by the caller.
- The key cannot be recovered if lost, so the application should return it once and require the caller to store it safely.
- The server should never store this key in plaintext.
- At the API layer, encrypt the mapping server-side and return only the encrypted blob to clients or protected storage.
- When decrypting, use the same key and handle `WrongKeyError` cleanly so invalid keys or corrupted blobs return a 400-style error rather than crashing the service.
- Treat the encryption key as a secret value just like any other credential: keep it in secure configuration, a hardware security module, or client-managed vault if you want zero-knowledge storage.
