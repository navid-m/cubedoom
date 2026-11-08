-- cubedoom_map.lua
-- A hand-authored 32x32 cell arena for the cubedoom raycaster.
-- Every wall, pillar and room edge is snapped to the 64-unit cell grid so the
-- game can turn the Valve 220 .map into its collision / raycast grid at load
-- time. Textures use the Quake 101 set shipped in ./textures/QUAKE101.

MOD = {
    name = "Cubedoom Arena",
    description = "A 32x32 Quake-textured arena with four rooms, a central ring and a stone heart.",
    params = {
        { key = "scale", label = "Texture scale", type = "number", default = 0.25, min = 0.05, step = 0.05 },
    },
}

local Level = {}

local CELL = 64
local WALL_H = 128
local W = 32
local H = 32

local TEX = {
    tech = "quake/tech08_2",
    stone = "quake/dung01_1",
    metal = "quake/tech07_2",
    floor = "quake/floor01_5",
    ceiling = "quake/tech08_2",
}

local MATERIAL = {
    ["#"] = TEX.tech,
    ["%"] = TEX.stone,
    ["M"] = TEX.metal,
}

local function must(value, label)
    if value == nil then
        error("cubedoom arena: " .. label .. " failed", 2)
    end
    return value
end

local function make_grid()
    local grid = {}
    for y = 0, H - 1 do
        grid[y] = {}
        for x = 0, W - 1 do
            grid[y][x] = "#"
        end
    end
    return grid
end

local function carve(grid, x0, y0, x1, y1)
    for y = math.max(0, y0), math.min(H - 1, y1) do
        for x = math.max(0, x0), math.min(W - 1, x1) do
            grid[y][x] = "."
        end
    end
end

local function fill(grid, x0, y0, x1, y1, ch)
    for y = math.max(0, y0), math.min(H - 1, y1) do
        for x = math.max(0, x0), math.min(W - 1, x1) do
            grid[y][x] = ch
        end
    end
end

local function paint_edges(grid, x0, y0, x1, y1, ch)
    for y = math.max(0, y0 - 1), math.min(H - 1, y1 + 1) do
        for x = math.max(0, x0 - 1), math.min(W - 1, x1 + 1) do
            if grid[y][x] ~= "." then
                grid[y][x] = ch
            end
        end
    end
end

local function build_layout()
    local g = make_grid()

    -- Corner rooms, the north / south halls, and the central arena.
    local rooms = {
        { 3, 3, 9, 8, "%" },     -- north-west
        { 22, 3, 28, 8, "%" },   -- north-east
        { 3, 23, 9, 28, "M" },   -- south-west (player start)
        { 22, 23, 28, 28, "M" }, -- south-east
        { 13, 3, 18, 7, "%" },   -- north hall
        { 13, 24, 18, 28, "M" }, -- south hall
    }

    for _, r in ipairs(rooms) do
        carve(g, r[1], r[2], r[3], r[4])
    end

    -- The ring corridor wraps the arena and joins all four corner rooms.
    carve(g, 9, 9, 10, 22)
    carve(g, 21, 9, 22, 22)
    carve(g, 9, 9, 22, 10)
    carve(g, 9, 21, 22, 22)

    -- Short cuts between the corner rooms and the north / south halls.
    carve(g, 9, 5, 12, 6)
    carve(g, 18, 5, 21, 6)
    carve(g, 9, 25, 12, 26)
    carve(g, 18, 25, 21, 26)

    -- Arena shell, with wide doorways on all four sides.
    carve(g, 11, 11, 20, 20)
    fill(g, 11, 11, 20, 11, "#")
    fill(g, 11, 20, 20, 20, "#")
    fill(g, 11, 11, 11, 20, "#")
    fill(g, 20, 11, 20, 20, "#")
    carve(g, 15, 11, 16, 11)
    carve(g, 15, 20, 16, 20)
    carve(g, 11, 15, 11, 16)
    carve(g, 20, 15, 20, 16)

    -- Connect the halls to the ring.
    carve(g, 15, 8, 16, 9)
    carve(g, 15, 22, 16, 24)

    -- Four pillars in the arena plus one marker pillar in each corner room.
    fill(g, 13, 13, 13, 13, "M")
    fill(g, 18, 13, 18, 13, "M")
    fill(g, 13, 18, 13, 18, "M")
    fill(g, 18, 18, 18, 18, "M")
    fill(g, 5, 5, 5, 5, "M")
    fill(g, 26, 5, 26, 5, "M")
    fill(g, 5, 26, 5, 26, "M")
    fill(g, 26, 26, 26, 26, "M")

    -- Give every room a matching wall material.
    for _, r in ipairs(rooms) do
        paint_edges(g, r[1], r[2], r[3], r[4], r[5])
    end
    paint_edges(g, 11, 11, 20, 20, "%")

    return g
end

local function set_used(used, x, y, w, h)
    for yy = y, y + h - 1 do
        for xx = x, x + w - 1 do
            used[yy][xx] = true
        end
    end
end

local function row_matches(grid, used, x, y, w, ch)
    for xx = x, x + w - 1 do
        if grid[y][xx] ~= ch or used[y][xx] then
            return false
        end
    end
    return true
end

local function build_walls(grid)
    local used = {}
    for y = 0, H - 1 do
        used[y] = {}
    end

    local brushes = {}
    for y = 0, H - 1 do
        for x = 0, W - 1 do
            local ch = grid[y][x]
            if ch ~= "." and not used[y][x] then
                local w = 1
                while x + w < W and grid[y][x + w] == ch and not used[y][x + w] do
                    w = w + 1
                end

                local h = 1
                while y + h < H and row_matches(grid, used, x, y + h, w, ch) do
                    h = h + 1
                end

                set_used(used, x, y, w, h)
                brushes[#brushes + 1] = must(xmap.make_box(
                    { x * CELL, y * CELL, 0 },
                    { (x + w) * CELL, (y + h) * CELL, WALL_H },
                    MATERIAL[ch]
                ), "wall brush")
            end
        end
    end
    return brushes
end

local function point_entity(classname, cell_x, cell_y, extra)
    local props = extra or {}
    return must(xmap.make_point_entity(
        classname,
        { cell_x * CELL + CELL * 0.5, cell_y * CELL + CELL * 0.5, 32 },
        props
    ), classname)
end

function Level.generate(params)
    local scale = params.scale or 0.25
    local g = build_layout()
    local walls = build_walls(g)
    local result = {}

    result[#result + 1] = must(xmap.make_box(
        { 0, 0, -16 },
        { W * CELL, H * CELL, 0 },
        TEX.floor
    ), "floor")
    result[#result + 1] = must(xmap.make_box(
        { 0, 0, WALL_H },
        { W * CELL, H * CELL, WALL_H + 16 },
        TEX.ceiling
    ), "ceiling")

    for _, brush in ipairs(walls) do
        result[#result + 1] = brush
    end

    -- Player start, facing east into the south-west room.
    result[#result + 1] = must(xmap.make_spawn(
        { 6 * CELL + CELL * 0.5, 26 * CELL + CELL * 0.5, 32 },
        { angle = "0" }
    ), "player start")

    -- Six monsters spread over the rooms and the arena.
    local monsters = {
        { 6, 5 },
        { 25, 6 },
        { 15, 5 },
        { 17, 17 },
        { 15, 26 },
        { 26, 25 },
    }
    for _, m in ipairs(monsters) do
        result[#result + 1] = point_entity("monster_army", m[1], m[2], { angle = "180" })
    end

    -- Quake-style lights keep the map useful when opened in an editor.
    local lights = {
        { 6, 5, 320 },
        { 25, 5, 320 },
        { 15, 4, 300 },
        { 15, 15, 420 },
        { 6, 26, 320 },
        { 15, 27, 300 },
        { 25, 26, 320 },
        { 15, 17, 360 },
    }
    for _, l in ipairs(lights) do
        result[#result + 1] = must(xmap.make_light(
            { l[1] * CELL + CELL * 0.5, l[2] * CELL + CELL * 0.5, l[3] },
            { light = 280 }
        ), "light")
    end

    xmap.set_texture_scales(result, scale)

    local invalid = 0
    for index, item in ipairs(result) do
        if xmap.is_brush(item) then
            local valid, diagnostics = xmap.validate_brush(item)
            if not valid then
                invalid = invalid + 1
                for _, d in ipairs(diagnostics) do
                    xmap.warn(string.format("brush %d: %s (%s)", index, d.message, d.code))
                end
            end
        end
    end
    if invalid > 0 then
        error(string.format("cubedoom arena produced %d invalid brush(es)", invalid))
    end

    print(string.format("Cubedoom Arena: %d wall brushes, %dx%d cells, texture scale %.3f",
        #walls, W, H, scale))
    return result
end

return Level
