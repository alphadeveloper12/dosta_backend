import os, json, re, openai
from django.core.mail import send_mail
from django.conf import settings
from ai_agents.context import get_catering_context, get_vending_context, get_accounting_context, get_sales_context, get_support_context
from ai_agents.models import AgentActivity, AgentInteractionLog

class AgentService:
    @staticmethod
    def log_activity(agent_id, status, last_task=None):
        activity, created = AgentActivity.objects.get_or_create(agent_id=agent_id)
        activity.status = status
        if last_task:
            activity.last_task = last_task
        activity.save()

    @staticmethod
    def send_whatsapp_message(phone, message):
        """Sends a WhatsApp message via the outbound Node.js gateway"""
        import requests
        try:
            # The bot listens on port 3001
            url = "http://127.0.0.1:3001/send"
            response = requests.post(url, json={
                "phone": phone,
                "message": message
            }, timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to send WhatsApp message: {str(e)}")
            return False

    @staticmethod
    def alert_human_team(agent_type, user_message, ai_response):
        admin_email = getattr(settings, 'ADMIN_EMAIL', 'info@dosta.ae')
        admin_phone = getattr(settings, 'ADMIN_PHONE', '971509171092') # Default admin phone if not in env
        
        subject = f"AI Escalation: {agent_type}"
        email_body = f"AI interaction requires review.\n\nMsg: {user_message}\n\nAI: {ai_response}"
        
        # 1. Email Alert
        try:
            send_mail(subject, email_body, settings.DEFAULT_FROM_EMAIL, [admin_email], fail_silently=True)
        except: pass

        # 2. WhatsApp Alert
        ws_msg = f"🔔 *AI ALERT ({agent_type})*\n\n*User:* {user_message}\n\n*AI:* {ai_response}\n\nReview: https://dosta.ae/kitchen/agents/"
        AgentService.send_whatsapp_message(admin_phone, ws_msg)


    @staticmethod
    def get_agent_config(agent_type):
        from ai_agents.models import AgentConfiguration
        try:
            config_obj = AgentConfiguration.objects.get(agent_type=agent_type)
            return {
                "name": config_obj.name,
                "role": config_obj.role,
                "knowledge": config_obj.knowledge,
                "context_func": AgentService._get_context_func(agent_type)
            }
        except AgentConfiguration.DoesNotExist:
            # Fallback to defaults
            configs = {
                "sales": {
                    "name": "Dosta Assistant (under Chef Ammar Alekili)",
                    "role": """You are the digital representation of the culinary excellence at Dosta, guided by our Director of Culinary & Operation, Chef Ammar Alekili. 
    With his 25+ years of experience in luxury hospitality and high-end catering, you assist customers in crafting the perfect event menus and experiencing the best of Dosta's culinary offerings.""",
                    "knowledge": "",
                    "context_func": get_sales_context
                },
                "customer_service": {
                    "name": "Dosta Support Specialist",
                    "role": "You are a helpful and empathetic Customer Service agent for Dosta.",
                    "knowledge": "",
                    "context_func": get_support_context
                }
            }
            default = configs.get(agent_type, configs["customer_service"])
            return default

    @staticmethod
    def _get_context_func(agent_type):
        funcs = {
            "sales": get_sales_context,
            "customer_service": get_support_context,
            "lead_gen": get_vending_context,
            "marketing": get_catering_context,
            "accounting": get_accounting_context
        }
        return funcs.get(agent_type, get_support_context)

    @staticmethod
    def get_api_key():
        from ai_agents.models import AIGlobalSetting
        try:
            setting = AIGlobalSetting.objects.get(key='OPENAI_API_KEY')
            return setting.value
        except AIGlobalSetting.DoesNotExist:
            return os.getenv("OPENAI_API_KEY")

    @staticmethod
    def chat(agent_type, user_message, chat_history=None, **kwargs):
        openai.api_key = AgentService.get_api_key()
        config = AgentService.get_agent_config(agent_type)
        
        # Log processing state
        AgentService.log_activity(agent_type, "Processing", f"Working on: {user_message[:50]}...")
        
        context = config["context_func"]()
        
        system_prompt = f"""
{config['role']}

### SPECIALIZED KNOWLEDGE & CURRENT OFFERS:
{config.get('knowledge', 'No seasonal knowledge provided.')}

### DATA CONTEXT FOR YOUR ROLE:
{context}

### GENERAL DOSTA GUIDELINES:
- Be professional, UAE-centric, and helpful.
- **ANTI-REPETITION:** DO NOT repeat your introduction, Chef Ammar's bio, or his accomplishments if you have already said them once in the conversation. Focus ONLY on answering the user's latest question.
- **STRICT THREE-STEP FLOW (WITH FLEXIBILITY):**
    1. **Acknowledge Inputs**: If the user sends a link (Instagram, Facebook, etc.) or a mention of a "story", acknowledge it immediately. Say something like: "I see you're interested in our recent post! I'm here to provide more details."
    2. **Event Selection**: After acknowledging, if the user hasn't chosen (Iftar, Sohour, Box, Sweets, Catering), present the 1-5 list. **DO NOT include any links or URLs in this list.**
    3. **Selection Flow**:
        - **IF IFTAR (1), SOHOUR (2), or BOX (3)**: You MUST ask them to choose between specific menus or boxes.
        - **IF SWEETS (4)**: Present the sweets list from the context and provide the ordering link: https://dosta.ae/dosta-sweets. Then ask if they want to proceed with an order or have questions.
        - **IF CATERING (5)**: You MUST reply ONLY with the plain URL: https://dosta.ae/catering/plan - Do not add any text, introduction, or duplicate URLs.
    4. **Lead Capture**: ONLY after they have confirmed a specific Menu or expressed interest in an order, you then ask for Name, Email, Date, Time, People, and Venue.
- **GENERAL RESPONSIVENESS:** You MUST respond to EVERY message from any number. Never ignore a message even if it only contains a link. Always be helpful and proactive.
- **URL FORMATTING:** Never use markdown links like [label](url). Always use plain URLs (e.g., https://example.com).
- **MENU DETAILS (Iftar/Sohour):** When presenting menus, use the exhaustive item lists in the context.
- If you don't know something, suggest contacting info@dosta.ae.
- Always maintain your specific persona as a {config['name']}.

### SPECIAL DATA CAPTURE COMMANDS:
If you are a Sales agent and have collected ALL required fields (Name, Email, Date, Time, People count, Venue), append the following tag to your message:
[LEAD_DATA]{{"name": "...", "email": "...", "date": "...", "time": "...", "people": "...", "venue": "...", "preference": "..."}}[/LEAD_DATA]

If you are a Customer Service agent and have captured a clear complaint or suggestion, append:
[TICKET_DATA]{{"subject": "...", "message": "..."}}[/TICKET_DATA]

### CONVERSATION CONTROL:
If you detect that you are communicating with another automated bot, or if the user explicitly asks to stop/unsubscribe or shows no interest after multiple attempts, append the following tag to end the loop:
[STOP_CHAT]
"""
        
        # --- FETCH HISTORY IF NOT PROVIDED ---
        phone = kwargs.get('phone', 'Unknown')
        if not chat_history and phone != 'Unknown':
            past_logs = AgentInteractionLog.objects.filter(phone=phone, agent_id=agent_type).order_by('-timestamp')[:10]
            # Need to reverse so it's in chronological order
            chat_history = []
            for log in reversed(past_logs):
                chat_history.append({"role": "user", "content": log.user_message})
                chat_history.append({"role": "assistant", "content": log.ai_response})

        messages = [{"role": "system", "content": system_prompt}]
        if chat_history:
            messages.extend(chat_history)
        messages.append({"role": "user", "content": user_message})

        try:
            client = openai.OpenAI(api_key=openai.api_key)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=800,
                temperature=0.7
            )
            reply = response.choices[0].message.content
            
            # Hard-enforce minimal catering response if link is present and it's a sales agent
            if agent_type == "sales" and ("catering/plan" in reply.lower() or "5" == user_message.strip()):
                reply = "For bespoke catering and full event coordination, please visit our planning portal: https://dosta.ae/catering/plan\n\nYou can outline your event details there, and Chef Ammar’s team will respond with tailored menus, décor, and service options. If you’d like me to guide you through the form or capture details here first, just let me know."

            # --- POST-PROCESSING: STRIP MARKDOWN LINKS ---
            # Convert [text](url) to just url
            reply = re.sub(r"\[.*?\]\((https?://.*?)\)", r"\1", reply)

            # --- DATA EXTRACTION LOGIC ---
            from ai_agents.models import CustomerInquiry, CustomerServiceTicket

            # 1. Check for Lead Data
            lead_match = re.search(r"\[LEAD_DATA\](.*?)\[/LEAD_DATA\]", reply, re.DOTALL)
            if lead_match:
                try:
                    data = json.loads(lead_match.group(1))
                    CustomerInquiry.objects.create(
                        name=data.get('name'),
                        email=data.get('email'),
                        phone=kwargs.get('phone', 'Unknown'), # We'll need to pass phone to chat()
                        preference=data.get('preference'),
                        event_date=data.get('date'),
                        event_time=data.get('time'),
                        people_count=data.get('people'),
                        venue=data.get('venue')
                    )
                    reply = reply.replace(lead_match.group(0), "").strip() # Clean the tag from user view
                except: pass

            # 2. Check for Ticket Data
            ticket_match = re.search(r"\[TICKET_DATA\](.*?)\[/TICKET_DATA\]", reply, re.DOTALL)
            if ticket_match:
                try:
                    data = json.loads(ticket_match.group(1))
                    CustomerServiceTicket.objects.create(
                        phone=kwargs.get('phone', 'Unknown'),
                        subject=data.get('subject'),
                        message=data.get('message')
                    )
                    reply = reply.replace(ticket_match.group(0), "").strip()
                except: pass
            
            # Save the full transcript
            AgentInteractionLog.objects.create(
                agent_id=agent_type,
                phone=kwargs.get('phone', 'Unknown'),
                user_message=user_message,
                ai_response=reply
            )

            # Check if we should notify human team
            AgentService.alert_human_team(agent_type, user_message, reply)

            # Log completed state
            AgentService.log_activity(agent_type, "Active", user_message)
            
            return reply
        except Exception as e:
            AgentService.log_activity(agent_type, "Error", str(e))
            return f"Error: {str(e)}"
