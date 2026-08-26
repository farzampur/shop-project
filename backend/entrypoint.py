import os
import time
import psycopg
import subprocess
import sys


def wait_for_database():
    print("Waiting for PostgreSQL...", flush=True)

    while True:
        try:
            conn = psycopg.connect(
                dbname=os.environ["DB_NAME"],
                user=os.environ["DB_USER"],
                password=os.environ["DB_PASSWORD"],
                host=os.environ["DB_HOST"],
                port=os.environ["DB_PORT"],
            )

            conn.close()

            print("PostgreSQL is ready.", flush=True)
            return

        except Exception:
            print("PostgreSQL is not ready yet...", flush=True)
            time.sleep(2)


def run_command(command):
    print(f"Running: {' '.join(command)}", flush=True)

    result = subprocess.run(command)

    if result.returncode != 0:
        print("Command failed.", flush=True)
        sys.exit(result.returncode)


def create_admin():
    username = os.environ.get("ADMIN_USERNAME")
    password = os.environ.get("ADMIN_PASSWORD")
    email = os.environ.get("ADMIN_EMAIL", "")

    if not username or not password:
        print(
            "ADMIN_USERNAME or ADMIN_PASSWORD not provided. "
            "Skipping admin creation.",
            flush=True,
        )
        return

    print("Checking administrator account...", flush=True)

    script = """
from django.contrib.auth import get_user_model

User = get_user_model()

username = __import__("os").environ["ADMIN_USERNAME"]
password = __import__("os").environ["ADMIN_PASSWORD"]
email = __import__("os").environ.get("ADMIN_EMAIL", "")

user, created = User.objects.get_or_create(
    username=username,
    defaults={
        "email": email,
        "is_staff": True,
        "is_superuser": True,
        "is_active": True,
    },
)

if created:
    user.set_password(password)
    user.save()
    print("Administrator created.")
else:
    print("Administrator already exists.")
"""

    run_command([
        sys.executable,
        "manage.py",
        "shell",
        "-c",
        script,
    ])


def main():
    wait_for_database()

    print("Running migrations...", flush=True)

    run_command([
        sys.executable,
        "manage.py",
        "migrate",
        "--noinput",
    ])

    create_admin()

    print("Collecting static files...", flush=True)

    run_command([
        sys.executable,
        "manage.py",
        "collectstatic",
        "--noinput",
    ])

    print("Starting Shop...", flush=True)

    os.execvp(
        "waitress-serve",
        [
            "waitress-serve",
            "--listen=0.0.0.0:8000",
            "config.wsgi:application",
        ],
    )


if __name__ == "__main__":
    main()