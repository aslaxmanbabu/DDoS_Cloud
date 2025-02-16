package.path = package.path .. ";D:/Official/Final/Implementation/nginx/lua/jit/?.lua"
local shared_functions = require "shared_functions"
local cjson = require "cjson"

local request_uri = ngx.var.request_uri
local client_ip = ngx.var.remote_addr
local alert_file_path = "D:/Official/Final/Implementation/alert_state.json"
local suspicious_ips_path = "D:/Official/Final/Implementation/TempLogs/suspicious_ips.conf"
local ip_log_path = "D:/Official/Final/Implementation/TempLogs/quarantine_ips.json"

local read_alert_state = shared_functions.read_alert_state
local write_alert_state = shared_functions.write_alert_state
local write_ip_logs = shared_functions.write_ip_logs
local read_ip_logs = shared_functions.read_ip_logs
local add_ip_to_suspicious_list = shared_functions.add_ip_to_suspicious_list

local function load_alert_data()
    local alert_data = read_alert_state(alert_file_path) or {}

    if type(alert_data) ~= "table" then
        ngx.log(ngx.ERR, "Failed to load alert state, resetting to empty table")
        return {}
    end

    return alert_data
end

local alert_data = load_alert_data()
local captcha_validated = ngx.var.cookie_captcha_status
local ngx_now = ngx.now()

-- Function to log IP requests for rate limiting
local function log_ip_request(ip)
    local logs = read_ip_logs(ip_log_path) or {}

    if not logs[ip] then
        logs[ip] = {}
    end

    -- Append current timestamp
    table.insert(logs[ip], os.time())

    -- Keep only requests within the last 2 seconds
    local new_logs = {}
    for _, timestamp in ipairs(logs[ip]) do
        if os.time() - timestamp <= 2 then
            table.insert(new_logs, timestamp)
        end
    end
    logs[ip] = new_logs

    -- Save updated logs
    write_ip_logs(logs, ip_log_path)

    -- If more than 4 requests in 2 seconds, flag as suspicious
    if #logs[ip] > 4 then
        ngx.log(ngx.WARN, "Suspicious activity detected for IP: " .. ip)
        add_ip_to_suspicious_list(ip, suspicious_ips_path)
    end
end

-- Function to check and reset expired alerts
local function check_alert_expiry()
    local updated = false

    for endpoint, data in pairs(alert_data) do
        if data.alert_state and (ngx_now - data.timestamp > 600) then  -- 10 minutes expiry
            ngx.log(ngx.INFO, "Resetting alert state for " .. endpoint)
            alert_data[endpoint].alert_state = false
            updated = true
        end
    end

    if updated then
        write_alert_state(alert_data, alert_file_path)
    end
end

-- Function to start a recurring timer every 2 minutes
local function start_alert_timer()
    local ok, err = ngx.timer.at(120, function()
        check_alert_expiry()
        start_alert_timer()  -- Restart the timer
    end)

    if not ok then
        ngx.log(ngx.ERR, "Failed to start alert expiry timer: " .. err)
    end
end

-- Start the timer when the script is loaded
start_alert_timer()

-- Check if the request URI is under active alert
if alert_data[request_uri] and alert_data[request_uri].alert_state then
    log_ip_request(client_ip)

    if captcha_validated == "valid" then
        ngx.header["Set-Cookie"] = "captcha_status=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/"
        ngx.log(ngx.INFO, "CAPTCHA validated for IP: " .. client_ip)
        return ngx.exec("/forward_main")
    else
        ngx.log(ngx.WARN, "Redirecting to CAPTCHA challenge for IP: " .. client_ip)
        return ngx.redirect("/captcha_challenge?redirect_uri=" .. ngx.escape_uri(request_uri))
    end
else
    ngx.log(ngx.INFO, "No active alert for " .. request_uri .. ", forwarding request.")
    return ngx.exec("/forward_main")
end
