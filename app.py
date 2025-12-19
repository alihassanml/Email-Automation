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
    """Generate HTML email template with embedded images matching client design"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #ffffff;
                margin: 0;
                padding: 0;
                background-color: #f4f7f9;
            }}
            .email-wrapper {{
                background-color: #f4f7f9;
                padding: 0;
            }}
            .container {{
                max-width: 700px;
                margin: 0 auto;
                background-color: #2a6fa8;
                overflow: hidden;
            }}
            .logo-section {{
                background-color: #ffffff;
                padding: 20px;
                text-align: center;
            }}
            .logo {{
                width: 200px;
                height: 110px;
                object-fit: cover;
                display: inline-block;
            }}
            .header-image {{
                width: 100%;
                height: 200px;
                object-fit: cover;
                display: block;
                background-color: white;

            }}
            .content {{
                padding: 50px 40px;
                background-color: #2a6fa8;
                color: #ffffff;
            }}
            .name-box {{
                background-color: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                padding: 20px;
                text-align: center;
                margin-bottom: 40px;
            }}
            .name-box h2 {{
                font-size: 28px;
                font-weight: 700;
                color: #ffffff;
                margin: 0;
            }}
            .paragraph {{
                margin-bottom: 25px;
                line-height: 1.8;
                font-size: 18px;
                color: #ffffff;
            }}
            .button-container {{
                text-align: center;
                margin: 40px 0;
            }}
            .button {{
                display: inline-block;
                padding: 18px 50px;
                background-color: #f4d8a0;
                color: #2a6fa8 !important;
                text-decoration: none;
                border-radius: 50px;
                font-weight: 700;
                font-size: 18px;
                transition: all 0.3s ease;
            }}
            .button:hover {{
                background-color: #f5e5b8;
                transform: translateY(-2px);
            }}
            .contact-line {{
                text-align: center;
                margin: 30px 0;
                font-size: 20px;
            }}
            .contact-line a {{
                color: #ffffff;
                text-decoration: none;
                font-weight: 600;
            }}
            .signature {{
                text-align: center;
                margin-top: 40px;
                font-size: 20px;
                font-weight: 600;
                color: #ffffff;
            }}
            @media only screen and (max-width: 600px) {{
                .content {{
                    padding: 30px 20px;
                }}
                .paragraph {{
                    font-size: 16px;
                }}
                .button {{
                    padding: 15px 35px;
                    font-size: 16px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="email-wrapper">
            <div class="container">
                <!-- Logo Section -->
                <div class="logo-section">
                    <img src="cid:logo_image" class="logo" alt="Oceanex Logo">
                </div>
                
                <!-- Header Image -->
                <img src="cid:header_image" class="header-image" alt="PoolBar IAAPA">
                
                <!-- Content Section -->
                <div class="content">
                    <!-- Personalized Name Box -->
                    <div class="name-box">
                        <h2>Hi {name}</h2>
                    </div>
                    
                    <p class="paragraph">Thanks again for stopping by at IAAPA and experiencing the PoolBar live. Many operators told us the same thing: this is the kind of high-impact asset they want in their lineup for 2026.</p>
                    
                    <p class="paragraph">The PoolBar, which you previewed, inflates into a rigid, premium structure in minutes using a single high-pressure pump. It requires no blower, stays firm for up to six days, and only needs a quick top-up when you choose. When the event ends, it deflates fast and packs down small, making turnover and transport effortless.</p>
                    
                    <p class="paragraph">Since IAAPA, operators have already begun reserving 2026 slots and requesting ROI projections. The momentum has been strong, and early-adopter allocations are filling quickly.</p>
                    
                    <p class="paragraph">If you'd like to explore how the PoolBar can elevate your lineup in 2026 or secure early access to the IAAPA program, let’s keep the conversation moving.</p>
                    
                    <!-- CTA Button -->
                    <div class="button-container">
                        <a href="https://calendly.com/hello-oceanex/30min" class="button">Schedule your follow-up meeting now:</a>
                    </div>
                    
                    <!-- Contact Email -->
                    <div class="contact-line">
                        <a href="mailto:Hello@oceanex.group">Hello@oceanex.group</a>
                    </div>
                    
                    <p class="paragraph">Thanks again for being part of the IAAPA experience. We look forward to helping you build your PoolBar revenue zone in 2026.</p>
                    
                    <!-- Signature -->
                    <p class="signature">Your PoolBar™ Crew</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

def send_email(to_email: str, to_name: str) -> bool:
    """Send email to a recipient with embedded images (logo + header)"""
    try:
        msg = MIMEMultipart('related')
        msg['Subject'] = f"{to_name}, quick IAAPA follow-up for your 2026 planning"
        msg['From'] = EMAIL
        msg['To'] = to_email

        to_name= str.capitalize(to_name.split()[0])
        # Create HTML part
        html_content = get_email_template(to_name)
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Attach logo image
        try:
            with open('images/logo.png', 'rb') as logo_file:
                logo_img = MIMEImage(logo_file.read())
                logo_img.add_header('Content-ID', '<logo_image>')
                logo_img.add_header('Content-Disposition', 'inline', filename='logo.png')
                msg.attach(logo_img)
        except FileNotFoundError:
            print("Warning: images/logo.png not found")
        
        # Attach header image
        try:
            with open('images/header.png', 'rb') as header_file:
                header_img = MIMEImage(header_file.read())
                header_img.add_header('Content-ID', '<header_image>')
                header_img.add_header('Content-Disposition', 'inline', filename='header.png')
                msg.attach(header_img)
        except FileNotFoundError:
            print("Warning: images/header.png not found")
        
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