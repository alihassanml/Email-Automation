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
                color: #2c3e50;
                margin: 0;
                padding: 0;
                background-color: #f4f7f9;
            }}
            .email-wrapper {{
                background-color: #f4f7f9;
                padding: 20px 0;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            }}
            .header-image {{
                width: 100%;
                object-fit: cover;
                height: 250px;
                display: block;
                border-bottom: 4px solid #0066cc;
            }}
            .content {{
                padding: 40px 35px;
            }}
            .header-badge {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 12px 25px;
                border-radius: 25px;
                display: inline-block;
                font-size: 14px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 25px;
            }}
            .header-title {{
                font-size: 28px;
                font-weight: 700;
                color: #1a1a1a;
                margin-bottom: 30px;
                line-height: 1.3;
            }}
            .greeting {{
                font-size: 20px;
                font-weight: 600;
                margin-bottom: 20px;
                color: #2c3e50;
            }}
            .paragraph {{
                margin-bottom: 18px;
                line-height: 1.8;
                font-size: 16px;
                color: #4a5568;
            }}
            .highlight-box {{
                background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
                border-left: 4px solid #667eea;
                padding: 20px;
                margin: 25px 0;
                border-radius: 8px;
            }}
            .highlight-box p {{
                margin: 0;
                font-size: 15px;
                color: #2c3e50;
                font-weight: 500;
            }}
            .features-list {{
                background-color: #f8fafc;
                padding: 20px 25px;
                border-radius: 8px;
                margin: 25px 0;
            }}
            .feature-item {{
                padding: 10px 0;
                display: flex;
                align-items: flex-start;
            }}
            .feature-item:before {{
                content: "✓";
                color: #10b981;
                font-weight: bold;
                font-size: 20px;
                margin-right: 12px;
                flex-shrink: 0;
            }}
            .button-container {{
                text-align: center;
                margin: 35px 0;
            }}
            .button {{
                display: inline-block;
                padding: 16px 40px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white !important;
                text-decoration: none;
                border-radius: 50px;
                font-weight: 700;
                font-size: 16px;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
                transition: all 0.3s ease;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
            }}
            .divider {{
                height: 2px;
                background: linear-gradient(90deg, transparent, #e0e7ff, transparent);
                margin: 30px 0;
            }}
            .contact-box {{
                background-color: #f8fafc;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                margin: 25px 0;
            }}
            .contact-box p {{
                margin-bottom: 10px;
                color: #4a5568;
                font-size: 14px;
            }}
            .contact-box a {{
                color: #667eea;
                text-decoration: none;
                font-weight: 600;
                font-size: 16px;
            }}
            .contact-box a:hover {{
                text-decoration: underline;
            }}
            .footer {{
                background: linear-gradient(135deg, #1e3a8a 0%, #312e81 100%);
                padding: 30px;
                text-align: center;
                color: white;
            }}
            .footer p {{
                margin-bottom: 8px;
                font-size: 15px;
            }}
            .signature {{
                font-weight: 700;
                font-size: 18px;
                margin-top: 15px;
                color: white;
            }}
            .urgency-banner {{
                background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
                color: #78350f;
                padding: 15px 25px;
                text-align: center;
                font-weight: 600;
                font-size: 14px;
                border-radius: 8px;
                margin: 20px 0;
            }}
            @media only screen and (max-width: 600px) {{
                .content {{
                    padding: 25px 20px;
                }}
                .header-title {{
                    font-size: 24px;
                }}
                .button {{
                    padding: 14px 30px;
                    font-size: 14px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="email-wrapper">
            <div class="container">
                <img src="cid:header_image" class="header-image" alt="PoolBar IAAPA 2026">
                
                <div class="content">
                    <div class="header-badge">🌊 IAAPA 2026 OPPORTUNITY</div>
                    
                    <h1 class="header-title">Your IAAPA PoolBar Opportunity for 2026</h1>
                    
                    <p class="greeting">Hi {name},</p>
                    
                    <p class="paragraph">Thanks again for stopping by at IAAPA and experiencing the PoolBar live. Many operators told us the same thing: <strong>this is the kind of high-impact asset they want in their lineup for 2026.</strong></p>
                    
                    <div class="highlight-box">
                        <p>💡 The PoolBar inflates into a rigid, premium structure in minutes using a single high-pressure pump. It requires no blower, stays firm for up to six days, and only needs a quick top-up when you choose.</p>
                    </div>
                    
                    <div class="features-list">
                        <div class="feature-item">Inflates in minutes with a single high-pressure pump</div>
                        <div class="feature-item">No blower required - stays firm for up to 6 days</div>
                        <div class="feature-item">Quick deflation and compact storage</div>
                        <div class="feature-item">Effortless turnover and transport</div>
                    </div>
                    
                    <p class="paragraph">Since IAAPA, operators across various industries have already begun <strong>reserving 2026 slots and requesting ROI projections.</strong> The momentum has been strong, and early-adopter allocations are filling quickly.</p>
                    
                    <div class="urgency-banner">
                        ⚡ Early-adopter allocations are filling quickly for 2026
                    </div>
                    
                    <p class="paragraph">If you'd like to explore how the PoolBar can elevate your lineup in 2026 or secure early access to the IAAPA program, let's keep the conversation moving.</p>
                    
                    <div class="button-container">
                        <a href="https://calendly.com/hello-oceanex/30min" class="button">📅 Schedule Your Follow-Up Meeting</a>
                    </div>
                    
                    <div class="divider"></div>
                    
                    <div class="contact-box">
                        <p>Questions? Reach out directly:</p>
                        <a href="mailto:Hello@oceanex.group">Hello@oceanex.group</a>
                    </div>
                </div>
                
                <div class="footer">
                    <p>Thanks again for being part of the IAAPA experience.</p>
                    <p>We look forward to helping you build your PoolBar revenue zone in 2026.</p>
                    <p class="signature">🌊 Your Oceanex Crew</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


def send_email(to_email: str, to_name: str) -> bool:
    """Send email to a recipient with embedded image"""
    try:
        msg = MIMEMultipart('related')
        msg['Subject'] = f"{to_name} quick IAAPA follow-up for your 2026 planning"
        msg['From'] = EMAIL
        msg['To'] = to_email
        
        # Create HTML part
        html_content = get_email_template(to_name)
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Attach image
        try:
            with open('images/image.png', 'rb') as img_file:
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