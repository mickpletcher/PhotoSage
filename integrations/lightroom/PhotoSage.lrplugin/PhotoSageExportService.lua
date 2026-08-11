local LrDialogs = import "LrDialogs"
local LrPathUtils = import "LrPathUtils"
local LrTasks = import "LrTasks"

local provider = {}

function provider.processRenderedPhotos(functionContext, exportContext)
    local session = exportContext.exportSession
    local destination = nil
    for _, rendition in session:renditions() do
        local success, pathOrMessage = rendition:waitForRender()
        if success and not destination then
            destination = LrPathUtils.parent(pathOrMessage)
        end
    end
    if not destination then
        LrDialogs.message("PhotoSage", "No rendered photos were available.", "warning")
        return
    end
    local command = 'photosage lightroom-process --input "' .. destination .. '" --preview'
    local result = LrTasks.execute(command)
    if result ~= 0 then
        LrDialogs.message("PhotoSage", "Preview failed. Run the command manually:\n" .. command, "critical")
    else
        LrDialogs.message("PhotoSage", "A review manifest was created. No files were renamed.", "info")
    end
end

return provider
