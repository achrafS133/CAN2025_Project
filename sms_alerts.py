import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

def send_threat_alert(threat_type, location="Entrance Gate 5"):
    """
    Sends an SMS alert to the security team using Twilio when a threat is detected.
    """
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_PHONE_NUMBER')
    to_number = os.getenv('RECIPIENT_PHONE_NUMBER')

    if not all([account_sid, auth_token, from_number, to_number]):
        print("⚠️ Twilio credentials missing. SMS alert not sent.")
        return False

    try:
        client = Client(account_sid, auth_token)
        message_body = f"🚨 CAN 2025 SECURITY ALERT!\nThreat: {threat_type.upper()} detected!\nLocation: {location}\nTimestamp: {os.uname().nodename if hasattr(os, 'uname') else 'Command Center'}"
        
        message = client.messages.create(
            body=message_body,
            from_=from_number,
            to=to_number
        )
        print(f"✅ SMS Alert sent. SID: {message.sid}")
        return True
    except Exception as e:
        print(f"❌ Failed to send SMS: {str(e)}")
        return False
