# Ocean-EX Email Automation

A FastAPI-based tool to send personalized emails from a Google Sheet contact list.
Each day (1–3) triggers a different email template with attachments.

---

## 🚀 Features

- Reads contacts from Google Sheets (CSV link)
- Sends 3 different email templates (Day 1, 3, 6)
- Personalizes with recipient’s first name
- Attaches 1 image + 3 videos from `/media`
- Config via `.env` (SMTP credentials)

---

## ⚙️ Setup

```bash
git clone https://github.com/alihassanml/Ocean-EX-Email-Automation.git
cd Ocean-EX-Email-Automation
pip install -r requirements.txt
```

Create `.env`:

```

```

---

## ▶️ Run

```bash
uvicorn main:app --reload
```

Then visit:

```
http://127.0.0.1:8000/send-emails/?day=1
```

---

## 📂 Project Structure

```
main.py
email_templates.py
credentials.env
/media/
   ├── image.jpg
   ├── video1.mp4
   ├── video2.mp4
   └── video3.mp4
```

---

**Author:** Ali Hassan
**Tech:** FastAPI • Pandas • SMTP • Python-dotenv

```

```

`
