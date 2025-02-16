package.path = package.path .. ";D:/Official/Final/Implementation/nginx/lua/jit/?.lua"
local shared_functions = require "shared_functions"
local cjson = require "cjson"

local alert_file_path = "D:/Official/Final/Implementation/alert_state.json"

ngx.req.read_body()
local data = ngx.req.get_body_data()
local decoded_data = cjson.decode(data)

if not decoded_data or not decoded_data.result or not decoded_data.result.uri_path then
    ngx.status = 400
    ngx.say(cjson.encode({ error = "Invalid webhook payload. 'uri_path' key missing." }))
    return
end

local target_endpoint = decoded_data.result.uri_path
local ngx_now = os.time() -- Use os.time() for consistency with shared_functions.lua

-- Update the alert state using shared function
shared_functions.update_alert_state(true, ngx_now, target_endpoint, alert_file_path)

ngx.status = 200
ngx.header["Content-Type"] = "application/json"
ngx.say(cjson.encode({ message = "Alert activated for " .. target_endpoint }))
