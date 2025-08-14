import os
import pickle
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from hashlib import sha256

# === КЛЮЧИ ===
PASSWORD = b'my-secret-password'  # можно задать вручную
KEY = sha256(PASSWORD).digest()  # 32 байта
IV = b'1234567890abcdef'         # 16 байт

# === Папка и выходной файл ===
DATA_DIR = 'data'
OUTPUT_FILE = 'data.pkg'

# === Читаем все файлы в папке data ===
data_dict = {}

for root, _, files in os.walk(DATA_DIR):
    for fname in files:
        path = os.path.join(root, fname)
        rel_path = os.path.relpath(path, DATA_DIR)  # ключ в словаре
        with open(path, 'rb') as f:
            data_dict[rel_path] = f.read()

print(f"[INFO] Найдено файлов: {len(data_dict)}")

# === Упаковываем и шифруем ===
raw_bytes = pickle.dumps(data_dict)
cipher = AES.new(KEY, AES.MODE_CBC, IV)
encrypted = cipher.encrypt(pad(raw_bytes, AES.block_size))

# === Сохраняем ===
with open(OUTPUT_FILE, 'wb') as f:
    f.write(encrypted)

print(f"[OK] Шифрованный архив создан: {OUTPUT_FILE}")
