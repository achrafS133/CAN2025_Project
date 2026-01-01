# CAN 2025 Guardian - Quick Launch Script
Write-Host "🚀 Starting CAN 2025 Guardian Environment..." -ForegroundColor Cyan

if (!(Test-Path ".env")) {
    Write-Host "⚠️ Warning: .env file not found. Creating template..." -ForegroundColor Yellow
    "OPENAI_API_KEY=your_key_here`nTWILIO_ACCOUNT_SID=your_sid`nTWILIO_AUTH_TOKEN=your_token`nTWILIO_PHONE_NUMBER=your_num`nRECIPIENT_PHONE_NUMBER=your_dest" | Out-File -FilePath ".env"
}

Write-Host "📦 Installing dependencies..." -ForegroundColor Gray
pip install -r requirements.txt

Write-Host "🛡️ Launching Command Center..." -ForegroundColor Green
streamlit run app.py
