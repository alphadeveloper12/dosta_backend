from django.db import models

class AgentActivity(models.Model):
    agent_id = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=50, default='Active')
    is_paused = models.BooleanField(default=False)
    last_task = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.agent_id} - {self.status}"

class AgentInteractionLog(models.Model):
    agent_id = models.CharField(max_length=50)
    phone = models.CharField(max_length=50, blank=True, null=True)
    user_message = models.TextField()
    ai_response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.agent_id} for {self.phone} at {self.timestamp}"

class ScrapedLead(models.Model):
    STATUS_CHOICES = (
        ('New', 'New'),
        ('Contacted', 'Contacted'),
        ('Failed', 'Failed'),
    )
    company_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='New')
    source = models.CharField(max_length=255, blank=True, null=True)
    date_scraped = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.company_name} - {self.phone_number} ({self.status})"

class CustomerInquiry(models.Model):
    """Leads captured by the Sales Agent (Chef Ammar Digital Assistant)"""
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50)
    preference = models.CharField(max_length=255, help_text="Event Type or Menu selection")
    event_date = models.CharField(max_length=100, blank=True, null=True)
    event_time = models.CharField(max_length=100, blank=True, null=True)
    people_count = models.CharField(max_length=100, blank=True, null=True)
    venue = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Customer Inquiries"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.name} - {self.preference} ({self.timestamp.strftime('%Y-%m-%d')})"

class CustomerServiceTicket(models.Model):
    """Complaints or suggestions captured by the CS Agent"""
    STATUS_CHOICES = (
        ('Open', 'Open'),
        ('Resolved', 'Resolved'),
    )
    phone = models.CharField(max_length=50)
    subject = models.CharField(max_length=255, default="Complaint/Suggestion")
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ticket from {self.phone} - {self.status}"

class ConversationState(models.Model):
    """Tracks the state of a WhatsApp conversation for multi-step flows"""
    phone = models.CharField(max_length=50, unique=True)
    state = models.CharField(max_length=100, default='START')
    language = models.CharField(max_length=20, blank=True, null=True)  # 'en' or 'ar'
    agent_type = models.CharField(max_length=50, blank=True, null=True) # 'sales' or 'support'
    context_data = models.JSONField(default=dict, blank=True) # For partial lead data
    loop_counter = models.IntegerField(default=0)
    is_bot = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.phone} - {self.state}"

class WhatsAppDevice(models.Model):
    """Tracks the status of the WhatsApp Gateway (QR, Connected, etc.)"""
    phone_number = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=50, default='DISCONNECTED') # DISCONNECTED, QR_READY, CONNECTED
    qr_code = models.TextField(blank=True, null=True) # Base64 image
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"WhatsApp Gateway ({self.status}) - {self.phone_number or 'Unlinked'}"

class ScraperStatus(models.Model):
    """Tracks the progress of the automated lead scraper"""
    is_running = models.BooleanField(default=False)
    progress_percentage = models.IntegerField(default=0)
    current_source = models.CharField(max_length=255, blank=True, null=True)
    leads_found = models.IntegerField(default=0)
    last_run_time = models.DateTimeField(auto_now=True)
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Scraper {'Running' if self.is_running else 'Idle'} - {self.progress_percentage}%"

class ScraperSchedule(models.Model):
    """Configuration for daily scraping"""
    run_time = models.TimeField(default="09:00:00")
    is_enabled = models.BooleanField(default=True)
    last_automated_run = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Daily Scrape at {self.run_time} ({'Enabled' if self.is_enabled else 'Disabled'})"

class MarketingReport(models.Model):
    """Stores the daily AI-generated marketing analysis based on ad platform stats"""
    date = models.DateField(auto_now_add=True)
    meta_spend = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    google_spend = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    ai_analysis_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Marketing Report - {self.date}"

class AgentConfiguration(models.Model):
    """Stores dynamic prompts and seasonal knowledge for each agent type"""
    agent_type = models.CharField(max_length=50, unique=True, help_text="e.g., sales, customer_service")
    name = models.CharField(max_length=255, help_text="The display name of the agent")
    role = models.TextField(help_text="The primary system persona/role definition")
    knowledge = models.TextField(blank=True, null=True, help_text="Specific background knowledge, current deals, menu changes, etc.")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Config: {self.name} ({self.agent_type})"

class AIGlobalSetting(models.Model):
    """Global AI settings like API keys"""
    key = models.CharField(max_length=50, unique=True)
    value = models.TextField()
    description = models.CharField(max_length=255, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Setting: {self.key}"
class AdDraft(models.Model):
    """Stores AI-suggested ads for admin approval before going live"""
    STATUS_CHOICES = (
        ('Draft', 'Draft'),
        ('Pending Approval', 'Pending Approval'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Live', 'Live'),
        ('Failed', 'Failed'),
    )
    PLATFORM_CHOICES = (
        ('Meta', 'Meta (Facebook/Instagram)'),
        ('Google', 'Google Ads'),
    )
    
    agent_id = models.CharField(max_length=50, default="marketing")
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    headline = models.CharField(max_length=255)
    body_text = models.TextField()
    targeting_summary = models.TextField(help_text="Human-readable targeting description")
    targeting_data = models.JSONField(default=dict, blank=True, help_text="Raw API targeting parameters")
    budget = models.DecimalField(max_digits=10, decimal_places=2, help_text="Daily budget in AED")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending Approval')
    rejection_reason = models.TextField(blank=True, null=True)
    platform_ad_id = models.CharField(max_length=100, blank=True, null=True, help_text="ID returned by Meta/Google after going live")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.platform} Ad: {self.headline[:30]}... ({self.status})"
