/**
 * Content Script for YouTube RAG Assistant
 * Detects YouTube videos and extracts video ID
 */

// Extract video ID from current YouTube page
function getCurrentVideoId() {
    const url = new URL(window.location.href);
    
    // Check if we're on a watch page
    if (url.pathname === '/watch') {
        return url.searchParams.get('v');
    }
    
    return null;
}

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'getVideoId') {
        const videoId = getCurrentVideoId();
        sendResponse({ videoId: videoId });
    }
    return true;  // Keep message channel open for async response
});

// Optional: Notify popup when video changes
let lastVideoId = null;

function checkVideoChange() {
    const currentVideoId = getCurrentVideoId();
    
    if (currentVideoId && currentVideoId !== lastVideoId) {
        lastVideoId = currentVideoId;
        
        // Send message to popup (if it's open)
        chrome.runtime.sendMessage({
            action: 'videoChanged',
            videoId: currentVideoId
        }).catch(() => {
            // Popup might not be open, that's okay
        });
    }
}

// Check for video changes every 2 seconds
setInterval(checkVideoChange, 2000);

// Initial check
checkVideoChange();

console.log('YouTube RAG Assistant: Content script loaded');

