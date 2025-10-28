/**
 * Popup Script for YouTube RAG Assistant
 * Handles indexing videos and asking questions
 */

// API Configuration
const API_BASE = 'http://localhost:5000/api';

// DOM Elements
let currentVideoId = null;
const videoStatusEl = document.getElementById('video-status');
const indexBtn = document.getElementById('index-btn');
const askBtn = document.getElementById('ask-btn');
const questionInput = document.getElementById('question-input');
const loaderEl = document.getElementById('loader');
const loaderText = document.getElementById('loader-text');
const resultEl = document.getElementById('result');
const indexingProgressEl = document.getElementById('indexing-progress');
const progressBarEl = document.getElementById('progress-bar');
const progressTextEl = document.getElementById('progress-text');

// Initialize popup
document.addEventListener('DOMContentLoaded', async () => {
    await checkCurrentVideo();
    
    // Set up event listeners
    indexBtn.addEventListener('click', indexCurrentVideo);
    askBtn.addEventListener('click', askQuestion);
    
    // Allow Ctrl+Enter or Shift+Enter to submit question
    questionInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && (e.ctrlKey || e.shiftKey)) {
            e.preventDefault();
            askQuestion();
        }
    });
});

/**
 * Check if we're on a YouTube video page
 */
async function checkCurrentVideo() {
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        
        if (!tab) {
            videoStatusEl.textContent = 'No active tab found';
            return;
        }
        
        // Check if we're on YouTube
        if (!tab.url || (!tab.url.includes('youtube.com/watch'))) {
            videoStatusEl.textContent = 'Navigate to a YouTube video to index it';
            indexBtn.disabled = true;
            return;
        }
        
        // Get video ID from content script
        chrome.tabs.sendMessage(tab.id, { action: 'getVideoId' }, (response) => {
            if (chrome.runtime.lastError) {
                videoStatusEl.textContent = 'Please refresh the YouTube page';
                indexBtn.disabled = true;
                return;
            }
            
            if (response && response.videoId) {
                currentVideoId = response.videoId;
                videoStatusEl.innerHTML = `Video ID: <span class="video-id">${currentVideoId}</span>`;
                indexBtn.disabled = false;
            } else {
                videoStatusEl.textContent = 'Could not detect video ID';
                indexBtn.disabled = true;
            }
        });
        
    } catch (error) {
        console.error('Error checking video:', error);
        videoStatusEl.textContent = 'Error detecting video';
        indexBtn.disabled = true;
    }
}

/**
 * Show loading state
 */
function showLoading(message = 'Processing...') {
    loaderEl.style.display = 'block';
    loaderText.textContent = message;
    resultEl.style.display = 'none';
    indexBtn.disabled = true;
    askBtn.disabled = true;
}

/**
 * Hide loading state
 */
function hideLoading() {
    loaderEl.style.display = 'none';
    indexBtn.disabled = !currentVideoId;
    askBtn.disabled = false;
}

/**
 * Show result message
 */
function showResult(message, isError = false) {
    resultEl.className = isError ? 'error' : 'success';
    resultEl.innerHTML = message;
    resultEl.style.display = 'block';
}

/**
 * Index the current YouTube video
 */
async function indexCurrentVideo() {
    if (!currentVideoId) {
        showResult('No video detected', true);
        return;
    }
    
    showLoading('Starting indexing...');
    
    try {
        const response = await fetch(`${API_BASE}/index_youtube`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                video_id: currentVideoId
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            if (data.status === 'already_indexed') {
                // Video is already indexed, show success message immediately
                hideLoading();
                showResult(`
                    ✅ <strong>Video Already Indexed!</strong><br>
                    Video ID: ${data.video_id}<br>
                    <small>You can now ask questions about this video</small>
                `);
                return;
            }
            
            // Show progress bar
            indexingProgressEl.style.display = 'block';
            progressBarEl.style.width = '0%';
            progressTextEl.textContent = 'Starting indexing...';
            
            // Hide the main loader
            hideLoading();
            
            // Start polling for status updates
            pollIndexingStatus(data.video_id);
        } else {
            showResult(`❌ ${data.message}`, true);
            hideLoading();
        }
        
    } catch (error) {
        console.error('Indexing error:', error);
        showResult(`❌ Failed to connect to server. Make sure the Flask server is running on port 5000.`, true);
        hideLoading();
    }
}

/**
 * Poll indexing status until completion
 */
async function pollIndexingStatus(videoId) {
    const maxAttempts = 300; // 5 minutes max
    let attempts = 0;
    
    const poll = async () => {
        try {
            const response = await fetch(`${API_BASE}/indexing_status/${videoId}`);
            const status = await response.json();
            
            if (status.status === 'completed') {
                // Hide progress bar and show success
                indexingProgressEl.style.display = 'none';
                showResult(`
                    🎉 <strong>Indexing Completed!</strong><br>
                    Video ID: ${status.video_id}<br>
                    Chunks indexed: ${status.total_chunks}<br>
                    <small>You can now ask questions about this video</small>
                `);
                return;
            } else if (status.status === 'failed') {
                // Hide progress bar and show error
                indexingProgressEl.style.display = 'none';
                showResult(`❌ Indexing failed: ${status.error || status.message}`, true);
                return;
            } else if (status.status === 'started' || status.status === 'in_progress') {
                // Update progress bar
                const progress = status.progress || 0;
                const message = status.message || 'Processing...';
                
                progressBarEl.style.width = `${progress}%`;
                progressTextEl.textContent = `${message} (${progress}%)`;
                
                // Continue polling
                attempts++;
                if (attempts < maxAttempts) {
                    setTimeout(poll, 2000); // Poll every 2 seconds
  } else {
                    indexingProgressEl.style.display = 'none';
                    showResult('⏰ Indexing is taking longer than expected. Please check server logs.', true);
                }
            }
            
        } catch (error) {
            console.error('Status polling error:', error);
            attempts++;
            if (attempts < maxAttempts) {
                setTimeout(poll, 2000);
            } else {
                showResult('❌ Lost connection to server during indexing', true);
                hideLoading();
            }
        }
    };
    
    // Start polling
    poll();
}

/**
 * Ask a question about indexed videos
 */
async function askQuestion() {
    const question = questionInput.value.trim();
    
    if (!question) {
        showResult('Please enter a question', true);
      return;
    }

    showLoading('Searching and generating answer...');

    try {
        const response = await fetch(`${API_BASE}/ask_youtube`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
                question: question,
                video_id: currentVideoId,  // Optional: restrict to current video
                top_k: 3
        })
      });

        const data = await response.json();
        
        if (data.success) {
            // Format the answer with context links
            let resultHTML = `
                <div class="answer-section">
                    <div class="answer-label">Answer:</div>
                    <div class="answer-text">${escapeHtml(data.answer)}</div>
                </div>
            `;
            
            if (data.youtube_links && data.youtube_links.length > 0) {
                resultHTML += `
                    <div class="context-links">
                        <div class="answer-label">📺 Relevant video segments:</div>
                `;
                
                data.contexts.forEach((ctx, index) => {
                    const link = data.youtube_links[index];
                    const timestamp = formatTimestamp(ctx.timestamp);
                    resultHTML += `
                        <a href="${link}" target="_blank" class="context-link">
                            <span class="timestamp">${timestamp}</span> - Video ${ctx.video_id}
                        </a>
                    `;
                });
                
                resultHTML += '</div>';
            }
            
            showResult(resultHTML);
        } else {
            showResult(`❌ ${data.message}`, true);
      }

    } catch (error) {
        console.error('Question error:', error);
        showResult(`❌ Failed to connect to server. Make sure the Flask server is running on port 5000.`, true);
    } finally {
        hideLoading();
    }
}

/**
 * Format timestamp from seconds to MM:SS
 */
function formatTimestamp(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
        return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    } else {
        return `${minutes}:${String(secs).padStart(2, '0')}`;
    }
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Listen for video changes from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'videoChanged') {
        currentVideoId = request.videoId;
        videoStatusEl.innerHTML = `Video ID: <span class="video-id">${currentVideoId}</span>`;
        indexBtn.disabled = false;
  }
});
