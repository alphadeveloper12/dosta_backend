import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dosta.settings')
django.setup()

from catering.models import CanapeItem, ServiceStyle, ServiceStylePrivate, Cuisine, BudgetOption, Pax

def populate_canapes():
    print("Deleting 'Canape' Cuisine...")
    Cuisine.objects.filter(name__icontains="Canape").delete()

    print("Creating/Updating 'Canape' Service Styles...")
    ss, _ = ServiceStyle.objects.get_or_create(name="Canape", defaults={'min_pax': 10})
    ssp, _ = ServiceStylePrivate.objects.get_or_create(name="Canape", defaults={'min_pax': 10})
    
    # Define specific Canape budgets
    canape_budgets_data = [
        {"label": "Standard", "price_range": "70 AED"},
        {"label": "Premium", "price_range": "85 AED"},
        {"label": "Gold", "price_range": "100 AED"},
        {"label": "Platinum", "price_range": "120 AED"},
        {"label": "Royal", "price_range": "135 AED"},
    ]
    
    canape_budgets = []
    for b_data in canape_budgets_data:
        budget, _ = BudgetOption.objects.get_or_create(
            price_range=b_data["price_range"],
            defaults={"label": b_data["label"]}
        )
        canape_budgets.append(budget)

    # Link ONLY these budgets to Canape styles
    ss.budget_options.set(canape_budgets)
    ssp.budget_options.set(canape_budgets)
    print("Linked Specific Canape BudgetOptions to Canape Service Styles.")

    # Link all Pax options to these styles
    pax_options = Pax.objects.all()
    # Pax models have 'service_styles' and 'service_styles_private' M2M fields
    # We need to add the service style to the pax option's M2M field, 
    # OR add the pax options to the service style if the M2M is defined on ServiceStyle.
    # Looking at models.py: Pax has:
    # service_styles = models.ManyToManyField(ServiceStyle, blank=True, related_name='pax_options')
    # service_styles_private = models.ManyToManyField('ServiceStylePrivate', blank=True, related_name='pax_options')
    
    # So we must add the style to the Pax object.
    for pax in pax_options:
        pax.service_styles.add(ss)
        pax.service_styles_private.add(ssp)
        pax.save()
    
    print("Linked Pax Options to Canape Service Styles.")

    print("Clearing existing Canape Items...")
    CanapeItem.objects.all().delete()

    canapes = [
        # Cold Canapes
        {"name": "Smoked Salmon on Blinis", "category": "Cold"},
        {"name": "Caprese Skewers", "category": "Cold"},
        {"name": "Cucumber Cups with Hummus", "category": "Cold"},
        {"name": "Chicken Liver Pâté on Crostini", "category": "Cold"},
        {"name": "Bruschetta with Tomato and Basil", "category": "Cold"},
        {"name": "Tuna Tartare on Rice Crackers", "category": "Cold"},
        {"name": "Chilled Shrimp Cocktail", "category": "Cold"},
        {"name": "Prosciutto and Melon Bites", "category": "Cold"},
        {"name": "Roasted Red Pepper and Goat Cheese Bites", "category": "Cold"},
        {"name": "Mini Gazpacho Shots", "category": "Cold"},
        {"name": "Deviled Eggs with Herbs", "category": "Cold"},
        {"name": "Antipasto Skewers", "category": "Cold"},
        {"name": "Cheese and Charcuterie Platter", "category": "Cold"},
        {"name": "Smoked Trout Mousse on Toast", "category": "Cold"},
        {"name": "Marinated Olives", "category": "Cold"},
        {"name": "Caprese Salad in a Cup", "category": "Cold"},
        {"name": "Savory Palmiers with Spinach", "category": "Cold"},
        {"name": "Chilled Asparagus with Lemon Zest", "category": "Cold"},
        {"name": "Mini Sushi Rolls", "category": "Cold"},
        {"name": "Stuffed Cherry Tomatoes", "category": "Cold"},

        # Hot Canapes
        {"name": "Mini Beef Wellington", "category": "Hot"},
        {"name": "Stuffed Mushrooms", "category": "Hot"},
        {"name": "Vegetable Spring Rolls", "category": "Hot"},
        {"name": "Chicken Satay Skewers", "category": "Hot"},
        {"name": "Spinach and Feta Puff Pastry Bites", "category": "Hot"},
        {"name": "Mini Quiches", "category": "Hot"},
        {"name": "Crispy Calamari with Aioli", "category": "Hot"},
        {"name": "Zucchini Fritters with Tzatziki", "category": "Hot"},
        {"name": "Eggplant Parmesan Bites", "category": "Hot"},
        {"name": "Spicy Lamb Kofta Skewers", "category": "Hot"},
        {"name": "Pulled Lamb Sliders", "category": "Hot"},
        {"name": "Buffalo Cauliflower Bites", "category": "Hot"},
        {"name": "Cheese-Stuffed Jalapeño Poppers", "category": "Hot"},
        {"name": "Savory Meatballs in Marinara", "category": "Hot"},
        {"name": "Baked Brie with Jam", "category": "Hot"},
        {"name": "Mini Corn Dogs", "category": "Hot"},
        {"name": "Chicken and Apple Sausage Rolls", "category": "Hot"},
        {"name": "Vegetarian Samosas", "category": "Hot"},
        {"name": "Crab Cakes with Remoulade", "category": "Hot"},
        {"name": "Spinach Artichoke Dip Bites", "category": "Hot"},

        # Arabic Canapes
        {"name": "Hummus and Pita Chips", "category": "Arabic"},
        {"name": "Falafel Bites with Tahini Sauce", "category": "Arabic"},
        {"name": "Stuffed Grape Leaves (Dolma)", "category": "Arabic"},
        {"name": "Mini Kebabs (Chicken or Lamb)", "category": "Arabic"},
        {"name": "Shakshuka in Mini Cups", "category": "Arabic"},
        {"name": "Labneh with Olive Oil and Za'atar", "category": "Arabic"},
        {"name": "Muhammara on Bread", "category": "Arabic"},
        {"name": "Baba Ganoush with Veggie Sticks", "category": "Arabic"},
        {"name": "Mini Spinach and Cheese Fatayers", "category": "Arabic"},
        {"name": "Sambousek (Savory Pastry) with Meat or Cheese", "category": "Arabic"},
        {"name": "Tabbouleh Salad in Cucumber Cups", "category": "Arabic"},
        {"name": "Kibbeh Balls with Yogurt Dip", "category": "Arabic"},
        {"name": "Roasted Eggplant Rolls with Feta", "category": "Arabic"},
        {"name": "Mini Pita Sandwiches with Shawarma", "category": "Arabic"},
        {"name": "Zucchini Fritters with Yogurt Sauce", "category": "Arabic"},
        {"name": "Chickpea Salad Skewers", "category": "Arabic"},
        {"name": "Spiced Carrot and Walnut Bites", "category": "Arabic"},
        {"name": "Mini Manakish (Za'atar Bread)", "category": "Arabic"},
        {"name": "Baklava Bites", "category": "Arabic"},
        {"name": "Rosewater and Pistachio Mousse Cups", "category": "Arabic"},

        # Sweet Canapes
        {"name": "Mini Chocolate Eclairs", "category": "Sweet"},
        {"name": "Fruit Tartlets", "category": "Sweet"},
        {"name": "Macarons", "category": "Sweet"},
        {"name": "Mini Cheesecakes", "category": "Sweet"},
        {"name": "Panna Cotta Cups", "category": "Sweet"},
        {"name": "Chocolate-dipped Strawberries", "category": "Sweet"},
        {"name": "Brownie Bites with Ganache", "category": "Sweet"},
        {"name": "Mini Pavlovas with Fresh Berries", "category": "Sweet"},
        {"name": "Tiramisu Cups", "category": "Sweet"},
        {"name": "Caramel Apple Bites", "category": "Sweet"},
        {"name": "Lemon Curd Tartlets", "category": "Sweet"},
        {"name": "Peach Melba Cups", "category": "Sweet"},
        {"name": "Raspberry Fool in Shot Glasses", "category": "Sweet"},
        {"name": "Mini Fruit Kebabs", "category": "Sweet"},
        {"name": "Banoffee Bites", "category": "Sweet"},
        {"name": "Chocolate Mousse Cups", "category": "Sweet"},
        {"name": "Pineapple Upside Down Bites", "category": "Sweet"},

        # Vegetarian Canapes
        {"name": "Hummus and Veggie Cups", "category": "Vegetarian"},
        {"name": "Caprese Salad Bites", "category": "Vegetarian"},
        {"name": "Stuffed Peppadews with Cream Cheese", "category": "Vegetarian"},
        {"name": "Mini Grilled Cheese Sandwiches", "category": "Vegetarian"},
        {"name": "Roasted Beet and Goat Cheese Bites", "category": "Vegetarian"},
        {"name": "Falafel Balls with Tahini Dip", "category": "Vegetarian"},
        {"name": "Vegetable Tempura", "category": "Vegetarian"},
        {"name": "Spinach and Ricotta Stuffed Pasta Shells", "category": "Vegetarian"},
        {"name": "Savory Scones with Cheese and Chives", "category": "Vegetarian"},
        {"name": "Mushroom and Spinach Tartlets", "category": "Vegetarian"},
        {"name": "Crispy Vegetable Spring Rolls", "category": "Vegetarian"},
        {"name": "Stuffed Zucchini Boats", "category": "Vegetarian"},
        {"name": "Bruschetta with Avocado", "category": "Vegetarian"},
        {"name": "Mini Vegetable Fritattas", "category": "Vegetarian"},
        {"name": "Cucumber Sandwiches", "category": "Vegetarian"},
        {"name": "Roasted Cauliflower Bites", "category": "Vegetarian"},
        {"name": "Savory Oatmeal Bites", "category": "Vegetarian"},
        {"name": "Vegetable Sushi Rolls", "category": "Vegetarian"},
        {"name": "Mini Caprese Salad Stacks", "category": "Vegetarian"},
        {"name": "Cheese and Chutney on Crackers", "category": "Vegetarian"},

        # Cold Beverages
        {"name": "Sparkling Water with Citrus", "category": "Cold Beverages"},
        {"name": "Iced Tea with Mint", "category": "Cold Beverages"},
        {"name": "Lemonade", "category": "Cold Beverages"},
        {"name": "Cucumber Mint Cooler", "category": "Cold Beverages"},
        {"name": "Fruit-Infused Water", "category": "Cold Beverages"},
        {"name": "Iced Coffee", "category": "Cold Beverages"},
        {"name": "Coconut Water", "category": "Cold Beverages"},
        {"name": "Smoothie Shots", "category": "Cold Beverages"},
        {"name": "Fresh Fruit Juices", "category": "Cold Beverages"},
        {"name": "Pineapple Mint Spritzer", "category": "Cold Beverages"},
        {"name": "Berry Lemonade", "category": "Cold Beverages"},
        {"name": "Chilled Green Tea", "category": "Cold Beverages"},
        {"name": "Ginger Ale", "category": "Cold Beverages"},
        {"name": "Sparkling Apple Cider", "category": "Cold Beverages"},
        {"name": "Herbal Iced Tea", "category": "Cold Beverages"},

        # Hot Beverages
        {"name": "Coffee", "category": "Hot Beverages"},
        {"name": "Tea (various flavors)", "category": "Hot Beverages"},
        {"name": "Hot Chocolate", "category": "Hot Beverages"},
        {"name": "Chai Latte", "category": "Hot Beverages"},
        {"name": "Spiced Apple Cider", "category": "Hot Beverages"},
        {"name": "Herbal Infusions", "category": "Hot Beverages"},
        {"name": "Turmeric Latte", "category": "Hot Beverages"},
        {"name": "Warm Lemon Ginger Tea", "category": "Hot Beverages"},
        {"name": "Hot Buttered Rum", "category": "Hot Beverages"},
        {"name": "Peppermint Hot Chocolate", "category": "Hot Beverages"},
        {"name": "Cinnamon Spice Tea", "category": "Hot Beverages"},
        {"name": "Warm Vanilla Milk", "category": "Hot Beverages"},
        {"name": "Caramel Apple Cider", "category": "Hot Beverages"},
        {"name": "Lemon Verbena Tea", "category": "Hot Beverages"},
        {"name": "Chai Spiced Hot Milk", "category": "Hot Beverages"},
    ]

    print("Populating Canape Items...")
    for data in canapes:
        CanapeItem.objects.create(
            name=data['name'],
            category=data['category'],
            description=f"Delicious {data['name'].lower()}"
        )
        print(f"Created: {data['name']}")

    print("Population complete.")

if __name__ == '__main__':
    populate_canapes()
