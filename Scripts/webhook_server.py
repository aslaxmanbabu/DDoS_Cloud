import os
from time import sleep

FLAG_FILE = "alert_active.flag"


def create_flag():
    # Create the flag file
    with open(FLAG_FILE, "w") as f:
        f.write("Alert active for 5 minutes.\n")
    print("Flag file created. Alert active.")


def remove_flag_after_timeout(timeout=300):
    # Wait for the specified timeout (1 hour)
    sleep(timeout)
    if os.path.exists(FLAG_FILE):
        os.remove(FLAG_FILE)
        print("Flag file removed. Alert deactivated.")


if __name__ == "__main__":
    create_flag()
    remove_flag_after_timeout()
