// Options page script for Content Shield
// Manages keyword list and filter mode settings

// Cross-browser compatibility
if (typeof browser !== 'undefined' && !window.chrome) {
  window.chrome = browser;
}

const keywordsListDiv = document.getElementById('keywordsList');
const addKeywordBtn = document.getElementById('addKeyword');
const saveBtn = document.getElementById('save');
const filterModeSelect = document.getElementById('filterMode');
const statusDiv = document.getElementById('status');

let currentKeywords = [];

// Load existing settings on page load
document.addEventListener('DOMContentLoaded', () => {
  loadSettings();
});

// Load settings from storage
function loadSettings() {
  chrome.storage.sync.get(['keywords', 'filterMode'], (data) => {
    currentKeywords = data.keywords || [];
    const filterMode = data.filterMode || 'blur';
    
    console.log('Content Shield Options: Loaded settings', data);
    
    // Set filter mode
    filterModeSelect.value = filterMode;
    
    // Render keywords
    renderKeywords();
  });
}

// Render keyword list
function renderKeywords() {
  keywordsListDiv.innerHTML = '';
  
  if (currentKeywords.length === 0) {
    keywordsListDiv.innerHTML = '<div class="empty-state">No keywords added yet. Click "+ Add Keyword" to get started.</div>';
    return;
  }
  
  currentKeywords.forEach((keyword, index) => {
    const row = createKeywordRow(keyword, index);
    keywordsListDiv.appendChild(row);
  });
}

// Create a keyword row element
function createKeywordRow(keyword, index) {
  const row = document.createElement('div');
  row.className = 'keyword-row';
  
  const input = document.createElement('input');
  input.type = 'text';
  input.value = keyword;
  input.placeholder = 'Enter keyword to block';
  input.dataset.index = index;
  
  const deleteBtn = document.createElement('button');
  deleteBtn.textContent = 'Delete';
  deleteBtn.onclick = () => deleteKeyword(index);
  
  row.appendChild(input);
  row.appendChild(deleteBtn);
  
  return row;
}

// Add new keyword row
addKeywordBtn.addEventListener('click', () => {
  currentKeywords.push('');
  renderKeywords();
  
  // Focus on the new input
  const inputs = keywordsListDiv.querySelectorAll('input');
  if (inputs.length > 0) {
    inputs[inputs.length - 1].focus();
  }
});

// Delete keyword
function deleteKeyword(index) {
  currentKeywords.splice(index, 1);
  renderKeywords();
}

// Save settings
saveBtn.addEventListener('click', () => {
  // Collect all keyword inputs
  const inputs = keywordsListDiv.querySelectorAll('input');
  const keywords = Array.from(inputs)
    .map(input => input.value.trim())
    .filter(keyword => keyword.length > 0); // Remove empty strings
  
  const filterMode = filterModeSelect.value;
  
  // Save to storage
  chrome.storage.sync.set({
    keywords: keywords,
    filterMode: filterMode
  }, () => {
    console.log('Content Shield Options: Settings saved', { keywords, filterMode });
    
    // Show success message
    statusDiv.textContent = `Settings saved! ${keywords.length} keyword(s) will be blocked. Refresh pages to see changes.`;
    statusDiv.style.display = 'block';
    
    // Update current keywords
    currentKeywords = keywords;
    renderKeywords();
    
    // Hide status after 5 seconds
    setTimeout(() => {
      statusDiv.style.display = 'none';
    }, 5000);
    
    // Notify all tabs to refilter
    chrome.tabs.query({}, (tabs) => {
      tabs.forEach((tab) => {
        chrome.tabs.sendMessage(tab.id, { action: 'refilter' }, () => {
          // Ignore errors for tabs that don't have content script
          if (chrome.runtime.lastError) {
            console.log('Could not send message to tab', tab.id);
          }
        });
      });
    });
  });
});

// Save on Enter key in input fields
keywordsListDiv.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    saveBtn.click();
  }
});
