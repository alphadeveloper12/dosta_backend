
import subprocess
import os
import sys

# List of all population scripts found in the directory
scripts = [
    "populate_american_menus.py",
    "populate_arabic_menu_120.py",
    "populate_arabic_menu_200.py",
    "populate_arabic_menu_260.py",
    "populate_asian_menu_120.py",
    "populate_asian_menu_145.py",
    "populate_indian_menu_100.py",
    "populate_indian_menu_120.py",
    "populate_indian_menu_150.py",
    "populate_indian_menu_200.py",
    "populate_indian_menu_240.py",
    "populate_indian_menu_260.py",
    "populate_italian_menu_100.py",
    "populate_italian_menu_120.py",
    "populate_italian_menu_140.py",
    "populate_filipino_menu_120.py",
    "populate_filipino_menu_140.py",
    "populate_international_menu_90.py",
    "populate_international_menu_100.py",
    "populate_international_menu_120.py",
    "populate_international_menu_145.py",
    "populate_international_menu_150.py",
    "populate_african_menu_120.py",
    "populate_turkish_menu_100.py",
    "populate_turkish_menu_120.py",
    "populate_turkish_menu_145.py",
    "populate_canapes.py",
    "populate_coffee_break.py",
    "populate_live_stations.py",
    "populate_platters.py"
]

def run_all():
    print("Starting Master Population...")
    failures = []
    for script in scripts:
        if not os.path.exists(script):
            print(f"Skipping {script} (Not found)")
            continue
            
        print(f"Running {script}...")
        try:
            result = subprocess.run([sys.executable, script], 
                                  capture_output=True, 
                                  text=True, 
                                  check=True)
            print("  OK")
        except subprocess.CalledProcessError as e:
            print(f"  FAILED: {e}")
            print(e.stdout)
            print(e.stderr)
            failures.append(script)
    
    print("-" * 30)
    print("Master Population Complete.")
    if failures:
        print(f"Failures: {failures}")
    else:
        print("All scripts ran successfully.")

if __name__ == "__main__":
    run_all()
