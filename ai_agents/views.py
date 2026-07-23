from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import FileResponse, Http404
import threading
import socket
import subprocess
import os
import signal
from rest_framework.permissions import AllowAny
from .services.agent_service import AgentService

class AgentChatView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        agent_type = request.data.get('agent_type', 'customer_service')
        user_message = request.data.get('message')
        chat_history = request.data.get('history', [])
        phone = request.data.get('phone') or request.data.get('phone_number', 'Unknown')

        print(f"[*] AgentChatView request: phone={phone}, agent={agent_type}, message='{user_message}'")
        if not user_message:
            print("[!] Error: user_message is empty")
            return Response({"error": "Message is required"}, status=status.HTTP_400_BAD_REQUEST)

        reply = AgentService.chat(agent_type, user_message, chat_history, phone=phone)
        
        return Response({
            "reply": reply,
            "agent_type": agent_type
        }, status=status.HTTP_200_OK)

from .models import (
    ScrapedLead, CustomerInquiry, CustomerServiceTicket, 
    ConversationState, AgentActivity, WhatsAppDevice, 
    ScraperStatus, ScraperSchedule, AgentConfiguration, AIGlobalSetting
)
import threading
from .scraper.lead_scraper import scrape_leads

class AgentStatusView(APIView):
    """API to get the current pause status of an agent"""
    permission_classes = [AllowAny]

    def get(self, request, agent_id):
        activity, created = AgentActivity.objects.get_or_create(agent_id=agent_id)
        return Response({"agent_id": agent_id, "is_paused": activity.is_paused})

class ToggleAgentPauseView(APIView):
    """API to toggle the pause status of an agent"""
    permission_classes = [AllowAny]

    def post(self, request, agent_id):
        activity, created = AgentActivity.objects.get_or_create(agent_id=agent_id)
        activity.is_paused = not activity.is_paused
        activity.save()
        return Response({
            "agent_id": agent_id,
            "is_paused": activity.is_paused,
            "message": f"Agent {agent_id} {'paused' if activity.is_paused else 'resumed'}"
        })

class ScrapedLeadView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # Fetch up to 100 'New' leads per cycle for scaling
        leads = ScrapedLead.objects.filter(status='New')[:100]
        data = [
            {
                "id": lead.id,
                "company_name": lead.company_name,
                "phone_number": lead.phone_number,
                "source": lead.source
            }
            for lead in leads
        ]
        return Response({"leads": data}, status=status.HTTP_200_OK)

    def post(self, request):
        lead_id = request.data.get('id')
        new_status = request.data.get('status')
        
        if not lead_id or not new_status:
            return Response({"error": "ID and status are required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            lead = ScrapedLead.objects.get(id=lead_id)
            lead.status = new_status
            lead.save()
            return Response({"message": f"Lead {lead_id} updated to {new_status}"}, status=status.HTTP_200_OK)
        except ScrapedLead.DoesNotExist:
            return Response({"error": "Lead not found"}, status=status.HTTP_404_NOT_FOUND)

class CustomerInquiryView(APIView):
    """API for the Sales Agent to save captured lead data"""
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        inquiry = CustomerInquiry.objects.create(
            name=data.get('name'),
            email=data.get('email'),
            phone=data.get('phone'),
            preference=data.get('preference'),
            event_date=data.get('event_date'),
            event_time=data.get('event_time'),
            people_count=data.get('people_count'),
            venue=data.get('venue')
        )
        return Response({"message": "Inquiry saved", "id": inquiry.id}, status=status.HTTP_201_CREATED)

class CustomerServiceTicketView(APIView):
    """API for the CS Agent to save tickets"""
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        ticket = CustomerServiceTicket.objects.create(
            phone=data.get('phone'),
            message=data.get('message'),
            subject=data.get('subject', 'General Complaint/Suggestion')
        )
        return Response({"message": "Ticket created", "id": ticket.id}, status=status.HTTP_201_CREATED)

class ConversationStateView(APIView):
    """API to manage the state of a WhatsApp conversation"""
    permission_classes = [AllowAny]

    def get(self, request, phone):
        state_obj, created = ConversationState.objects.get_or_create(phone=phone)
        return Response({
            "state": state_obj.state,
            "language": state_obj.language,
            "agent_type": state_obj.agent_type,
            "context_data": state_obj.context_data,
            "loop_counter": state_obj.loop_counter,
            "is_bot": state_obj.is_bot
        })

    def post(self, request, phone):
        state_obj, created = ConversationState.objects.get_or_create(phone=phone)
        old_state = state_obj.state
        
        state_obj.state = request.data.get('state', state_obj.state)
        state_obj.language = request.data.get('language', state_obj.language)
        state_obj.agent_type = request.data.get('agent_type', state_obj.agent_type)
        state_obj.context_data = request.data.get('context_data', state_obj.context_data)
        state_obj.loop_counter = request.data.get('loop_counter', state_obj.loop_counter)
        state_obj.is_bot = request.data.get('is_bot', state_obj.is_bot)
        
        # Reset loop counter if state changes (meaning the user provided valid input)
        if old_state != state_obj.state:
            state_obj.loop_counter = 0
            
        state_obj.save()
        return Response({"message": "State updated"})

class WhatsAppDeviceStatusView(APIView):
    """API for the bot to update its gateway status (QR, Number, etc.)"""
    permission_classes = [AllowAny]

    def post(self, request):
        status_val = request.data.get('status')
        qr_code = request.data.get('qr_code')
        phone = request.data.get('phone_number')

        device, _ = WhatsAppDevice.objects.get_or_create(id=1) # Single device for now
        if status_val: device.status = status_val
        if qr_code is not None: device.qr_code = qr_code
        if phone: device.phone_number = phone
        device.save()
        return Response({"message": "Gateway status updated"})

    def get(self, request):
        device, _ = WhatsAppDevice.objects.get_or_create(id=1)
        return Response({
            "status": device.status,
            "phone_number": device.phone_number,
            "qr_code": device.qr_code,
            "updated_at": device.updated_at
        })

class WhatsAppDeviceResetView(APIView):
    """API for the dashboard to trigger a session reset"""
    permission_classes = [AllowAny]

    def post(self, request):
        # Notify the bot to reset
        import requests
        try:
            # The bot will be listening on port 3001 locally for reset triggers
            requests.post("http://127.0.0.1:3001/reset", timeout=5)
        except Exception as e:
            print(f"Error notifying bot: {e}")

        # Update local DB state
        device, _ = WhatsAppDevice.objects.get_or_create(id=1)
        device.status = 'DISCONNECTED'
        device.qr_code = None
        device.phone_number = None
        device.save()
        
        return Response({"message": "Reset command sent to gateway"})

class WhatsAppDeviceStartView(APIView):
    """API to start the WhatsApp bot process if it's not running"""
    permission_classes = [AllowAny]

    def post(self, request):
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 3001))
        if result == 0:
            return Response({"error": "Bot is already running (Port 3001 in use)"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Path to the bot
        bot_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'whatsapp_outbound')
        bot_script = os.path.join(bot_dir, 'index.js')
        
        if not os.path.exists(bot_script):
            return Response({"error": f"Bot script not found at {bot_script}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            # Start the bot in the background
            # We use subprocess.Popen to let it run independently
            log_file = open(os.path.join(bot_dir, 'bot_output.log'), 'a')
            subprocess.Popen(
                ['node', 'index.js'],
                cwd=bot_dir,
                stdout=log_file,
                stderr=log_file,
                preexec_fn=os.setsid # Run in a new session
            )
            return Response({"message": "WhatsApp bot starting... Check the dashboard in a few seconds."})
        except Exception as e:
            return Response({"error": f"Failed to start bot: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class WhatsAppMediaUploadView(APIView):
    """API to upload media files for outreach"""
    permission_classes = [AllowAny]

    def post(self, request):
        if 'file' not in request.FILES:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_file = request.FILES['file']
        
        # Validate file type (simple check)
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.webp', '.mp4']:
            return Response({"error": f"Unsupported file type: {ext}"}, status=status.HTTP_400_BAD_REQUEST)

        # Path to assets
        bot_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'whatsapp_outbound')
        assets_dir = os.path.join(bot_dir, 'outreach_assets')
        
        if not os.path.exists(assets_dir):
            os.makedirs(assets_dir, exist_ok=True)

        # Save the file
        file_path = os.path.join(assets_dir, uploaded_file.name)
        try:
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            return Response({"message": f"Successfully uploaded {uploaded_file.name}"})
        except Exception as e:
            return Response({"error": f"Upload failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class WhatsAppMediaListView(APIView):
    """API to list all uploaded outreach media assets"""
    permission_classes = [AllowAny]

    def get(self, request):
        bot_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'whatsapp_outbound')
        assets_dir = os.path.join(bot_dir, 'outreach_assets')
        
        if not os.path.exists(assets_dir):
            return Response({"media": []})

        files = []
        for f in os.listdir(assets_dir):
            if os.path.isfile(os.path.join(assets_dir, f)) and not f.startswith('.'):
                files.append(f)
        
        return Response({"media": files})

class WhatsAppMediaServeView(APIView):
    """API to securely serve media assets to the dashboard"""
    permission_classes = [AllowAny]

    def get(self, request, filename):
        bot_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'whatsapp_outbound')
        assets_dir = os.path.join(bot_dir, 'outreach_assets')
        file_path = os.path.join(assets_dir, filename)
        
        # Security check: ensure file is within assets_dir
        if not os.path.abspath(file_path).startswith(os.path.abspath(assets_dir)):
            raise Http404("Invalid file path")

        if not os.path.exists(file_path):
            raise Http404("File not found")

        return FileResponse(open(file_path, 'rb'))

class WhatsAppMediaDeleteView(APIView):
    """API to delete an outreach media asset"""
    permission_classes = [AllowAny]

    def delete(self, request, filename):
        bot_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'whatsapp_outbound')
        assets_dir = os.path.join(bot_dir, 'outreach_assets')
        file_path = os.path.join(assets_dir, filename)

        if not os.path.abspath(file_path).startswith(os.path.abspath(assets_dir)):
            return Response({"error": "Invalid file path"}, status=status.HTTP_400_BAD_REQUEST)

        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                return Response({"message": f"Deleted {filename}"})
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({"error": "File not found"}, status=status.HTTP_404_NOT_FOUND)
class TriggerScrapeView(APIView):
    """API to manually trigger the lead scraper in a background thread"""
    permission_classes = [AllowAny]

    def post(self, request):
        status_obj, _ = ScraperStatus.objects.get_or_create(id=1)
        if status_obj.is_running:
            return Response({"error": "Scraper is already running"}, status=status.HTTP_400_BAD_REQUEST)

        # Reset status
        status_obj.is_running = True
        status_obj.progress_percentage = 0
        status_obj.leads_found = 0
        status_obj.error_message = ""
        status_obj.save()

        # Start scraping in a separate thread
        def run_scrape():
            try:
                # This function will need to be updated to report progress to DB
                # For now we use a simple wrapper
                from .scraper.lead_scraper import scrape_leads_with_progress
                scrape_leads_with_progress(status_id=1)
            except Exception as e:
                print(f"[!] Scraper Thread Error: {e}")
                status_obj.is_running = False
                status_obj.error_message = str(e)
                status_obj.save()

        thread = threading.Thread(target=run_scrape)
        thread.daemon = True
        thread.start()

        return Response({"message": "Scraper started successfully"})

class ScraperProgressView(APIView):
    """API to get the current scraping progress"""
    permission_classes = [AllowAny]

    def get(self, request):
        status_obj, _ = ScraperStatus.objects.get_or_create(id=1)
        schedule, _ = ScraperSchedule.objects.get_or_create(id=1)
        return Response({
            "is_running": status_obj.is_running,
            "progress": status_obj.progress_percentage,
            "leads_found": status_obj.leads_found,
            "current_source": status_obj.current_source,
            "last_run": status_obj.last_run_time,
            "error": status_obj.error_message,
            "schedule_time": schedule.run_time.strftime("%H:%M"),
            "schedule_enabled": schedule.is_enabled
        })

class AgentConfigListView(APIView):
    """API to list all available agent configurations"""
    permission_classes = [AllowAny]

    def get(self, request):
        configs = AgentConfiguration.objects.all()
        data = [
            {
                "agent_type": c.agent_type,
                "name": c.name,
                "role": c.role,
                "knowledge": c.knowledge,
                "updated_at": c.updated_at
            }
            for c in configs
        ]
        return Response({"configs": data})

class AgentConfigDetailView(APIView):
    """API to get or update a specific agent configuration"""
    permission_classes = [AllowAny]

    def get(self, request, agent_type):
        try:
            c = AgentConfiguration.objects.get(agent_type=agent_type)
            return Response({
                "agent_type": c.agent_type,
                "name": c.name,
                "role": c.role,
                "knowledge": c.knowledge
            })
        except AgentConfiguration.DoesNotExist:
            return Response({"error": "Configuration not found"}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, agent_type):
        config, created = AgentConfiguration.objects.get_or_create(agent_type=agent_type)
        config.name = request.data.get('name', config.name)
        config.role = request.data.get('role', config.role)
        config.knowledge = request.data.get('knowledge', config.knowledge)
        config.save()
        return Response({"message": f"Configuration for {agent_type} updated successfully"})

class AIGlobalSettingView(APIView):
    """API to manage global AI settings (e.g., API keys)"""
    permission_classes = [AllowAny]

    def get(self, request):
        settings = AIGlobalSetting.objects.all()
        data = {s.key: s.value for s in settings}
        return Response({"settings": data})

    def post(self, request):
        key = request.data.get('key')
        value = request.data.get('value')
        description = request.data.get('description', '')

        if not key or value is None:
            return Response({"error": "Key and value are required"}, status=status.HTTP_400_BAD_REQUEST)

        setting, created = AIGlobalSetting.objects.get_or_create(key=key)
        setting.value = value
        if description:
            setting.description = description
        setting.save()
        return Response({"message": f"Setting {key} updated successfully"})
