from django.urls import path
from .views import (
    AgentChatView, ScrapedLeadView, 
    CustomerInquiryView, CustomerServiceTicketView, ConversationStateView,
    AgentStatusView, ToggleAgentPauseView,
    WhatsAppDeviceStatusView, WhatsAppDeviceResetView, WhatsAppDeviceStartView, WhatsAppMediaUploadView,
    WhatsAppMediaListView, WhatsAppMediaServeView, WhatsAppMediaDeleteView,
    TriggerScrapeView, ScraperProgressView,
    AgentConfigListView, AgentConfigDetailView, AIGlobalSettingView
)

urlpatterns = [
    path('chat/', AgentChatView.as_view(), name='agent-chat'),
    path('leads/', ScrapedLeadView.as_view(), name='agent-leads'),
    path('inquiries/', CustomerInquiryView.as_view(), name='customer-inquiries'),
    path('tickets/', CustomerServiceTicketView.as_view(), name='customer-tickets'),
    path('state/<str:phone>/', ConversationStateView.as_view(), name='conversation-state'),
    path('status/<str:agent_id>/', AgentStatusView.as_view(), name='agent-status'),
    path('toggle-pause/<str:agent_id>/', ToggleAgentPauseView.as_view(), name='agent-toggle-pause'),
    path('whatsapp/status/', WhatsAppDeviceStatusView.as_view(), name='whatsapp-status'),
    path('whatsapp/reset/', WhatsAppDeviceResetView.as_view(), name='whatsapp-reset'),
    path('whatsapp/start/', WhatsAppDeviceStartView.as_view(), name='whatsapp-start'),
    path('whatsapp/upload/', WhatsAppMediaUploadView.as_view(), name='whatsapp-upload'),
    path('whatsapp/media/list/', WhatsAppMediaListView.as_view(), name='whatsapp-media-list'),
    path('whatsapp/media/view/<str:filename>/', WhatsAppMediaServeView.as_view(), name='whatsapp-media-view'),
    path('whatsapp/media/delete/<str:filename>/', WhatsAppMediaDeleteView.as_view(), name='whatsapp-media-delete'),
    path('scraper/trigger/', TriggerScrapeView.as_view(), name='scraper-trigger'),
    path('scraper/progress/', ScraperProgressView.as_view(), name='scraper-progress'),
    path('config/', AgentConfigListView.as_view(), name='agent-config-list'),
    path('config/<str:agent_type>/', AgentConfigDetailView.as_view(), name='agent-config-detail'),
    path('settings/', AIGlobalSettingView.as_view(), name='ai-global-settings'),
]
