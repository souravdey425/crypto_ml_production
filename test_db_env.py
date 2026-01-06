import os
from dotenv import load_dotenv

load_dotenv()

print("DB_HOST =", os.getenv("DB_HOST"))
print("DB_NAME =", os.getenv("DB_NAME"))
print("DB_PORT =", os.getenv("DB_PORT"))
