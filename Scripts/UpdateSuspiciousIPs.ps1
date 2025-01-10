param(
    [string]$ip
)

# Configuration file path
$configPath = "D:\Official\Final\Implementation\nginx\conf\suspicious_ips.conf"
$tempPath = "D:\Official\Final\Implementation\nginx\conf\suspicious_ips_temp.conf"

# Current timestamp
$currentTime = Get-Date

# Check if suspicious_ips.conf exists; if not, create it
if (!(Test-Path $configPath)) {
    New-Item -ItemType File -Path $configPath
}

# Add the IP address with timestamp to the config file
Add-Content $configPath "$ip|$($currentTime.ToString('yyyy-MM-dd HH:mm:ss'))"

# Filter out expired IPs (older than 1 hour)
Get-Content $configPath | ForEach-Object {
    $parts = $_ -split '\|'
    if ($parts.Count -eq 2) {
        $ipAddress = $parts[0]
        $timestamp = [datetime]::Parse($parts[1])
        
        # Check if the IP entry is older than 1 hour; if not, add it to the temporary list
        if ((Get-Date) - $timestamp -lt (New-TimeSpan -Hours 1)) {
            Add-Content $tempPath "deny $ipAddress;"
        }
    }
}

# Replace original file with the filtered list
Move-Item -Force $tempPath $configPath

# Reload NGINX to apply the new block list
Start-Process -FilePath "D:\Official\Final\Implementation\nginx\nginx.exe" -ArgumentList "-s reload"
