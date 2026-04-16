hs.window.animationDuration = 0

local TOLERANCE = 8
local FRAC_TOLERANCE = 0.02
local GRID_POINTS = {0, 1/4, 1/3, 1/2, 2/3, 3/4, 1}
local MOD = {"cmd", "alt"}
local MOD_SHIFT = {"cmd", "alt", "shift"}

local function nearestGridPoint(frac)
  local best, bestDist = nil, math.huge
  for _, gp in ipairs(GRID_POINTS) do
    local d = math.abs(frac - gp)
    if d < bestDist then best, bestDist = gp, d end
  end
  return best, bestDist
end

local function fracEq(a, b)
  return math.abs(a - b) < FRAC_TOLERANCE
end

local function slotWidth(slot)
  return slot.right - slot.left
end

local function getGridSlot(win)
  local f = win:frame()
  local sf = win:screen():frame()
  if math.abs(f.y - sf.y) > TOLERANCE or math.abs(f.h - sf.h) > TOLERANCE then
    return nil
  end
  local leftFrac = (f.x - sf.x) / sf.w
  local rightFrac = (f.x + f.w - sf.x) / sf.w
  local snapLeft, dLeft = nearestGridPoint(leftFrac)
  local snapRight, dRight = nearestGridPoint(rightFrac)
  if dLeft * sf.w > TOLERANCE or dRight * sf.w > TOLERANCE then
    return nil
  end
  return {left = snapLeft, right = snapRight}
end

local function getSnappedWindows(screen)
  local wins = {}
  for _, w in ipairs(hs.window.visibleWindows()) do
    if w:screen() == screen and w:isStandard() then
      local slot = getGridSlot(w)
      if slot then
        table.insert(wins, {win = w, slot = slot})
      end
    end
  end
  table.sort(wins, function(a, b) return a.slot.left < b.slot.left end)
  return wins
end

local function setSlot(win, screen, left, right)
  local sf = screen:frame()
  win:setFrame({
    x = sf.x + left * sf.w,
    y = sf.y,
    w = (right - left) * sf.w,
    h = sf.h,
  })
  win:raise()
end

local function picker(callback)
  local c = hs.chooser.new(callback)
  local choices = {}
  for _, w in ipairs(hs.window.visibleWindows()) do
    if w:isStandard() then
      local title = w:title()
      local app = w:application():name()
      local label = (title and title ~= "") and (app .. " — " .. title) or app
      table.insert(choices, {text = label, winId = w:id()})
    end
  end
  c:choices(choices)
  c:show()
end

local function pickerAndPlace(screen, left, right, originalWin)
  picker(function(choice)
    if not choice then return end
    local w = hs.window.get(choice.winId)
    if w then
      setSlot(w, screen, left, right)
      if originalWin then originalWin:raise() end
    end
  end)
end

local function cycleWidth(slot)
  local w = slotWidth(slot)
  if fracEq(w, 1/2) then return 1/3 end
  if fracEq(w, 1/3) then return 2/3 end
  return 1/2
end

-- cmd+alt+d: split rightward
hs.hotkey.bind(MOD, "d", function()
  local win = hs.window.focusedWindow()
  if not win then return end
  local screen = win:screen()
  local slot = getGridSlot(win)

  if not slot then
    setSlot(win, screen, 0, 1/2)
    pickerAndPlace(screen, 1/2, 1, win)
    return
  end

  local w = slotWidth(slot)

  if w <= 1/4 + FRAC_TOLERANCE then
    hs.alert.show("Already at max density", 1)
    return
  end

  if fracEq(w, 1/2) then
    local mid = slot.left + 1/4
    setSlot(win, screen, slot.left, mid)
    pickerAndPlace(screen, mid, slot.right, win)
    return
  end

  if fracEq(w, 1/3) then
    local snapped = getSnappedWindows(screen)
    for i, sw in ipairs(snapped) do
      setSlot(sw.win, screen, (i-1)/4, i/4)
    end
    local nextSlot = #snapped / 4
    pickerAndPlace(screen, nextSlot, nextSlot + 1/4, win)
    return
  end

  setSlot(win, screen, 0, 1/2)
  pickerAndPlace(screen, 1/2, 1, win)
end)

-- cmd+alt+e: equalize snapped windows
hs.hotkey.bind(MOD, "e", function()
  local win = hs.window.focusedWindow()
  if not win then return end
  local screen = win:screen()
  local snapped = getSnappedWindows(screen)
  local n = #snapped
  if n == 0 then return end
  for i, sw in ipairs(snapped) do
    setSlot(sw.win, screen, (i-1)/n, i/n)
  end
end)

-- cmd+alt+f: fullscreen
hs.hotkey.bind(MOD, "f", function()
  local win = hs.window.focusedWindow()
  if not win then return end
  setSlot(win, win:screen(), 0, 1)
end)

-- cmd+alt+left: left-anchored, cycle 1/2 → 1/3 → 1/4 → 1/2
hs.hotkey.bind(MOD, "left", function()
  local win = hs.window.focusedWindow()
  if not win then return end
  local screen = win:screen()
  local slot = getGridSlot(win)

  if slot and fracEq(slot.left, 0) then
    local newWidth = cycleWidth(slot)
    setSlot(win, screen, 0, newWidth)
  else
    setSlot(win, screen, 0, 1/2)
  end
end)

-- cmd+alt+right: right-anchored, cycle 1/2 → 1/3 → 1/4 → 1/2
hs.hotkey.bind(MOD, "right", function()
  local win = hs.window.focusedWindow()
  if not win then return end
  local screen = win:screen()
  local slot = getGridSlot(win)

  if slot and fracEq(slot.right, 1) then
    local newWidth = cycleWidth(slot)
    setSlot(win, screen, 1 - newWidth, 1)
  else
    setSlot(win, screen, 1/2, 1)
  end
end)
