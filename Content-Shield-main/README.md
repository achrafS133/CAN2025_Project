# 🛡️ Content Shield

**Block spoilers and unwanted content before you see them.**

Content Shield is a lightweight, cross-browser extension that automatically filters web content based on keywords you define. Perfect for avoiding TV show spoilers, hiding news topics, or creating a distraction-free browsing experience.

## ✨ Key Features

- **🌊 Works with Dynamic Content** - Automatically filters YouTube Shorts, and live-updating feeds
- **✏️ Easy Management** - Add, edit, or delete keywords directly from the popup
- **🔒 100% Private** - All data stored locally in your browser, no tracking
- **🌐 Works Everywhere** - YouTube, Reddit, Twitter/X, Facebook, news sites, and any web page
- **🦊 Cross-Browser** - Compatible with Chrome, Edge, Brave, and Firefox
- **⚡ Instant Filtering** - Content is filtered as pages load, before you see spoilers
- **🎨 Three Filter Modes:**
  - **Blur** (default): Content is blurred and clickable to reveal
  - **Censor**: Content is covered with black bar, click to reveal
  - **Remove**: Content is completely removed from the page


## 🚀 Quick Start

### Installation

#### Chrome / Edge / Brave
1. Download or clone this repository
2. Open your browser and go to:
   - Chrome: `chrome://extensions/`
   - Edge: `edge://extensions/`
   - Brave: `brave://extensions/`
3. Enable **Developer mode** (toggle in top-right)
4. Click **Load unpacked**
5. Select the `content-shield` folder
6. ✅ Done! Extension icon should appear in your toolbar

#### Firefox
1. Download or clone this repository
2. Open Firefox and go to: `about:debugging#/runtime/this-firefox`
3. Click **Load Temporary Add-on...**
4. Navigate to the `content-shield` folder and select `manifest.json`
5. ✅ Done! (Note: Temporary in Firefox - removed on browser restart)

> **Firefox Note:** For permanent installation, use Firefox Developer Edition or sign the extension through Mozilla.

### How to Use

**Adding Your First Keyword:**
1. Click the Content Shield icon in your toolbar
2. Type a keyword in the "Quick add keyword..." box (e.g., "Stranger Things")
3. Press Enter or click "Add Keyword"
4. Browse any website - content with that keyword will be blurred!

**Managing Your Keywords:**
- **Edit**: Click any keyword in the list, modify it, and press Enter
- **Delete**: Click the "Delete" button next to any keyword
- **View All**: Open the popup to see all your blocked keywords at once

**Revealing Filtered Content:**
- Click any blurred or censored content to reveal it temporarily
- The filter is removed for that specific item until the page reloads

### Common Use Cases

- 🎬 **Avoid spoilers** for shows you haven't watched yet
- 📰 **Hide news topics** you want to avoid
- 🎮 **Block game spoilers** before you finish playing
- 🏆 **Hide sports scores** until you watch the game
- 🎭 **Filter celebrity names** or topics you're tired of seeing

## ⚙️ Advanced Settings

Access advanced options by clicking "Open Settings" in the popup.

**Filter Modes:**
- **Blur** (18px): Heavily blurs content - click to reveal

**Keyword Tips:**
- ✅ Keywords are **case-insensitive** ("spoiler" = "SPOILER")
- ✅ **Space-flexible** matching ("stranger things" matches "strangerthings")
- ✅ **Partial matching** enabled ("Potter" matches "Harry Potter")
- ✅ Use **specific phrases** for precise filtering
- ⚠️ Changes apply immediately to all open tabs

## 🔍 How It Works

Content Shield uses advanced web technologies to filter content efficiently:

1. **Early Detection** - Content script runs at `document_start` before content renders
2. **Smart Scanning** - Targets titles, headings, links, and text elements (not all text)
3. **Dynamic Monitoring** - MutationObserver watches for new content (YouTube Shorts, infinite scroll)
4. **URL-Based Filtering** - Detects navigation changes in single-page apps and re-evaluates content
5. **Selective Filtering** - Only filters elements that match your keywords (verified on every scroll)
6. **Performance Optimized** - Uses WeakSet to avoid reprocessing nodes, minimal memory footprint

### Tested On
- ✅ YouTube (homepage, watch page, Shorts)
- ✅ Reddit (posts, comments, feeds)
- ✅ Twitter/X (timeline, profiles)
- ✅ Facebook (news feed, groups)
- ✅ Google Search Results
- ✅ News sites and blogs
- ✅ Any website with text content

## 🛠️ Troubleshooting

**Content not being filtered?**
- Check if keywords are saved (open popup to verify)
- Try adding more specific keywords
- Check browser console (F12) for "Content Shield:" debug messages
- Ensure extension is enabled in your browser's extensions page

**Some YouTube Shorts not filtered?**
- Keywords are matched when you scroll to a new short
- Try refreshing the page if a short was missed
- Check that your keyword matches the video title/caption

**Filtered content showing briefly before blurring?**
- Normal for very fast page loads
- Extension filters as early as possible, but some content may flash briefly

**Keywords not syncing across devices?**
- Ensure you're logged into your browser account
- Chrome/Edge use `chrome.storage.sync` for automatic syncing

## 🧑‍💻 For Developers

### Technical Architecture

- **Manifest V3** - Modern Chrome extension format with cross-browser support
- **Content Script** (`content.js`) - Runs on all pages, filters DOM content in real-time
- **Background Script** (`background.js`) - Service worker for extension lifecycle
- **Storage API** - Uses `chrome.storage.sync` for cross-device keyword syncing
- **MutationObserver** - Monitors DOM changes for dynamic content filtering
- **Cross-Browser Compatible** - Polyfill for Firefox `browser` API

### Project Structure

```
content-shield/
├── manifest.json          # Extension configuration
├── content.js             # Core filtering logic
├── background.js          # Service worker
├── popup.html/js          # Popup interface (keyword management)
├── options.html/js        # Settings page
├── icons/                 # Extension icons
├── README.md              # This file
└── INSTALL.md             # Detailed installation guide
```

### Making Changes

1. Edit source files
2. Go to `chrome://extensions/` (or your browser's extension page)
3. Click the refresh icon on Content Shield
4. Test your changes

**Debug Logging:** All actions are logged with "Content Shield:" prefix in the browser console (F12).

## 🤝 Contributing

Contributions are welcome! Ideas for features:
- Domain whitelist/blacklist
- Regex pattern support
- Customizable blur intensity
- Keyword categories/groups
- Import/export keyword lists
- Temporary disable per-tab

## 📝 License

Open source - free to use, modify, and distribute.

---

**Need Help?** 
- Check browser console (F12) for debug messages
- Verify keywords in the popup
- See [INSTALL.md](INSTALL.md) for detailed setup instructions
