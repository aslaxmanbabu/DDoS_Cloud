# Define the log file path
$logFile = "D:\Official\Final\Implementation\Scripts\test_alert_trigger.log"

# Check if the log file exists; create it if it doesn't
if (!(Test-Path $logFile)) {
    New-Item -ItemType File -Path $logFile -Force
}

# Append a timestamp to the log file
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $logFile -Value "Alert triggered at $timestamp"

# Optional: Print a confirmation message to the console (useful for manual testing)
Write-Output "Script executed successfully at $timestamp"
