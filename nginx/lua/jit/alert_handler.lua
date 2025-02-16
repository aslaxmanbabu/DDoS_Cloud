local cjson = require "cjson"
local M = {}

local alert_file_path = "D:/Official/Final/Implementation/alert_state.json"

function M.read_alert_state()
    local file = io.open(alert_file_path, "r")
    if not file then
        ngx.log(ngx.ERR, "Failed to open alert_state.json")
        return {}
    end

    local content = file:read("*a")
    file:close()

    if not content or content == "" then
        ngx.log(ngx.ERR, "alert_state.json is empty")
        return {}
    end

    local success, alert_data = pcall(cjson.decode, content)
    if not success then
        ngx.log(ngx.ERR, "Failed to decode alert_state.json")
        return {}
    end

    if type(alert_data) ~= "table" then
        return {}
    end

    local current_time = os.time()
    local updated = false

    for endpoint, data in pairs(alert_data) do
        if data.alert_state then
            local elapsed_time = current_time - data.timestamp

            if elapsed_time > 600 then  -- Reset alerts after 10 minutes
                alert_data[endpoint].alert_state = false
                updated = true
            end
        end
    end

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

return M
