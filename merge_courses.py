import sys
import os
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from catering.models import Course, FixedCateringMenu, MenuItem

def merge_courses():
    print("Merging Courses...")

    # Mappings: { "Canonical Name": ["Duplicate 1", "Duplicate 2"] }
    # Based on inspection, we likely want "Desserts" if it has the image, or "Dessert" if valid.
    # Looking at the output from previous step will determine the exact IDs, 
    # but for now I will implement a logic to find the best one.
    
    # Logic: Prefer course with an image that is NOT placeholder.
    # Target Names we generally want: "Desserts", "Main Courses", "Salads"
    
    normalization_map = {
        "Desserts": ["Dessert"],
        "Main Courses": ["Main Course", "Main Dish", "Mains"],
        "Salads": ["Salads & Chaats", "Salad", "Salads & Starters"] # Be careful with "Salads & Chaats" if strictly different
    }
    
    # Actually, "Salads & Chaats" might be distinct for Indian.
    # Let's strictly just fix "Dessert" -> "Desserts" and "Main Course" -> "Main Courses" 
    # if "Desserts" has the good image.
    
    # Let's try to find the "Desserts" course that has a real image.
    all_desserts = Course.objects.filter(name__icontains="Dessert")
    target_dessert = None
    
    # Find the best target
    for d in all_desserts:
        img_str = str(d.image)
        if img_str and "placeholder" not in img_str and "default" not in img_str:
            target_dessert = d
            break
    
    if not target_dessert:
        print("No 'good' Dessert course found with unique image. Picking the one named 'Desserts' as target.")
        target_dessert = all_desserts.filter(name="Desserts").first()
        
    if not target_dessert:
        # If still none, just pick the first one
        target_dessert = all_desserts.first()

    if target_dessert:
        print(f"Target Dessert Course: {target_dessert.name} (ID: {target_dessert.id})")
        
        for d in all_desserts:
            if d.id != target_dessert.id:
                print(f"  Merging {d.name} (ID: {d.id}) into Target...")
                
                # Move Items
                MenuItem.objects.filter(course=d).update(course=target_dessert)
                
                # Update Fixed Menus - ManyToMany
                # We need to add the target to any menu that has the duplicate, then remove the duplicate
                menus = FixedCateringMenu.objects.filter(courses=d)
                for menu in menus:
                    menu.courses.add(target_dessert)
                    menu.courses.remove(d)
                    
                # Delete duplicate
                d.delete()
                print("    Merged and Deleted.")

    # --- Main Courses ---
    all_mains = Course.objects.filter(name__icontains="Main Course")
    # We want "Main Courses" usually
    target_main = None
    for m in all_mains:
        img_str = str(m.image)
        if m.name == "Main Courses" and img_str and "placeholder" not in img_str:
            target_main = m
            break
            
    if not target_main:
         target_main = all_mains.filter(name="Main Courses").first()
         
    if target_main:
        print(f"Target Main Course: {target_main.name} (ID: {target_main.id})")
        for m in all_mains:
            if m.id != target_main.id:
                # Be careful not to merge things that are genuinely different if specific naming was intended
                # But here "Main Course" vs "Main Courses" is likely a typo variance
                if m.name in ["Main Course", "Main Dish"]:
                    print(f"  Merging {m.name} (ID: {m.id}) into Target...")
                    MenuItem.objects.filter(course=m).update(course=target_main)
                    menus = FixedCateringMenu.objects.filter(courses=m)
                    for menu in menus:
                        menu.courses.add(target_main)
                        menu.courses.remove(m)
                    m.delete()

    print("Merge Complete.")

if __name__ == "__main__":
    merge_courses()
