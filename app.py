from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from typing import List, Optional
import os
from dotenv import load_dotenv
import asyncio
from datetime import datetime

load_dotenv()

app = FastAPI()

# Setup static files and templates
app.mount("/images", StaticFiles(directory="images"), name="images")
templates = Jinja2Templates(directory="templates")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Email configuration
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT"))
EMAIL = os.getenv("EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# File to track sent emails
SENT_EMAILS_FILE = "sent_emails.json"

# Store email send status
email_status = []
is_sending = False

class EmailRequest(BaseModel):
    batch: str  # "1st_quarter", "2nd_quarter", "3rd_quarter", "4th_quarter"

class EmailStatus(BaseModel):
    name: str
    email: str
    status: str
    timestamp: str

def load_sent_emails() -> List[str]:
    """Load list of already sent email addresses"""
    try:
        with open(SENT_EMAILS_FILE, 'r') as f:
            data = json.load(f)
            return data.get("sent_emails", [])
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []

def save_sent_email(email: str):
    """Save email address to sent list"""
    sent_emails = load_sent_emails()
    if email not in sent_emails:
        sent_emails.append(email)
    
    with open(SENT_EMAILS_FILE, 'w') as f:
        json.dump({"sent_emails": sent_emails}, f, indent=2)

def get_email_template(name: str) -> str:
    """Generate HTML email template with embedded image"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header-image {{
                width: 100%;
                max-width: 600px;
                height: auto;
                margin-bottom: 20px;
            }}
            .greeting {{
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 10px;
            }}
            .button {{
                display: inline-block;
                padding: 12px 24px;
                background-color: #007bff;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .signature {{
                margin-top: 30px;
                font-style: italic;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <img src="cid:header_image" class="header-image" alt="PoolBar Header">
            
            <p class="greeting">Hi {name},</p>
            
            <p>Thanks for stopping by at IAAPA and checking out the PoolBar™ Experience!</p>
            
            <p>We hope you enjoyed seeing how a luxury Inflatable Swim-Up PoolBar™ can elevate any rental space with a high-value, high-engagement experience guests naturally gravitate toward.</p>
            
            <p>The PoolBar™, which you previewed, is fully portable, easy to set up, and built to enhance rental offerings with a premium attraction that stands out without heavy logistics or complexity.</p>
            
            <p>If you'd like materials for your team or want to see how PoolBar™ could fit within your rental lineup, let's keep the IAAPA momentum going.</p>
            
            <p><strong>Schedule your follow-up meeting now:</strong></p>
            <a href="https://calendly.com/hello-oceanex/30min" class="button">Book a Meeting</a>
            
            <p>Or reach us at: <a href="mailto:Hello@oceanex.group">Hello@oceanex.group</a></p>
            
            <p>Thanks again for being part of the action and for helping shape the next chapter of portable, immersive experiences.</p>
            
            <p class="signature">Your PoolBar™ Crew</p>
        </div>
    </body>
    </html>
    """

def send_email(to_email: str, to_name: str) -> bool:
    """Send email to a recipient with embedded image"""
    try:
        msg = MIMEMultipart('related')
        msg['Subject'] = "Follow Up: PoolBar™ Experience at IAAPA"
        msg['From'] = EMAIL
        msg['To'] = to_email
        
        # Create HTML part
        html_content = get_email_template(to_name)
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Attach image
        try:
            with open('images/image.jpg', 'rb') as img_file:
                img = MIMEImage(img_file.read())
                img.add_header('Content-ID', '<header_image>')
                img.add_header('Content-Disposition', 'inline', filename='image.png')
                msg.attach(img)
        except FileNotFoundError:
            print("Warning: images/image.png not found, sending without image")
        
        with smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT) as server:
            server.login(EMAIL, EMAIL_PASSWORD)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Error sending email to {to_email}: {str(e)}")
        return False

def load_contacts() -> List[dict]:
    """Load contacts from output.json"""
    try:
        with open('test.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="output.json not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")

def get_batch_contacts(batch: str) -> List[dict]:
    """Get contacts based on batch selection - divides into 4 equal quarters"""
    contacts = load_contacts()
    total = len(contacts)
    quarter = total // 4
    
    if batch == "1st_quarter":
        return contacts[:quarter]
    elif batch == "2nd_quarter":
        return contacts[quarter:quarter*2]
    elif batch == "3rd_quarter":
        return contacts[quarter*2:quarter*3]
    elif batch == "4th_quarter":
        return contacts[quarter*3:]
    else:
        raise HTTPException(status_code=400, detail="Invalid batch option")

@app.get("/", response_class=HTMLResponse)
async def get_frontend(request: Request):
    """Serve the frontend HTML from templates folder"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/contacts")
async def get_contacts():
    """Get all contacts from output.json and sent emails info"""
    contacts = load_contacts()
    sent_emails = load_sent_emails()
    
    return {
        "total": len(contacts),
        "contacts": contacts,
        "sent_count": len(sent_emails),
        "sent_emails": sent_emails
    }

@app.get("/api/sending-status")
async def get_sending_status():
    """Check if emails are currently being sent"""
    return {"is_sending": is_sending}

@app.post("/api/send-emails")
async def send_emails(request: EmailRequest):
    """Send emails to selected batch (skip already sent)"""
    global email_status, is_sending
    
    if is_sending:
        raise HTTPException(status_code=400, detail="Emails are already being sent")
    
    is_sending = True
    email_status = []
    
    try:
        contacts = get_batch_contacts(request.batch)
        sent_emails = load_sent_emails()
        
        for contact in contacts:
            name = contact.get("name", "")
            email = contact.get("email", "")
            
            if not email:
                continue
            
            # Skip if already sent
            if email in sent_emails:
                status = {
                    "name": name,
                    "email": email,
                    "status": "Already Sent",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                email_status.append(status)
                continue
            
            success = send_email(email, name)
            
            if success:
                save_sent_email(email)
            
            status = {
                "name": name,
                "email": email,
                "status": "Sent" if success else "Failed",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            email_status.append(status)
            
            # Small delay to avoid overwhelming the email server
            await asyncio.sleep(0.5)
        
        return {
            "message": f"Processed {len(contacts)} contacts",
            "results": email_status
        }
    finally:
        is_sending = False

@app.get("/api/status")
async def get_status():
    """Get current email send status"""
    return {"status": email_status}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)