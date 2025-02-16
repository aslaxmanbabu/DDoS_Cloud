package.path = package.path .. ";D:/Official/Final/Implementation/nginx/lua/jit/?.lua"
local cjson = require "cjson"
local shared_functions = require "shared_functions"

local suspicious_file = "D:/Official/Final/Implementation/TempLogs/suspicious_ips.conf"
local json_log_file = "D:/Official/Final/Implementation/TempLogs/request_logs.json"

local client_ip = ngx.var.remote_addr
local request_uri = ngx.var.uri
local current_time = os.time()

-- Check if alert state is active
local alert_state = shared_functions.get_alert_state(request_uri)
ngx.log(ngx.ERR, "Alert state for ", request_uri, ": ", tostring(alert_state))

if not alert_state then
    ngx.exit(ngx.HTTP_OK)  -- Use 200 instead of returning silently for debugging
end


-- Read request logs
local request_log = shared_functions.read_ip_logs(json_log_file)
if type(request_log) ~= "table" then
    request_log = {}
end

if type(request_log[client_ip]) ~= "table" then
    request_log[client_ip] = {}
end

-- Remove old entries (older than 2 seconds)
local recent_requests = {}
for _, timestamp in ipairs(request_log[client_ip]) do
    if current_time - timestamp <= 2 then
        table.insert(recent_requests, timestamp)
    end
end

-- Add new request timestamp
table.insert(recent_requests, current_time)
request_log[client_ip] = recent_requests

-- If more than 4 requests in 2 seconds, block the IP
if #recent_requests > 4 then
    shared_functions.add_ip_to_suspicious_list(client_ip, suspicious_file, json_log_file)
    ngx.exit(ngx.HTTP_FORBIDDEN)
else
    shared_functions.write_ip_logs(request_log, json_log_file)
end
