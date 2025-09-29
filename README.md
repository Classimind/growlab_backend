# 🌱 Hydroponics AI

## 📄 Documentation
For detailed documentation, see [DOCUMENTATION.md](DOCUMENTATION.md)

---

## ⚙️ Deployment Setup

### 1. Create `.env` File
Create a `.env` file in your project directory with the following environment variables and notes:

```bash
# MongoDB credentials
MONGO_USER=your_db_user
MONGO_PASSWORD=your_db_password
MONGO_DB_NAME=growlab
BROKER_URL=mqtt.safalstha.com.np
REDIS_URI=redis://localhost:6379

# Optional: backend settings
MONGO_HOST=localhost
MONGO_PORT=27017

# 🔄 Note
# Before pushing code to GitHub, update the following:
# broker_url
# Change from: mqtt.safalstha.com.np
# To: localhost
# redis_url
# Change from: redis://localhost:6379
# To: redis://redis:6379
```

## Run the Server Locally
```bash
uvicorn app.main:app --port <port_number> --reload
```

