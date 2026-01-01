// Popup script for Content Shield
// Displays extension status and provides quick access to settings

// Cross-browser compatibility
if (typeof browser !== 'undefined' && !window.chrome) {
  window.chrome = browser;
}

const statusDiv = document.getElementById('status');
const quickAddBtn = document.getElementById('quickAdd');
const quickKeywordInput = document.getElementById('quickKeywordInput');
const successMessage = document.getElementById('successMessage');
const keywordsListDiv = document.getElementById('keywordsList');
const noKeywordsDiv = document.getElementById('noKeywords');

// Load extension status on popup open
document.addEventListener('DOMContentLoaded', () => {
  loadStatus();
  renderKeywords();
});

// Load and display current status
function loadStatus() {
  chrome.storage.sync.get(['keywords', 'filterMode'], (data) => {
    const keywords = data.keywords || [];
    const filterMode = data.filterMode || 'blur';
    
    const count = keywords.length;
    const modeText = {
      'blur': 'Blurring',
      'censor': 'Censoring',
      'remove': 'Removing'
    }[filterMode] || 'Filtering';
    
    if (count === 0) {
      statusDiv.textContent = 'No keywords configured. Add one using the box above.';
    } else {
      statusDiv.textContent = `${modeText} ${count} keyword${count !== 1 ? 's' : ''}: ${keywords.slice(0, 3).join(', ')}${count > 3 ? '...' : ''}`;
    }
    // Update keywords list in popup
    populateKeywordsList(keywords);
    
    console.log('Content Shield Popup: Status loaded', { keywords, filterMode });
  });
}

// (Settings button removed — quick add and inline edits available in popup)

// Quick add keyword
quickAddBtn.addEventListener('click', () => {
  const keyword = quickKeywordInput.value.trim();
  
  if (keyword.length === 0) {
    alert('Please enter a keyword to block');
    return;
  }
  
  // Get current keywords and add new one
  chrome.storage.sync.get(['keywords'], (data) => {
    const keywords = data.keywords || [];
    
    // Check if keyword already exists
    if (keywords.includes(keyword)) {
      alert('This keyword is already in your list');
      return;
    }
    
    // Add new keyword
    keywords.push(keyword);
    
    // Save updated keywords
    chrome.storage.sync.set({ keywords }, () => {
      console.log('Content Shield Popup: Keyword added', keyword);
      
      // Clear input
      quickKeywordInput.value = '';
      
      // Show success message
      successMessage.style.display = 'block';
      setTimeout(() => {
        successMessage.style.display = 'none';
      }, 2000);
      
      // Update status
      loadStatus();
      
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
});

// Add keyword on Enter key
quickKeywordInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    quickAddBtn.click();
  }
});

// Render keywords area
function renderKeywords() {
  chrome.storage.sync.get(['keywords'], (data) => {
    const keywords = data.keywords || [];
    populateKeywordsList(keywords);
  });
}

function populateKeywordsList(keywords) {
  if (!keywordsListDiv) return;
  keywordsListDiv.innerHTML = '';

  if (keywords.length === 0) {
    noKeywordsDiv.style.display = 'block';
    return;
  }

  noKeywordsDiv.style.display = 'none';

  keywords.forEach((kw, idx) => {
    const row = document.createElement('div');
    row.className = 'keyword-row';
    row.style.display = 'flex';
    row.style.gap = '8px';
    row.style.marginBottom = '8px';

    const input = document.createElement('input');
    input.type = 'text';
    input.value = kw;
    input.style.flex = '1';
    input.style.padding = '8px';
    input.style.fontSize = '13px';
    input.style.background = '#070707';
    input.style.color = '#e6eef8';
    input.style.border = '1px solid #222';
    input.style.borderRadius = '6px';

    // Save on blur or Enter
    input.addEventListener('blur', () => saveKeywordEdit(idx, input.value.trim()));
    input.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        input.blur();
      }
    });

    const del = document.createElement('button');
    del.textContent = 'Delete';
    del.className = 'kw-delete';
    del.style.padding = '6px 10px';
    del.style.borderRadius = '6px';
    del.addEventListener('click', () => deleteKeywordAt(idx));

    row.appendChild(input);
    row.appendChild(del);

    keywordsListDiv.appendChild(row);
  });
}

function saveKeywordEdit(index, newValue) {
  chrome.storage.sync.get(['keywords'], (data) => {
    const keywords = data.keywords || [];
    if (!Array.isArray(keywords)) return;

    // If empty -> remove
    if (newValue.length === 0) {
      keywords.splice(index, 1);
    } else {
      keywords[index] = newValue;
    }

    chrome.storage.sync.set({ keywords }, () => {
      renderKeywords();
      // Notify tabs
      chrome.tabs.query({}, (tabs) => {
        tabs.forEach((tab) => {
          chrome.tabs.sendMessage(tab.id, { action: 'refilter' }, () => {});
        });
      });
    });
  });
}

function deleteKeywordAt(index) {
  chrome.storage.sync.get(['keywords'], (data) => {
    const keywords = data.keywords || [];
    keywords.splice(index, 1);
    chrome.storage.sync.set({ keywords }, () => {
      renderKeywords();
      chrome.tabs.query({}, (tabs) => {
        tabs.forEach((tab) => {
          chrome.tabs.sendMessage(tab.id, { action: 'refilter' }, () => {});
        });
      });
    });
  });
}
