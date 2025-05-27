![CodeRabbit Pull Request Reviews](https://img.shields.io/coderabbit/prs/github/Danielmtv1/ai-access-control?utm_source=oss&utm_medium=github&utm_campaign=Danielmtv1%2Fai-access-control&labelColor=171717&color=FF570A&link=https%3A%2F%2Fcoderabbit.ai&label=CodeRabbit+Reviews)

## 🎯 What does it do?

**AI-powered Physical Access Control System** that:
1. **Manages access permissions** (users, cards, doors, schedules)
2. **Validates access requests** from IoT devices in real-time
3. **Logs all access events** via MQTT
4. **Analyzes access patterns** with AI to detect anomalies and security threats

**Problem**: Manual access control + thousands of logs impossible to review
**Solution**: Automated access validation + AI analysis for intelligent security insights

## 🤖 Supported AI Providers

Configure your preferred one:

- **OpenAI** (GPT-4, GPT-3.5)
- **Google Gemini** (Pro, Flash)  
- **Anthropic Claude** (Opus, Sonnet)
- **Ollama** (Llama3, Mistral - local, free)
- **Azure OpenAI**
- **Cohere**

## 🚀 Setup (2 minutes)

### With OpenAI
```bash
git clone <repo>
cd ai-log-analyzer

# Configure
echo "AI_PROVIDER=openai" > .env
echo "OPENAI_API_KEY=sk-your_key" >> .env

# Start
docker-compose up -d
```

### With Ollama (free)
```bash
# Install Ollama first
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3

# Configure
echo "AI_PROVIDER=ollama" > .env
echo "OLLAMA_MODEL=llama3" >> .env

# Start
docker-compose up -d
```

## 📊 Complete System Flow

### **Access Control Flow**
```bash
# 1. IoT device detects card
Card "ABC123" → Door Reader → MQTT Request

# 2. System validates access
curl -X POST "http://localhost:8000/api/v1/access/validate" \
  -d '{"card_id": "ABC123", "door_id": "main_entrance", "timestamp": "2024-01-15T09:00:00Z"}'

# Response: {"access_granted": true, "user_name": "John Doe", "valid_until": "18:00"}

# 3. IoT device receives response
MQTT Response → Door Lock → Open/Deny

# 4. Access event logged
MQTT Log: {"card": "ABC123", "door": "main_entrance", "result": "granted", "user": "john.doe"}

# 5. AI analyzes patterns
AI Detection: "Unusual: John accessed server room at 3AM - investigate"
```

### **Data Management**
```bash
# Manage users
curl -X POST "http://localhost:8000/api/v1/users" \
  -d '{"name": "John Doe", "email": "john@company.com", "department": "IT"}'

# Manage access cards  
curl -X POST "http://localhost:8000/api/v1/cards" \
  -d '{"card_id": "ABC123", "user_id": 1, "card_type": "employee", "active": true}'

# Manage doors/areas
curl -X POST "http://localhost:8000/api/v1/doors" \
  -d '{"name": "Server Room", "location": "Building A", "security_level": "high"}'

# Set permissions
curl -X POST "http://localhost:8000/api/v1/permissions" \
  -d '{"user_id": 1, "door_id": 1, "access_schedule": "09:00-18:00", "days": ["mon","tue","wed","thu","fri"]}'
```

## 🔧 Configuration

**Main environment variables:**
```bash
AI_PROVIDER=openai|google|anthropic|ollama
AI_MODEL=gpt-4|gemini-pro|claude-3-opus|llama3
OPENAI_API_KEY=sk-...     # If using OpenAI
GOOGLE_AI_API_KEY=...     # If using Google
OLLAMA_BASE_URL=http://localhost:11434  # If using Ollama
```

## 📋 What the AI Does

**Input:** Raw log
```json
{"user": "admin", "action": "login", "time": "03:00", "result": "success"}
```

**Output:** Automatic analysis
```json
{
  "anomaly_detected": true,
  "severity": "high",
  "summary": "Admin login at 3AM outside business hours",
  "recommendations": [
    "Verify if it was scheduled maintenance",
    "Review post-login activity"
  ]
}
```

## 📅 MVP - 8 Week Development Timeline

### ✅ **Completed (Weeks 1-4)**
- [x] Base FastAPI + PostgreSQL + Docker structure
- [x] User management and JWT authentication
- [x] MQTT communication infrastructure
- [x] Basic database models (users, mqtt_messages)
- [x] Health checks and metrics
- [x] Alembic migrations

### 🚧 **In Development (Week 5 - Current)**
- [ ] **Access control entities** (cards, doors, permissions)
- [ ] **Real-time access validation** API for IoT devices
- [ ] **AI integration** for log analysis
- [ ] **MQTT bidirectional** communication (requests + responses)

### 📋 **Pending (Weeks 6-8)**

#### **Week 6: Core Access Control**
- [ ] Card management system (CRUD)
- [ ] Door/area management 
- [ ] Permission/schedule system
- [ ] Access validation engine
- [ ] IoT device authentication

#### **Week 7: AI Analysis & Dashboard**
- [ ] AI analysis of access patterns
- [ ] Anomaly detection (unusual access times, failed attempts)
- [ ] Web dashboard for access management
- [ ] Real-time alerts for security events

#### **Week 8: Integration & Deploy**
- [ ] Complete IoT device integration
- [ ] Access control + AI working together
- [ ] Performance optimization
- [ ] Production deployment

### 🎯 **Current Code Status**

**What works:**
```bash
# ✅ Basic APIs and auth
curl http://localhost:8000/health
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/auth/me

# ✅ MQTT message logging  
mosquitto_pub -h localhost -t "access/door1/events" -m '{"card":"ABC123","result":"granted"}'
curl http://localhost:8000/api/v1/mqtt/messages  # View logged messages

# ✅ User management
curl http://localhost:8000/api/v1/auth/login -d '{"email":"admin@access-control.com","password":"AdminPassword123!"}'
```

**What's missing (critical for access control):**
```bash
# ❌ Access control entities not implemented
curl http://localhost:8000/api/v1/cards  # → 404
curl http://localhost:8000/api/v1/doors  # → 404
curl http://localhost:8000/api/v1/permissions  # → 404

# ❌ Real-time access validation
curl http://localhost:8000/api/v1/access/validate  # → 404

# ❌ AI analysis  
curl http://localhost:8000/api/v1/ai/analyze  # → 404

# ❌ Dashboard
curl http://localhost:8000/dashboard  # → 404
```

### 📊 **MVP Progress**

| Component | Status | Week | Critical? |
|-----------|--------|------|-----------|
| 🏗️ Base infrastructure | ✅ 100% | 1-2 | ✅ |
| 👤 User management | ✅ 100% | 4 | ✅ |
| 💳 **Card management** | ❌ 0% | 5 | 🔥 **Critical** |
| 🚪 **Door management** | ❌ 0% | 5 | 🔥 **Critical** |
| 🔐 **Access validation** | ❌ 0% | 6 | 🔥 **Critical** |
| 📡 MQTT communication | ✅ 80% | 3 | ✅ |
| 🤖 AI integration | ❌ 0% | 6-7 | ⚠️ Important |
| 📊 Dashboard | ❌ 0% | 7 | ⚠️ Important |
| 🚨 Alerts | ❌ 0% | 7 | ⚠️ Important |

### 🚨 **Critical Gaps for Access Control**

**Without these, IoT devices can't validate access:**
1. **Card Management** - Register cards to users
2. **Door Management** - Define doors and security levels  
3. **Permission System** - Who can access what and when
4. **Access Validation API** - Real-time validation for IoT devices
5. **MQTT Response System** - Send validation results back to devices

### 🎯 **Critical Remaining Objectives**

**For a functional access control system:**
1. **Access Control Core** (Week 5-6) - Cards, doors, permissions, validation
2. **IoT Integration** (Week 6) - Real-time validation API for devices  
3. **AI Security Analysis** (Week 7) - Analyze access patterns for threats
4. **Management Dashboard** (Week 7) - UI to manage users, cards, doors


**Critical Path:** Access control must work before AI analysis adds value.

## 🛠️ Tech Stack

- **Backend**: FastAPI + Python 3.12
- **Database**: PostgreSQL
- **Messaging**: MQTT (Mosquitto)
- **AI**: Configurable (OpenAI/Google/Anthropic/Ollama)
- **Deploy**: Docker Compose

## 🔗 Useful Links

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics

---

**Turn log chaos into actionable insights with the power of AI.**
