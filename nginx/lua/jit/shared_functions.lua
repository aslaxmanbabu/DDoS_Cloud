local cjson = require "cjson"

local M = {}

-- Function to check if an IP already exists in the suspicious list
local function ip_exists_in_suspicious_list(ip, suspicious_file_path)
    local file = io.open(suspicious_file_path, "r")
    if not file then return false end

    for line in file:lines() do
        if line:match("deny " .. ip .. ";") then
            file:close()
            return true
        end
    end

    file:close()
    return false
end

-- Add an IP to the suspicious IP list and restart NGINX if not already present
function M.add_ip_to_suspicious_list(ip, suspicious_file_path)
    if ip_exists_in_suspicious_list(ip, suspicious_file_path) then
        ngx.log(ngx.NOTICE, "IP " .. ip .. " is already in the suspicious list. Skipping addition.")
        return
    end

    local file = io.open(suspicious_file_path, "a")
    if file then
        file:write("deny " .. ip .. ";\n")
        file:close()
        
        -- Restart NGINX to apply changes
        local restart_command = "nginx -s reload"
        local success, _, exit_code = os.execute(restart_command)

        if not success or exit_code ~= 0 then
            ngx.log(ngx.ERR, "Failed to restart NGINX after adding IP: " .. ip)
        end
    else
        ngx.log(ngx.ERR, "Failed to open suspicious IP file for writing: " .. suspicious_file_path)
    end
end

function M.get_alert_state(endpoint)
    local alert_file = "D:/Official/Final/Implementation/TempLogs/alert_state.json"
    local file = io.open(alert_file, "r")
    if not file then
        return false
    end

    local content = file:read("*a")
    file:close()
    
    local alert_data = cjson.decode(content)

    -- Ensure the endpoint exists in alert_data and check its alert_state
    if alert_data[endpoint] and alert_data[endpoint]["alert_state"] == true then
        return true
    end
    
    return false
end

function M.is_ip_suspicious(ip, suspicious_file)
    -- Read the suspicious IPs file
    local file = io.open(suspicious_file, "r")
    if not file then
        return false
    end

    for line in file:lines() do
        if line == ip then
            file:close()
            return true
        end
    end

    file:close()
    return false
end

-- Read the JSON file for IP logs
function M.read_ip_logs(file_path)
    file_path = file_path or "D:/Official/Final/Implementation/TempLogs/quarantine_ips.json"
    local file = io.open(file_path, "r")
    if not file then
        return {}
    end
    local content = file:read("*a")
    file:close()
    if content == "" then
        return {}
    end
    return cjson.decode(content)
end

-- Write IP logs to a JSON file
function M.write_ip_logs(logs, file_path)
    file_path = file_path or "D:/Official/Final/Implementation/TempLogs/quarantine_ips.json"
    local file = io.open(file_path, "w")
    if not file then
        ngx.log(ngx.ERR, "Failed to open IP logs file for writing")
        return
    end
    file:write(cjson.encode(logs))
    file:close()
end

-- Remove an IP from the logs
function M.remove_ip_from_logs(ip, file_path)
    local ip_logs = M.read_ip_logs(file_path)
    ip_logs[ip] = nil
    M.write_ip_logs(ip_logs, file_path)
end

-- Get the last request timestamp for an IP
function M.get_last_request_timestamp(ip, file_path)
    local ip_logs = M.read_ip_logs(file_path)
    local ip_request_timestamps = ip_logs[ip]
    if ip_request_timestamps and #ip_request_timestamps > 0 then
        return ip_request_timestamps[#ip_request_timestamps]
    end
    return nil
end

-- Read alert state with automatic expiry handling
function M.read_alert_state(alert_file_path)
    alert_file_path = alert_file_path or "D:/Official/Final/Implementation/alert_state.json"

    local file = io.open(alert_file_path, "r")
    if not file then
        ngx.log(ngx.ERR, "Failed to open alert_state.json")
        return {}  -- Return an empty table instead of `false`
    end

    local content = file:read("*a")
    file:close()

    if not content or content == "" then
        ngx.log(ngx.ERR, "alert_state.json is empty")
        return {}  -- Return an empty table
    end

    local success, alert_data = pcall(cjson.decode, content)
    if not success then
        ngx.log(ngx.ERR, "Failed to decode alert_state.json: " .. content)
        return {}  -- Return an empty table on decoding failure
    end

    -- Ensure alert_data is a valid table
    if not alert_data or type(alert_data) ~= "table" then
        return {}
    end

    local current_time = os.time()
    local updated = false

    -- Check for expired alerts and reset them
    for endpoint, data in pairs(alert_data) do
        if data.alert_state and (current_time - data.timestamp) > 600 then
            alert_data[endpoint].alert_state = false
            alert_data[endpoint].timestamp = current_time
            updated = true
        end
    end

    -- Write back only if there were updates
    if updated then
        local file = io.open(alert_file_path, "w")
        if file then
            file:write(cjson.encode(alert_data))
            file:close()
        else
            ngx.log(ngx.ERR, "Failed to write updated alert_state.json")
        end
    end

    return alert_data
end


function M.update_alert_state(state, timestamp, endpoint, alert_file_path)
    alert_file_path = alert_file_path or "D:/Official/Final/Implementation/alert_state.json"

    -- Read current alert state
    local file = io.open(alert_file_path, "r")
    local alert_data = {}

    if file then
        local content = file:read("*a")
        file:close()
        if content and content ~= "" then
            local success, decoded_data = pcall(cjson.decode, content)
            if success and type(decoded_data) == "table" then
                alert_data = decoded_data
            end
        end
    end

    -- Ensure alert_data is a valid table
    if not alert_data or type(alert_data) ~= "table" then
        alert_data = {}
    end

    -- Update or set alert state to false if no active alert
    if state then
        alert_data[endpoint] = { alert_state = state, timestamp = timestamp }
    else
        alert_data[endpoint] = alert_data[endpoint] or {}  -- Keep existing data if available
        alert_data[endpoint].alert_state = false
        alert_data[endpoint].timestamp = timestamp or alert_data[endpoint].timestamp
    end

    -- Write updated alert state back to the file
    local file = io.open(alert_file_path, "w")
    if not file then
        ngx.log(ngx.ERR, "Failed to open alert_state.json for writing")
        return
    end

    file:write(cjson.encode(alert_data))
    file:close()
end

return M
