# debug_env.py
import environ
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

print(env('AWS_STORAGE_BUCKET_NAME', default='Not set'))
