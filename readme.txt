Makes path of exile (pathofexile.com) a bit less boring to play.



# FEATURE track xp/hr in 15/45/135min increments
# FEATURE time remaining to level up for levels >= 90
# FEATURE xp to next and previous rank (how much someone is leading or trailing)
# FEATURE UI shows current counts of each chaos recipe item
# FEATURE UI shows needed/missing items to complete eg. 5 chaos recipes
# FEATURE UI chaos recipe button moves 1 completed recipe to inventory
# basically does item sorting for you
# note: only tested on 1920x1080 screen resolution when game is windowed
# FEATURE UI chaos recipe button becomes '+' only if there's enough items AND there are enough
# stash items after an API update. In other words, the + should clear after
# it was clicked until an API update (small unavoidable race condition - API updates
# while chaos items are being moved out of stash tab for a recipe leading to incorrect counts)
# FEATURE UI button becomes 'o' when clicked to show we are waiting for an API update with new items
# FEATURE UI warning when dump tab contains some unknown and identified items
# FEATURE UI always on top
# FEATURE UI right click quit menu
# FEATURE don't poll APIs when POE is not found
# FEATURE poestash should tag items when it categorizes them, so the uncategorized ones can be counted. eg 'poexp_found' = True
# FEATURE poestash categorizes items for different recipes
# FEATURE gemcutter recipe stash scan and clicker. 20 qual single and 40 qual multi gem
# skips enlighten, empower, enhance, because they are expensive
# FEATURE gems don't count as identified items that should be removed from dump tab
# FEATURE gcp count in info bar
# FEATURE stash count 6s and 6l items
# FEATURE six link items handling? see PoeStash.six_link_items; click 6s items, skip 6l
# FEATURE chromatics items (rgb) should be moved to inventory when 5+. only normal and magic items < 6 sockets
# FEATURE try to work on lists of recipes instead of enumerating individual ones
# FEATURE pick up maps from dump tab. only when 10+
# FEATURE pick up div cards from dump tab. only when 10+ stacks
# FEATURE currency stash scan. pick up when > 10c
# FEATURE start using STASH_FRAME_TYPE for filtering items. the `category` property is gone
# FEATURE use item icons for filtering items. the category property is gone
# FEATURE color UI needed items in different colors, similar to filter
# FEATURE video that showcases some old version
