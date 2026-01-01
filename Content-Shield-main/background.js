// Service Worker for Content Shield
// Handles background tasks and message routing

// Cross-browser compatibility
if (typeof browser !== 'undefined' && !self.chrome) {
  self.chrome = browser;
}

console.log('Content Shield: Service worker initialized');

chrome.runtime.onInstalled.addListener((details) => {
  console.log('Content Shield: Extension installed/updated', details);
  
  // Initialize default values if not set
  chrome.storage.sync.get(['keywords', 'filterMode'], (data) => {
    if (!data.keywords) {
      chrome.storage.sync.set({
        keywords: [],
        filterMode: 'blur'
      }, () => {
        console.log('Content Shield: Default settings initialized');
      });
    } else {
      console.log('Content Shield: Existing settings found');
    }
  });
});

// Optional: Handle messages from content scripts or popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('Content Shield: Background received message', message);
  sendResponse({ success: true });
});
