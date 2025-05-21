# 🛠️ Setup Instructions for Inventory Checker Bot

This guide will help you set up the backend (FastAPI) and frontend (React) for the Inventory Checker Bot.

---
# 🔁 Step 1: Clone the Repository

Clone this repository to your local machine:

```bash
git clone https://github.com/kamalkannan79/InventoryCheckerBOT.git
cd inventory-checker-bot
```

# Step 2: Create Python Virtual Environment

Open terminal in the root project folder
```bash
python -m venv .venv
```
Activate the virtual environment
For Windows:
.venv\Scripts\activate



# Step 3: Create .env File
In the root folder, create a .env file and add the following environment variables:
```bash
GOOGLE_GEMINI_API_KEY=your_google_gemini_api_key
```
Replace each value (your_google_gemini_api_key, etc.) with your actual credentials(https://aistudio.google.com/apikey).

# Step 4: Install Python Dependencies
Ensure your virtual environment is activated, then install all required Python libraries:
```bash
pip install -r requirements.txt
```
# Step 5: Set Up React Frontend
Navigate to the React frontend folder and install all dependencies:

In terminal navigate to chatbot folder
```bash
cd chatbot
```
Then run this
```bash
npm install
```

# Step 6 : Start the application
Navigate to **start.bat** and double click on it launch.  
Run this on google chrome
```bash
http://localhost:3000
```

---


