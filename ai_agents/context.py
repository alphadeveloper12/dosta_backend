from catering.models import ServiceStyle, BudgetOption, EventType
from vending.models import VendingLocation, MenuItem as VendingMenuItem
from django.db.models import Min, Max

def get_catering_context():
    """Extracts catering service styles, pricing, and event types."""
    styles = ServiceStyle.objects.all()
    budgets = BudgetOption.objects.all()
    events = EventType.objects.all()
    
    context = "### Dosta Catering Information\n"
    context += "#### Event Types we cater for:\n"
    for e in events:
        context += f"- {e.name}: {e.description or 'Custom solutions available'}\n"
        
    context += "\n#### Service Styles:\n"
    for s in styles:
        context += f"- {s.name}: Min Pax {s.min_pax}. {s.description or ''}\n"
        
    context += "\n#### Budget Options (Per Person):\n"
    for b in budgets:
        context += f"- {b.label}: {b.price_range} (Min: AED {b.min_price})\n"
        
    return context

def get_vending_context():
    """Extracts vending locations and current menu items."""
    locations = VendingLocation.objects.filter(is_active=True)
    menu_items = VendingMenuItem.objects.all()[:20]  # Limit to 20 items for context size
    
    context = "### Dosta Vending Information\n"
    context += "#### Strategic Locations:\n"
    for loc in locations:
        context += f"- {loc.name}: {loc.info}. Hours: {loc.hours or '24/7'}\n"
        
    context += "\n#### Popular Menu Items & Pricing:\n"
    for item in menu_items:
        context += f"- {item.name}: AED {item.price}. {item.description or ''}\n"
        
    return context

import os

def load_knowledge(filename):
    """Reads a markdown file from the knowledge directory."""
    base_path = os.path.dirname(__file__)
    file_path = os.path.join(base_path, 'knowledge', filename)
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return f.read()
    return ""

def get_sales_context():
    """Extracts Chef Ammar's specialized menus and pricing from knowledge files."""
    identity = load_knowledge('IDENTITY.md')
    soul = load_knowledge('SOUL.md')
    menus = load_knowledge('ramadan_menus.md')
    cv = load_knowledge('chef_cv.md')
    
    context = "### SALES AGENT BRAIN (Chef Ammar Digital Assistant)\n"
    context += f"#### Identity:\n{identity}\n"
    context += f"#### Soul & Persona:\n{soul}\n"
    context += f"#### Chef CV:\n{cv}\n"
    context += f"#### Ramadan Menus & Pricing:\n{menus}\n"
    
    context += "\n#### LEAD CAPTURE MANDATORY FIELDS:\n"
    context += "You must collect: Name, Email, Date, Time, Number of People, and Venue Details to finalize any inquiry.\n"
    return context

def get_accounting_context():
    """Mock accounting context for demonstration - can be expanded with real invoice logic."""
    return "### Accounting Assistance Information\n- Standard payment terms: 50% upfront for catering, 50% on delivery.\n- We accept Bank Transfer, Credit Card, and Cheque.\n- Refund policy: Full refund if cancelled 72 hours before the event.\n"

def get_support_context():
    """Context for general customer support, complaints and vending issues."""
    vending_data = get_vending_context()
    context = "### Dosta Customer Support Context\n"
    context += "#### Support Hours:\n09:00 AM - 06:00 PM (Monday to Saturday)\n"
    context += "#### Escalation Policy:\n"
    context += "- For missing items in vending machines: Ask for the Machine ID and Item name. Inform them a refund will be processed within 24 hours.\n"
    context += "- For catering issues: Collect the order date and contact details. Inform them the culinary team will review and call them back.\n"
    context += "\n" + vending_data
    return context
