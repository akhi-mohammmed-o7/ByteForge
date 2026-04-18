# ⚒️ BYTEFORGE

### Anonymous Proof-of-Work Passport for Inclusive Hiring

[![SDG 8](https://img.shields.io/badge/SDG-8%20Decent%20Work%20%26%20Economic%20Growth-00f2ff)](https://sdgs.un.org/goals/goal8)
[![Python](https://img.shields.io/badge/Python-3.x-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-00f2ff)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

## 📖 Overview

ByteForge is a skill-based hiring platform that eliminates bias by allowing workers to prove their abilities anonymously. Workers complete cryptographic MCQ tests, earn verified SHA-256 credentials, and receive a digital passport with QR code verification. Employers evaluate candidates based purely on demonstrated skills.

## 🎯 Features

### 👷 For Workers
- Anonymous registration with unique ID (e.g., `SH-X7K2M`)
- 5 skill domains with 10 questions each
- Real-time scoring (50% passing threshold)
- Digital passport with QR code
- Live leaderboard by shadow score
- Inbox for employer messages

### 🏢 For Employers
- Merit board with skill filtering
- Shortlist candidates anonymously
- Reveal identity only after shortlisting
- Direct messaging system
- Public hash verification

### 👑 For Admin
- CRUD operations for skills and questions
- User management dashboard
- Verification records tracking
- System statistics

## 🛠️ Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | Python 3.x, Flask, SQLAlchemy |
| **Database** | SQLite |
| **Frontend** | HTML5, CSS3, Bootstrap 5, Font Awesome |
| **Security** | SHA-256 Hashing, Flask-Login, Werkzeug |
| **Verification** | QR Code Generation, Cryptographic Hashes |

## 📁 Project Structure
