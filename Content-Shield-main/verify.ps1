# Content Shield Extension - File Verification
# This script checks that all required files are present and valid

Write-Host "Content Shield Extension - File Verification" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Green
1..50 | ForEach-Object { Write-Host "=" -NoNewline -ForegroundColor Green }
Write-Host ""
Write-Host ""

$extensionPath = $PSScriptRoot
$allFilesPresent = $true

# Required files
$requiredFiles = @(
    "manifest.json",
    "content.js",
    "background.js",
    "popup.html",
    "popup.js",
    "options.html",
    "options.js",
    "icons\icon128.png"
)

Write-Host "Checking required files..." -ForegroundColor Cyan
Write-Host ""

foreach ($file in $requiredFiles) {
    $filePath = Join-Path $extensionPath $file
    if (Test-Path $filePath) {
        $fileSize = (Get-Item $filePath).Length
        Write-Host "[OK] $file ($fileSize bytes)" -ForegroundColor Green
    } else {
        Write-Host "[MISSING] $file" -ForegroundColor Red
        $allFilesPresent = $false
    }
}

Write-Host ""
Write-Host "Checking manifest.json validity..." -ForegroundColor Cyan

$manifestPath = Join-Path $extensionPath "manifest.json"
try {
    $manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
    Write-Host "[OK] manifest.json is valid JSON" -ForegroundColor Green
    Write-Host "    Name: $($manifest.name)" -ForegroundColor Gray
    Write-Host "    Version: $($manifest.version)" -ForegroundColor Gray
    Write-Host "    Manifest Version: $($manifest.manifest_version)" -ForegroundColor Gray
} catch {
    Write-Host "[ERROR] manifest.json is not valid JSON" -ForegroundColor Red
    $allFilesPresent = $false
}

Write-Host ""
Write-Host "Checking icons..." -ForegroundColor Cyan

$iconPath = Join-Path $extensionPath "icons\icon128.png"
if (Test-Path $iconPath) {
    $iconSize = (Get-Item $iconPath).Length
    Write-Host "[OK] icon128.png exists ($iconSize bytes)" -ForegroundColor Green
} else {
    Write-Host "[MISSING] icon128.png" -ForegroundColor Red
    $allFilesPresent = $false
}

Write-Host ""
Write-Host "Checking content script..." -ForegroundColor Cyan

$contentPath = Join-Path $extensionPath "content.js"
$contentLines = (Get-Content $contentPath).Count
Write-Host "[OK] content.js has $contentLines lines" -ForegroundColor Green

# Check for key features in content.js
$contentCode = Get-Content $contentPath -Raw
$features = @{
    "TreeWalker" = $contentCode -match "createTreeWalker"
    "MutationObserver" = $contentCode -match "MutationObserver"
    "Message Listener" = $contentCode -match "chrome.runtime.onMessage"
    "Storage Access" = $contentCode -match "chrome.storage.sync"
}

foreach ($feature in $features.GetEnumerator()) {
    if ($feature.Value) {
        Write-Host "    [OK] $($feature.Key) implemented" -ForegroundColor Green
    } else {
        Write-Host "    [MISSING] $($feature.Key) not found" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Green
1..50 | ForEach-Object { Write-Host "=" -NoNewline -ForegroundColor Green }
Write-Host ""

if ($allFilesPresent) {
    Write-Host "STATUS: All files present and valid!" -ForegroundColor Green
    Write-Host ""
    Write-Host "NEXT STEPS:" -ForegroundColor Cyan
    Write-Host "1. Open Chrome/Edge/Brave" -ForegroundColor White
    Write-Host "2. Go to chrome://extensions/" -ForegroundColor White
    Write-Host "3. Enable Developer Mode" -ForegroundColor White
    Write-Host "4. Click 'Load unpacked'" -ForegroundColor White
    Write-Host "5. Select this folder: $extensionPath" -ForegroundColor White
    Write-Host ""
    Write-Host "Extension is ready to load!" -ForegroundColor Green
} else {
    Write-Host "STATUS: Some files are missing or invalid!" -ForegroundColor Red
    Write-Host "Please check the errors above." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
