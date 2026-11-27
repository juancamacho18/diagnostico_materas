import secrets

print("ESP32-" + secrets.token_hex(6).upper())
