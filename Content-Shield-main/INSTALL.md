# Quick Installation & Testing Guide

## Step 1: Load the Extension

### For Chrome / Edge / Brave:
1. Open your browser
2. Navigate to: `chrome://extensions/` (or `edge://extensions/` for Edge)
3. Enable **Developer mode** (toggle switch in top-right)
4. Click **"Load unpacked"**
5. Select this folder: `content-shield`
6. ✅ Extension should now appear with a shield icon

### For Firefox:
1. Open Firefox
2. Navigate to: `about:debugging#/runtime/this-firefox`
3. Click **"Load Temporary Add-on..."**
4. Navigate to the `content-shield` folder
5. Select the `manifest.json` file
6. ✅ Extension should now appear (temporary until browser restart)

**Note:** For permanent Firefox installation, the extension needs to be signed by Mozilla or use Firefox Developer Edition.

## Step 2: Quick Test

1. **Add a test keyword:**
   - Click the Content Shield icon in your toolbar
   - Type "test" in the quick add field
   - Click "Add Keyword"

2. **Test the filtering:**
   - Open a new tab
   - Go to any website (e.g., Google)
   - Search for "test"
   - You should see search results blurred!
   - Click on blurred content to reveal it

## Step 3: Test Dynamic Content (YouTube)

1. **Add a popular keyword:**
   - Click Content Shield icon
   - Add keyword: "music" or "gaming"

2. **Test on YouTube:**
   - Go to youtube.com
   - Videos with "music" in the title should be blurred
   - Scroll down - new recommendations should also be filtered
   - This proves MutationObserver is working!

## Step 4: Test Filter Modes

1. **Try different filter modes:**
   - Click Content Shield icon → "Open Settings"
   - Change filter mode to "Censor with black bar"
   - Refresh a page with filtered content
   - Content should now show as black bars
   - Try "Remove completely" mode - content disappears!

## Step 5: Test Real-time Updates

1. Open a page with some keywords
2. Add a NEW keyword via popup (without refreshing)
3. New content matching that keyword should be filtered immediately
4. This proves message passing works!

## Common Test Keywords

- **For YouTube:** "music", "gaming", "vlog", "tutorial"
- **For Reddit:** "politics", "news", "AskReddit"  
- **For spoilers:** "Stranger Things", "Game of Thrones", "Marvel"

## Verification Checklist

- [ ] Extension loads without errors
- [ ] Popup opens and shows keyword count
- [ ] Can add keywords via popup
- [ ] Can add keywords via settings page
- [ ] Settings save and persist
- [ ] Blur mode works (content blurred, click reveals)
- [ ] Censor mode works (black bar, click reveals)
- [ ] Remove mode works (content deleted)
- [ ] Dynamic content filtered (YouTube scroll)
- [ ] Works on multiple websites
- [ ] Console shows "Content Shield:" messages
- [ ] No errors in browser console

## Troubleshooting

### "Failed to load extension"
- Check all files are in the correct location
- Verify manifest.json has no syntax errors
- Ensure icon128.png exists in icons folder

### "Extension loads but doesn't filter"
- Open DevTools (F12) → Console tab
- Look for "Content Shield:" messages
- Verify keywords are saved (check popup)
- Try refreshing the page

### "Console errors"
- Check which file is causing the error
- Verify all permissions in manifest.json
- Make sure content.js is loaded on the page

## Debug Mode

To see detailed logs:
1. Open any webpage
2. Press F12 to open DevTools
3. Go to Console tab
4. Look for messages starting with "Content Shield:"
5. You should see:
   - "Initializing content filter"
   - "Loaded X keyword(s)"
   - "Scanning existing content"
   - "Found X element(s) to filter"
   - "MutationObserver initialized"

## Success Indicators

✅ **Working correctly if:**
- No errors in console
- Keywords save and display in popup
- Content with keywords is filtered
- New content (YouTube scroll) gets filtered
- Click-to-reveal works
- Filter mode changes take effect

---

**Your extension is ready to use!** 🎉

Add your favorite spoiler keywords and browse worry-free!
