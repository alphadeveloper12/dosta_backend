import os
import subprocess

scripts = [
    "populate_indian_menu.py",
    "populate_indian_menu_120.py",
    "populate_indian_menu_150.py",
    "populate_indian_menu_200.py",
    "populate_indian_menu_240.py",
    "populate_international_menu_90.py"
]

for script in scripts:
    print(f"Running {script}...")
    result = subprocess.run(["python", script], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"  Success!")
    else:
        print(f"  Failed!")
        print(result.stderr)

print("Restoration Complete.")
