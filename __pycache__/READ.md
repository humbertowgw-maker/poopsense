# PoopSense 🐾

AI-powered veterinary fecal assessment tool. Upload a photo and get a 
clinical-grade health report in seconds.

**Live Demo:** https://web-production-fb2d1.up.railway.app

---

## What it does

PoopSense analyzes dog stool photos using Claude's Vision AI and returns 
a structured veterinary assessment including:

- Color and consistency analysis
- Blood, mucus, and foreign object detection
- Urgency level (Normal / Monitor / Vet Soon / Emergency)
- Clinical recommendation
- Full vet notes using Bristol Stool Scale equivalent

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.14 |
| Web Framework | Flask |
| AI Vision | Anthropic Claude Sonnet (Vision API) |
| Image Processing | Pillow + Base64 |
| Frontend | HTML, CSS, Vanilla JS |
| Deployment | Railway |
| Config | python-dotenv |

---

## How it works