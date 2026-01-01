// Content Shield - Content Script for filtering web page content
// This script runs on every page and filters content based on user-defined keywords

(function() {
  'use strict';

  // Cross-browser compatibility
  if (typeof browser !== 'undefined' && !window.chrome) {
    window.chrome = browser;
  }

  let keywords = [];
  let filterMode = 'blur';
  let keywordPattern = null;
  let observer = null;
  const processedNodes = new WeakSet();
  const filteredNodes = new WeakSet(); // Track nodes that have filters applied
  let currentUrl = window.location.href;
  let urlCheckInterval = null;

  // Initialize the content filter
  function init() {
    console.log('Content Shield: Initializing content filter');
    
    // Check document ready state
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', loadSettingsAndFilter);
    } else {
      loadSettingsAndFilter();
    }
    
    // Monitor URL changes (for YouTube Shorts, single-page apps)
    startUrlMonitoring();
  }

  // Monitor URL changes for single-page apps like YouTube
  function startUrlMonitoring() {
    // Check URL every 500ms for Shorts scroll detection
    urlCheckInterval = setInterval(() => {
      const newUrl = window.location.href;
      if (newUrl !== currentUrl) {
        console.log('Content Shield: URL changed, checking content');
        currentUrl = newUrl;
        
        // For YouTube Shorts, verify existing filters and filter new content
        setTimeout(() => {
          verifyAndRemoveNonMatchingFilters();
          filterExistingContent();
        }, 300);
      }
    }, 500);
    
    // Also listen to history events
    window.addEventListener('popstate', handleUrlChange);
    window.addEventListener('pushstate', handleUrlChange);
    window.addEventListener('replacestate', handleUrlChange);
  }

  function handleUrlChange() {
    const newUrl = window.location.href;
    if (newUrl !== currentUrl) {
      console.log('Content Shield: Navigation detected, verifying and filtering content');
      currentUrl = newUrl;
      setTimeout(() => {
        // First verify existing filters and remove if not matched
        verifyAndRemoveNonMatchingFilters();
        // Then filter new content
        filterExistingContent();
      }, 300);
    }
  }

  // Clear all applied filters
  function clearAllFilters() {
    // Use data attribute to find filtered elements
    document.querySelectorAll('[data-content-shield]').forEach(el => {
      el.style.filter = '';
      el.style.backgroundColor = '';
      el.style.color = '';
      el.style.cursor = '';
      el.style.pointerEvents = '';
      el.title = '';
      el.removeAttribute('data-content-shield');
    });
    
    console.log('Content Shield: Cleared all filters');
  }

  // Load settings from storage and start filtering
  function loadSettingsAndFilter() {
    chrome.storage.sync.get(['keywords', 'filterMode'], (data) => {
      keywords = data.keywords || [];
      filterMode = data.filterMode || 'blur';
      
      console.log(`Content Shield: Loaded ${keywords.length} keyword(s)`);
      console.log(`Content Shield: Filter mode set to ${filterMode}`);
      
      if (keywords.length > 0) {
        // Build case-insensitive regex pattern with space variations
        const escapedKeywords = [];
        keywords.forEach(k => {
          const escaped = k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
          escapedKeywords.push(escaped);
          // If keyword contains spaces, also add version without spaces
          if (k.includes(' ')) {
            const noSpaces = k.replace(/\s+/g, '').replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            escapedKeywords.push(noSpaces);
          }
        });
        keywordPattern = new RegExp(escapedKeywords.join('|'), 'gi');
        
        // Perform initial DOM filtering
        filterExistingContent();
        
        // Set up observer for dynamic content
        setupMutationObserver();
      }
    });
  }

  // Filter existing content using TreeWalker
  function filterExistingContent() {
    if (!document.body || !keywordPattern) return;
    
    console.log('Content Shield: Scanning existing content');
    
    const nodesToFilter = [];
    
    // Find all text-containing elements (more specific targeting)
    const selectors = [
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6',  // Headings (video titles, post titles)
      'a',                                   // Links
      'p',                                   // Paragraphs
      'span',                                // Spans (often used for titles)
      'yt-formatted-string',                 // YouTube text nodes
      '[id*="video-title"]',                 // YouTube specific
      '[id*="title"]',
      '[class*="title"]',                    // Title classes
      '[class*="headline"]',                 // Headlines
      '[class*="post"]',                     // Post content
      '[aria-label]'                         // Aria labels (often contain titles)
    ];
    
    const elements = document.querySelectorAll(selectors.join(','));
    
    elements.forEach(element => {
      if (shouldFilterElement(element)) {
        // Find the appropriate container to blur
        const targetElement = findFilterTarget(element);
        // Skip if already filtered or if it's in the list
        if (targetElement && 
            !filteredNodes.has(targetElement) && 
            !targetElement.hasAttribute('data-content-shield') &&
            !nodesToFilter.includes(targetElement)) {
          console.log('Content Shield: Adding target to filter list', targetElement.tagName, targetElement.id || targetElement.className);
          nodesToFilter.push(targetElement);
        }
      }
    });
    
    if (nodesToFilter.length > 0) {
      console.log(`Content Shield: Found ${nodesToFilter.length} new element(s) to filter`);
      nodesToFilter.forEach(node => applyFilter(node));
    }
  }

  // Check if element should be filtered (only check direct text, not all descendants)
  function shouldFilterElement(element) {
    if (!keywordPattern || processedNodes.has(element)) {
      return false;
    }
    // Get relevant text from element (direct text, aria/title/alt, and a small descendant fallback)
    const textContent = getRelevantText(element);
    return keywordPattern.test(textContent);
  }

  // Get text content without deeply nested children
  function getDirectTextContent(element) {
    let text = '';
    for (let node of element.childNodes) {
      if (node.nodeType === Node.TEXT_NODE) {
        text += node.textContent;
      } else if (node.nodeType === Node.ELEMENT_NODE && node.children.length === 0) {
        // Include leaf elements only
        text += node.textContent;
      }
    }
    return text;
  }

  // Get relevant text for matching: direct text, attributes (aria-label/title/alt),
  // and a limited descendant text fallback to catch nested YouTube titles (shorts)
  function getRelevantText(element) {
    try {
      let parts = [];

      // direct/leaf text
      const direct = getDirectTextContent(element).trim();
      if (direct) parts.push(direct);

      // attributes that often contain titles
      const attrs = ['aria-label', 'title', 'alt'];
      for (let a of attrs) {
        const v = element.getAttribute && element.getAttribute(a);
        if (v) parts.push(v);
      }

      // small descendant fallback: check common YouTube text nodes and short depth text
      if (parts.length === 0) {
        // prefer yt-formatted-string, then small spans/links
        const selectors = ['yt-formatted-string', 'span', 'a', 'p'];
        for (let sel of selectors) {
          const el = element.querySelector(sel);
          if (el && el.textContent) {
            const txt = el.textContent.trim();
            if (txt.length > 0 && txt.length < 400) {
              parts.push(txt);
              break;
            }
          }
        }
      }

      // as a last resort, include a truncated full textContent (avoid huge blobs)
      if (parts.length === 0 && element.textContent) {
        const t = element.textContent.trim();
        if (t.length > 0) parts.push(t.slice(0, 500));
      }

      return parts.join(' ');
    } catch (e) {
      return '';
    }
  }

  // Find the best element to apply filter to
  function findFilterTarget(element) {
    // For YouTube videos, find the video container
    let current = element;
    let depth = 0;
    const maxDepth = 15;
    
    while (current && depth < maxDepth) {
      const tagName = current.tagName ? current.tagName.toUpperCase() : '';
      const id = current.id || '';
      const classList = current.classList || [];
      
      // YouTube Shorts - multiple selectors
      if (tagName === 'YTD-REEL-ITEM-RENDERER' || 
          tagName === 'YTD-SHORTS' ||
          id === 'shorts-container' ||
          id.includes('shorts') ||
          current.hasAttribute('is-active') ||
          classList.contains('ytd-reel-item-renderer')) {
        console.log('Content Shield: Found YouTube Shorts container', tagName);
        return current;
      }
      
      // YouTube Shorts player wrapper
      if (id === 'shorts-player' || 
          id === 'player' ||
          classList.contains('html5-video-player')) {
        // Go up one more level to get the full container
        const parent = current.parentElement;
        if (parent && parent.tagName === 'YTD-REEL-ITEM-RENDERER') {
          console.log('Content Shield: Found Shorts via player');
          return parent;
        }
        console.log('Content Shield: Found video player container');
        return current;
      }
      
      // YouTube video renderers (home page videos)
      if (tagName === 'YTD-RICH-ITEM-RENDERER' ||
          tagName === 'YTD-VIDEO-RENDERER' ||
          tagName === 'YTD-GRID-VIDEO-RENDERER' ||
          tagName === 'YTD-COMPACT-VIDEO-RENDERER' ||
          tagName === 'YTM-REEL-ITEM-RENDERER') {
        console.log('Content Shield: Found YouTube video container', tagName);
        return current;
      }
      
      // Look for common video/content container patterns
      if (classList.contains('video-stream') ||
          classList.contains('reel-video-in-sequence') ||
          classList.contains('shortsContainer')) {
        const parent = current.parentElement;
        if (parent) {
          console.log('Content Shield: Found video via class, using parent');
          return parent;
        }
      }
      
      // Reddit posts
      if (current.hasAttribute('data-testid') && 
          current.getAttribute('data-testid').includes('post')) {
        return current;
      }
      
      // Twitter/X posts
      if (current.hasAttribute('data-testid') && 
          current.getAttribute('data-testid') === 'tweet') {
        return current;
      }
      
      // Generic article or post containers
      if (tagName === 'ARTICLE' ||
          classList.contains('post') ||
          classList.contains('card') ||
          classList.contains('item')) {
        return current;
      }
      
      current = current.parentElement;
      depth++;
    }
    
    // If no container found, try to find the closest parent with a reasonable size
    current = element;
    for (let i = 0; i < 5; i++) {
      if (!current || !current.parentElement) break;
      current = current.parentElement;
      
      // Check if this element is large enough to be a container
      const rect = current.getBoundingClientRect();
      if (rect.height > 200 && rect.width > 200) {
        console.log('Content Shield: Using large parent container', rect.height, 'x', rect.width);
        return current;
      }
    }
    
    console.log('Content Shield: No suitable container found, using element itself');
    return element;
  }

  // Apply filter based on mode
  function applyFilter(element) {
    // If already filtered, skip
    if (filteredNodes.has(element) || element.hasAttribute('data-content-shield')) {
      return;
    }
    
    // Double-check: only filter if the element or its children actually match keywords
    if (!hasFilteredChild(element) && !shouldFilterElement(element)) {
      return;
    }
    
    // Mark as processed and filtered
    processedNodes.add(element);
    filteredNodes.add(element);
    
    console.log('Content Shield: Filtering element', element.tagName, element.className);
    
    switch (filterMode) {
      case 'blur':
        applyBlurFilter(element);
        break;
      case 'censor':
        applyCensorFilter(element);
        break;
      case 'remove':
        applyRemoveFilter(element);
        break;
      default:
        applyBlurFilter(element);
    }
  }

  // Check if element has a child that matches keywords
  function hasFilteredChild(element) {
    const selectors = [
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'a', 'p', 'span',
      '[id*="video-title"]',
      '[class*="title"]',
      '[class*="headline"]'
    ];
    
    const children = element.querySelectorAll(selectors.join(','));
    for (let child of children) {
      const text = getDirectTextContent(child);
      if (keywordPattern && keywordPattern.test(text)) {
        return true;
      }
    }
    return false;
  }

  // Remove filter from element
  function removeFilter(element) {
    element.style.filter = '';
    element.style.backgroundColor = '';
    element.style.color = '';
    element.style.cursor = '';
    element.title = '';
    console.log('Content Shield: Removed filter from element (no longer matches)');
  }

  // Blur mode implementation
  function applyBlurFilter(element) {
    // stronger blur for better obfuscation
    element.style.filter = 'blur(18px)';
    element.style.cursor = 'pointer';
    element.style.pointerEvents = 'auto';
    element.title = 'Click to reveal - Content Shield';
    element.setAttribute('data-content-shield', 'blurred');
    
    const revealBlur = function(e) {
      e.preventDefault();
      e.stopPropagation();
      this.style.filter = 'none';
      this.removeAttribute('data-content-shield');
      filteredNodes.delete(element);
      processedNodes.delete(element);
      this.removeEventListener('click', revealBlur, true);
    };
    
    element.addEventListener('click', revealBlur, true);
    
    console.log('Content Shield: Applied blur filter to element', element.tagName);
  }

  // Censor mode implementation (black bar)
  function applyCensorFilter(element) {
    element.style.backgroundColor = '#000';
    element.style.color = '#000';
    element.style.cursor = 'pointer';
    element.style.pointerEvents = 'auto';
    element.title = 'Click to reveal - Content Shield';
    element.setAttribute('data-content-shield', 'censored');
    
    const revealCensor = function(e) {
      e.preventDefault();
      e.stopPropagation();
      this.style.backgroundColor = 'transparent';
      this.style.color = 'inherit';
      this.removeAttribute('data-content-shield');
      filteredNodes.delete(element);
      processedNodes.delete(element);
      this.removeEventListener('click', revealCensor, true);
    };
    
    element.addEventListener('click', revealCensor, true);
    
    console.log('Content Shield: Applied censor filter to element', element.tagName);
  }

  // Remove mode implementation
  function applyRemoveFilter(element) {
    element.remove();
    console.log('Content Shield: Removed element from DOM');
  }

  // Set up MutationObserver for dynamic content
  function setupMutationObserver() {
    if (!document.body) return;
    
    // Disconnect existing observer if any
    if (observer) {
      observer.disconnect();
    }
    
    observer = new MutationObserver((mutations) => {
      const nodesToFilter = [];
      
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          // Only process element nodes
          if (node.nodeType === Node.ELEMENT_NODE) {
            // Check for specific selectors within the new node
            const selectors = [
              'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
              'a', 'p', 'span',
              '[id*="video-title"]',
              '[class*="title"]',
              '[class*="headline"]',
              '[class*="post"]',
              '[aria-label]'
            ];
            
            // Check the node itself first
            if (node.matches && node.matches(selectors.join(','))) {
              if (shouldFilterElement(node)) {
                const target = findFilterTarget(node);
                if (target && !nodesToFilter.includes(target)) {
                  nodesToFilter.push(target);
                }
              }
            }
            
            // Check descendants
            const elements = node.querySelectorAll ? node.querySelectorAll(selectors.join(',')) : [];
            elements.forEach(element => {
              if (shouldFilterElement(element)) {
                const target = findFilterTarget(element);
                if (target && !nodesToFilter.includes(target)) {
                  nodesToFilter.push(target);
                }
              }
            });
          }
        });
      });
      
      // Apply filters to found nodes
      nodesToFilter.forEach(node => applyFilter(node));
    });
    
    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
    
    console.log('Content Shield: MutationObserver initialized');
  }

  // Verify filtered elements still match keywords, remove filter if not
  function verifyAndRemoveNonMatchingFilters() {
    if (!keywordPattern) return;
    
    const filtered = document.querySelectorAll('[data-content-shield]');
    
    filtered.forEach(element => {
      // Check if this element or its children still match keywords
      const stillMatches = shouldFilterElement(element) || hasFilteredChild(element);
      
      if (!stillMatches) {
        console.log('Content Shield: Removing filter - content no longer matches keywords');
        removeFilter(element);
        filteredNodes.delete(element);
        processedNodes.delete(element);
      }
    });
  }

  // Clear all filters and refilter
  function refilter() {
    console.log('Content Shield: Refiltering content');
    
    // Clear all visual filters
    clearAllFilters();
    
    // Reload settings and refilter
    loadSettingsAndFilter();
  }

  // Listen for messages from popup/options
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'refilter') {
      console.log('Content Shield: Received refilter request');
      refilter();
      sendResponse({ success: true });
    }
  });

  // Start initialization
  init();
})();
