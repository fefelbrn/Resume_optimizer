// Main JavaScript for CV Optimizer Application

// State management
const state = {
    cvText: '',
    jobDescription: '',
    optimizedCv: '',
    coverLetter: '',
    apiKey: '',
    cvSkills: [],
    jobSkills: [],
    skillsMatched: false,
    assistantHistory: [],
    assistantSessionId: 'default',
    matchedSkillsData: null,
    lastExecutionLogs: null  // NEW: Store last execution logs
};

// DOM Elements
const elements = {
    apiKeyInput: document.getElementById('api-key'),
    languageSelect: document.getElementById('language'),
    modelSelect: document.getElementById('model'),
    temperatureInput: document.getElementById('temperature'),
    tempValue: document.getElementById('temp-value'),
    cvFileInput: document.getElementById('cv-file'),
    cvTextarea: document.getElementById('cv-text'),
    cvCount: document.getElementById('cv-count'),
    cvUploadStatus: document.getElementById('cv-upload-status'),
    jdFileInput: document.getElementById('jd-file'),
    jdTextarea: document.getElementById('job-description'),
    jdCount: document.getElementById('jd-count'),
    jdUploadStatus: document.getElementById('jd-upload-status'),
    minExperiences: document.getElementById('min-experiences'),
    maxExperiences: document.getElementById('max-experiences'),
    maxDateYears: document.getElementById('max-date-years'),
    letterWords: document.getElementById('letter-words'),
    optimizeBtn: document.getElementById('optimize-btn'),
    generateLetterBtn: document.getElementById('generate-letter-btn'),
    resultsSection: document.getElementById('results-section'),
    optimizedCvContent: document.getElementById('optimized-cv-content'),
    coverLetterContent: document.getElementById('cover-letter-content'),
    loadingOverlay: document.getElementById('loading-overlay'),
    loadingText: document.getElementById('loading-text'),
    tabs: document.querySelectorAll('.tab-btn'),
    tabContents: document.querySelectorAll('.tab-content'),
    errorModal: document.getElementById('error-modal'),
    errorMessage: document.getElementById('error-message'),
    errorModalClose: document.getElementById('error-modal-close'),
    mainTabs: document.querySelectorAll('.main-tab-btn'),
    mainTabContents: document.querySelectorAll('.main-tab-content'),
    historyList: document.getElementById('history-list'),
    filterBtns: document.querySelectorAll('.filter-btn'),
    clearHistoryBtn: document.getElementById('clear-history-btn'),
    skillsContainer: document.getElementById('skills-container'),
    skillsTags: document.getElementById('skills-tags'),
    skillsStats: document.getElementById('skills-stats'),
    skillsLoading: document.getElementById('skills-loading'),
    skillsEmpty: document.getElementById('skills-empty'),
    skillsTemperatureInput: document.getElementById('skills-temperature'),
    skillsTempValue: document.getElementById('skills-temp-value'),
    // Assistant elements (may be null if results section is hidden)
    assistantMessages: document.getElementById('assistant-messages'),
    assistantInput: document.getElementById('assistant-input'),
    assistantSendBtn: document.getElementById('assistant-send-btn'),
    clearAssistantBtn: document.getElementById('clear-assistant-btn'),
    // Quick navigation menu
    quickNavToggle: document.getElementById('quick-nav-toggle'),
    quickNavPopup: document.getElementById('quick-nav-popup'),
    quickNavItems: document.querySelectorAll('.quick-nav-item'),
    // Logs modal
    viewLogsBtn: document.getElementById('view-logs-btn'),
    logsModal: document.getElementById('logs-modal'),
    logsModalClose: document.getElementById('logs-modal-close'),
    simplifiedLogContent: document.getElementById('simplified-log-text'),
    fullLogContent: document.getElementById('full-log-text'),
    logsTabBtns: document.querySelectorAll('.logs-tab-btn')
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    try {
    setupEventListeners();
    updateWordCounts();
    loadHistory();
    setupMainTabs();
        // Assistant listeners will be set up when results section is shown
        // setupAssistantListeners(); // Commented out - will be called when needed
        loadAssistantHistory();
        setupQuickNavigation();
        console.log('Application initialized successfully');
    } catch (error) {
        console.error('Error during initialization:', error);
        showError('Error during application initialization: ' + error.message);
    }
});

// Event Listeners Setup
function setupEventListeners() {
    try {
    // Temperature slider
        if (elements.temperatureInput && elements.tempValue) {
    elements.temperatureInput.addEventListener('input', (e) => {
        // Format to 2 decimal places
        const value = parseFloat(e.target.value);
        elements.tempValue.textContent = value.toFixed(2);
    });
        }
    
    // Skills temperature slider
    if (elements.skillsTemperatureInput && elements.skillsTempValue) {
        elements.skillsTemperatureInput.addEventListener('input', (e) => {
            const value = parseFloat(e.target.value);
            elements.skillsTempValue.textContent = value.toFixed(2);
        });
    }

    // File uploads
        if (elements.cvFileInput) {
            console.log('CV file input found, attaching listener');
    elements.cvFileInput.addEventListener('change', (e) => handleFileUpload(e, 'cv'));
        } else {
            console.error('CV file input NOT FOUND!');
        }
        if (elements.jdFileInput) {
            console.log('JD file input found, attaching listener');
    elements.jdFileInput.addEventListener('change', (e) => handleFileUpload(e, 'jd'));
        } else {
            console.error('JD file input NOT FOUND!');
        }
    } catch (error) {
        console.error('Error in setupEventListeners:', error);
    }

    // Paste buttons - show textarea only, let user paste manually
    document.getElementById('paste-cv-btn').addEventListener('click', () => {
        // Show textarea
        elements.cvTextarea.classList.remove('hidden');
        elements.cvCount.classList.remove('hidden');
        
        // Clear textarea first - start fresh
        elements.cvTextarea.value = '';
        
        // Focus textarea so user can paste with Ctrl+V
        elements.cvTextarea.focus();
        
        // Hide upload status when showing textarea
        if (elements.cvUploadStatus) {
        elements.cvUploadStatus.classList.add('hidden');
        }
        
        // User will paste manually with Ctrl+V
    });

    document.getElementById('paste-jd-btn').addEventListener('click', () => {
        // Show textarea
        elements.jdTextarea.classList.remove('hidden');
        elements.jdCount.classList.remove('hidden');
        
        // Clear textarea first - start fresh
        elements.jdTextarea.value = '';
        
        // Focus textarea so user can paste with Ctrl+V
        elements.jdTextarea.focus();
        
        // Hide upload status when showing textarea
        if (elements.jdUploadStatus) {
        elements.jdUploadStatus.classList.add('hidden');
        }
        
        // User will paste manually with Ctrl+V
    });

    // Text area changes - auto-resize and word count
    // CV textarea - ONLY updates state.cvText
    elements.cvTextarea.addEventListener('input', (e) => {
        // Only update if textarea is visible (user is actively editing)
        if (!elements.cvTextarea.classList.contains('hidden')) {
        autoResizeTextarea(elements.cvTextarea);
            // Update ONLY CV state, never touch job description
            state.cvText = e.target.value;
        updateWordCounts();
        // Reset CV skills when text changes manually
        state.cvSkills = [];
        // Debounce extraction to avoid too many API calls
        clearTimeout(extractSkillsTimeout);
        extractSkillsTimeout = setTimeout(() => {
            if (state.cvText.trim()) {
                extractSkillsFromText(state.cvText, 'cv');
            }
        }, 2000); // Wait 2 seconds after user stops typing
        }
    });
    
    // Job description textarea - ONLY updates state.jobDescription
    elements.jdTextarea.addEventListener('input', (e) => {
        // Only update if textarea is visible (user is actively editing)
        if (!elements.jdTextarea.classList.contains('hidden')) {
        autoResizeTextarea(elements.jdTextarea);
            // Update ONLY job description state, never touch CV
            state.jobDescription = e.target.value;
        updateWordCounts();
        // Reset job skills when text changes manually
        state.jobSkills = [];
        // Debounce extraction to avoid too many API calls
        clearTimeout(extractSkillsTimeout);
        extractSkillsTimeout = setTimeout(() => {
            if (state.jobDescription.trim()) {
                extractSkillsFromText(state.jobDescription, 'job');
            }
        }, 2000); // Wait 2 seconds after user stops typing
        }
    });
    
    // Auto-resize on paste and update state
    elements.cvTextarea.addEventListener('paste', () => {
        setTimeout(() => {
            autoResizeTextarea(elements.cvTextarea);
            // Update state when user pastes
            state.cvText = elements.cvTextarea.value;
            updateWordCounts();
            // Extract skills
            if (state.cvText.trim()) {
                extractSkillsFromText(state.cvText, 'cv');
            }
        }, 10);
    });
    
    elements.jdTextarea.addEventListener('paste', () => {
        setTimeout(() => {
            autoResizeTextarea(elements.jdTextarea);
            // Update state when user pastes
            state.jobDescription = elements.jdTextarea.value;
            updateWordCounts();
            // Extract skills
            if (state.jobDescription.trim()) {
                extractSkillsFromText(state.jobDescription, 'job');
            }
        }, 10);
    });

    // Action buttons
    elements.optimizeBtn.addEventListener('click', optimizeCv);
    elements.generateLetterBtn.addEventListener('click', generateLetter);

    // Tab switching
    elements.tabs.forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });

    // Copy buttons
    document.querySelectorAll('.btn-copy').forEach(btn => {
        btn.addEventListener('click', (e) => copyToClipboard(e.target.dataset.copy));
    });

    // Download buttons
    document.querySelectorAll('.btn-download').forEach(btn => {
        btn.addEventListener('click', (e) => downloadContent(e.target.dataset.download));
    });

    // Error modal close button
    elements.errorModalClose.addEventListener('click', () => {
        elements.errorModal.classList.add('hidden');
    });

    // Close error modal when clicking outside
    elements.errorModal.addEventListener('click', (e) => {
        if (e.target === elements.errorModal) {
            elements.errorModal.classList.add('hidden');
        }
    });

    // Close error modal with Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !elements.errorModal.classList.contains('hidden')) {
            elements.errorModal.classList.add('hidden');
        }
    });
    
    // Logs modal
    if (elements.viewLogsBtn) {
        elements.viewLogsBtn.addEventListener('click', showLogsModal);
    }
    if (elements.logsModalClose) {
        elements.logsModalClose.addEventListener('click', () => {
            elements.logsModal.classList.add('hidden');
        });
    }
    if (elements.logsModal) {
        elements.logsModal.addEventListener('click', (e) => {
            if (e.target === elements.logsModal) {
                elements.logsModal.classList.add('hidden');
            }
        });
    }
    
    // Logs tabs
    if (elements.logsTabBtns) {
        elements.logsTabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const tabName = btn.dataset.logTab;
                switchLogsTab(tabName);
            });
        });
    }

    // History filters
    elements.filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            if (btn.id === 'clear-history-btn') {
                clearHistory();
                return;
            }
            elements.filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const filter = btn.dataset.filter;
            filterHistory(filter);
        });
    });

    // API key input - trigger skills extraction when API key is entered
    elements.apiKeyInput.addEventListener('input', () => {
        // If we have text but no skills extracted yet, try to extract
        if (state.cvText && state.cvSkills.length === 0) {
            extractSkillsFromText(state.cvText, 'cv');
        }
        if (state.jobDescription && state.jobSkills.length === 0) {
            extractSkillsFromText(state.jobDescription, 'job');
        }
        // If both are ready, match them
        if (state.cvText && state.jobDescription && state.cvSkills.length > 0 && state.jobSkills.length > 0) {
            matchSkills();
        }
    });
}

// Main tabs setup
function setupMainTabs() {
    elements.mainTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetTab = tab.dataset.mainTab;
            
            // Update tab buttons
            elements.mainTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            // Update tab contents
            elements.mainTabContents.forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(`${targetTab}-content`).classList.add('active');
            
            // Reload history when switching to history tab
            if (targetTab === 'history') {
                loadHistory();
            }
        });
    });
}

// History Management
const HISTORY_STORAGE_KEY = 'cvOptimizerHistory';

function saveToHistory(type, content, metadata = {}) {
    const history = getHistory();
    const historyItem = {
        id: Date.now(),
        type: type, // 'cv' or 'letter'
        content: content,
        timestamp: new Date().toISOString(),
        metadata: {
            language: metadata.language || 'fr',
            model: metadata.model || 'gpt-4o-mini',
            temperature: metadata.temperature || 0.3,
            ...metadata
        }
    };
    
    history.unshift(historyItem); // Add to beginning
    // Keep only last 50 items
    if (history.length > 50) {
        history.splice(50);
    }
    
    localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(history));
    loadHistory();
}

function getHistory() {
    try {
        const stored = localStorage.getItem(HISTORY_STORAGE_KEY);
        return stored ? JSON.parse(stored) : [];
    } catch (e) {
        return [];
    }
}

function loadHistory(filter = null) {
    // Get active filter if not provided
    if (filter === null) {
        const activeFilter = document.querySelector('.filter-btn.active');
        filter = activeFilter ? activeFilter.dataset.filter : 'all';
    }
    
    const history = getHistory();
    
    if (history.length === 0) {
        elements.historyList.innerHTML = `
            <div class="history-empty">
                <p>📭 No history yet</p>
                <p class="history-empty-subtitle">Your generations will appear here after using the Generation section</p>
            </div>
        `;
        return;
    }
    
    const filtered = filter === 'all' 
        ? history 
        : history.filter(item => item.type === filter);
    
    if (filtered.length === 0) {
        elements.historyList.innerHTML = `
            <div class="history-empty">
                <p>📭 No items in this category</p>
            </div>
        `;
        return;
    }
    
    elements.historyList.innerHTML = filtered.map(item => {
        const date = new Date(item.timestamp);
        const dateStr = date.toLocaleDateString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        const typeLabel = item.type === 'cv' ? 'Optimized CV' : 'Cover Letter';
        const typeClass = item.type === 'cv' ? 'cv' : 'letter';
        const preview = item.content.substring(0, 200) + (item.content.length > 200 ? '...' : '');
        
        return `
            <div class="history-item" data-id="${item.id}">
                <div class="history-item-header">
                    <div class="history-item-title">
                        <span class="history-item-type ${typeClass}">${typeLabel}</span>
                    </div>
                    <div class="history-item-date">${dateStr}</div>
                </div>
                <div class="history-item-meta">
                    <span>🌐 ${item.metadata.language?.toUpperCase() || 'FR'}</span>
                    <span>🤖 ${item.metadata.model || 'gpt-4o-mini'}</span>
                    <span>🌡️ ${item.metadata.temperature || 0.3}</span>
                    ${item.metadata.target_words ? `<span>📝 ${item.metadata.target_words} words</span>` : ''}
                </div>
                <div class="history-item-content">${escapeHtml(preview)}</div>
                <div class="history-item-actions">
                    <button class="history-btn" onclick="loadHistoryItem(${item.id})">
                        🔄 Reload
                    </button>
                    <button class="history-btn secondary" onclick="copyHistoryItem(${item.id})">
                        📋 Copy
                    </button>
                    <button class="history-btn secondary" onclick="downloadHistoryItem(${item.id})">
                        💾 Download
                    </button>
                    <button class="history-btn" onclick="deleteHistoryItem(${item.id})" style="background: var(--error-color); color: white; border-color: var(--error-color);">
                        🗑️ Delete
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

function filterHistory(filter) {
    loadHistory(filter);
}

function clearHistory() {
    if (confirm('Are you sure you want to clear all history?')) {
        localStorage.removeItem(HISTORY_STORAGE_KEY);
        loadHistory();
    }
}

function loadHistoryItem(id) {
    const history = getHistory();
    const item = history.find(h => h.id === id);
    if (!item) return;
    
    // Switch to generation tab
    document.querySelector('[data-main-tab="generation"]').click();
    
    // Load content based on type
    if (item.type === 'cv') {
        state.optimizedCv = item.content;
        elements.optimizedCvContent.textContent = item.content;
        elements.resultsSection.classList.remove('hidden');
        switchTab('optimized-cv');
    } else {
        state.coverLetter = item.content;
        elements.coverLetterContent.textContent = item.content;
        elements.resultsSection.classList.remove('hidden');
        switchTab('cover-letter');
    }
    
    // Restore metadata if available
    if (item.metadata.language) {
        elements.languageSelect.value = item.metadata.language;
    }
    if (item.metadata.model) {
        elements.modelSelect.value = item.metadata.model;
    }
    if (item.metadata.temperature !== undefined) {
        elements.temperatureInput.value = item.metadata.temperature;
        elements.tempValue.textContent = parseFloat(item.metadata.temperature).toFixed(2);
    }
}

function copyHistoryItem(id) {
    const history = getHistory();
    const item = history.find(h => h.id === id);
    if (!item) return;
    
    navigator.clipboard.writeText(item.content).then(() => {
        showError('✓ Content copied to clipboard!');
        setTimeout(() => {
            elements.errorModal.classList.add('hidden');
        }, 2000);
    }).catch(() => {
        showError('Error during copy');
    });
}

function downloadHistoryItem(id) {
    const history = getHistory();
    const item = history.find(h => h.id === id);
    if (!item) return;
    
    const filename = item.type === 'cv' ? 'optimized_cv.txt' : 'cover_letter.txt';
    const blob = new Blob([item.content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function deleteHistoryItem(id) {
    if (!confirm('Delete this item from history?')) return;
    
    const history = getHistory();
    const filtered = history.filter(h => h.id !== id);
    localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(filtered));
    loadHistory();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Make history functions globally accessible for onclick handlers
window.loadHistoryItem = loadHistoryItem;
window.copyHistoryItem = copyHistoryItem;
window.downloadHistoryItem = downloadHistoryItem;
window.deleteHistoryItem = deleteHistoryItem;

// Update word counts
function updateWordCounts() {
    // Only update counts for visible textareas using their actual content
    if (elements.cvCount && elements.cvTextarea && !elements.cvTextarea.classList.contains('hidden')) {
    const cvWords = elements.cvTextarea.value.trim().split(/\s+/).filter(w => w.length > 0).length;
        elements.cvCount.textContent = `${cvWords} words`;
    }
    if (elements.jdCount && elements.jdTextarea && !elements.jdTextarea.classList.contains('hidden')) {
    const jdWords = elements.jdTextarea.value.trim().split(/\s+/).filter(w => w.length > 0).length;
        elements.jdCount.textContent = `${jdWords} words`;
    }
}

// Handle file upload
async function handleFileUpload(event, type) {
    try {
    const file = event.target.files[0];
        if (!file) {
            console.log('No file selected');
            return;
        }

        console.log(`Uploading ${type} file:`, file.name);
        showLoading('Extracting text...');

    const formData = new FormData();
    formData.append('file', file);

        const response = await fetch('/api/parse-pdf', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.error) {
            showError(data.error);
            return;
        }

        if (!data.text || !data.text.trim()) {
            showError('The file is empty or could not be extracted');
            return;
        }

        console.log(`File uploaded successfully, ${data.word_count} words extracted`);

        if (type === 'cv') {
            // Store text in state ONLY - do NOT touch textarea
            state.cvText = data.text;
            console.log('CV text stored, length:', state.cvText.length);
            // Show success status indicator
            if (elements.cvUploadStatus) {
            elements.cvUploadStatus.classList.remove('hidden');
            }
            // Keep textarea hidden and empty - user can paste manually if needed
            if (elements.cvTextarea && elements.cvTextarea.classList.contains('hidden')) {
                // Don't touch it - it stays hidden
            }
            // Extract skills automatically
            extractSkillsFromText(data.text, 'cv');
        } else {
            // Store text in state ONLY - do NOT touch textarea
            state.jobDescription = data.text;
            console.log('Job description stored, length:', state.jobDescription.length);
            // Show success status indicator
            if (elements.jdUploadStatus) {
            elements.jdUploadStatus.classList.remove('hidden');
            }
            // Keep textarea hidden and empty - user can paste manually if needed
            if (elements.jdTextarea && elements.jdTextarea.classList.contains('hidden')) {
                // Don't touch it - it stays hidden
            }
            // Extract skills automatically
            extractSkillsFromText(data.text, 'job');
        }
        
        // If both CV and job description are loaded, match skills
        if (state.cvText && state.jobDescription && state.cvSkills.length > 0 && state.jobSkills.length > 0) {
            matchSkills();
        }
    } catch (error) {
        console.error('Error in handleFileUpload:', error);
        showError(`Upload error: ${error.message}`);
    } finally {
        hideLoading();
    }
}

// Optimize CV
async function optimizeCv() {
    // Validation
    if (!validateInputs()) return;

    showLoading('Optimizing CV...');

    const payload = {
        cv_text: state.cvText,
        job_description: state.jobDescription,
        api_key: elements.apiKeyInput.value,
        language: elements.languageSelect.value,
        model: elements.modelSelect.value,
        temperature: parseFloat(elements.temperatureInput.value),
        min_experiences: parseInt(elements.minExperiences.value),
        max_experiences: parseInt(elements.maxExperiences.value),
        max_date_years: elements.maxDateYears.value || null,
        session_id: state.assistantSessionId || 'default'  // NEW: Add session_id for RAG
    };

    try {
        const response = await fetch('/api/optimize-cv', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (data.error) {
            showError(data.error);
            return;
        }

        state.optimizedCv = data.optimized_cv;
        elements.optimizedCvContent.textContent = data.optimized_cv;
        elements.resultsSection.classList.remove('hidden');
        switchTab('optimized-cv');
        
        // Display RAG sources if available
        displayRAGSources(data.sources);
        
        // Store logs for the logs modal
        state.lastExecutionLogs = {
            agent_logs: data.agent_logs || [],
            rag_details: data.rag_details || null,
            model_used: data.model_used || elements.modelSelect?.value || 'N/A',
            temperature: parseFloat(elements.temperatureInput?.value) || 0.3,
            word_count: data.word_count || 0,
            cv_skills: data.cv_skills || [],
            job_skills: data.job_skills || [],
            skills_comparison: data.skills_comparison || null
        };
        
        // Show logs button and enable it
        if (elements.viewLogsBtn) {
            elements.viewLogsBtn.disabled = false;
            elements.viewLogsBtn.style.opacity = '1';
            elements.viewLogsBtn.style.cursor = 'pointer';
        } else {
            // Try to re-fetch it
            elements.viewLogsBtn = document.getElementById('view-logs-btn');
            if (elements.viewLogsBtn) {
                elements.viewLogsBtn.disabled = false;
                elements.viewLogsBtn.style.opacity = '1';
                elements.viewLogsBtn.style.cursor = 'pointer';
            }
        }
        
        // Re-initialize assistant elements now that results section is visible
        if (!elements.assistantSendBtn) {
            elements.assistantMessages = document.getElementById('assistant-messages');
            elements.assistantInput = document.getElementById('assistant-input');
            elements.assistantSendBtn = document.getElementById('assistant-send-btn');
            elements.clearAssistantBtn = document.getElementById('clear-assistant-btn');
            setupAssistantListeners();
            // Initialize textarea height
            if (elements.assistantInput) {
                autoResizeTextarea(elements.assistantInput);
            }
        }
        
        // Enable assistant button
        updateAssistantSendButton();
        
        // Save to history
        saveToHistory('cv', data.optimized_cv, {
            language: payload.language,
            model: payload.model,
            temperature: payload.temperature,
            min_experiences: payload.min_experiences,
            max_experiences: payload.max_experiences,
            max_date_years: payload.max_date_years
        });
    } catch (error) {
        showError(`Error: ${error.message}`);
    } finally {
        hideLoading();
    }
}

// Generate cover letter
async function generateLetter() {
    // Validation
    if (!validateInputs()) return;

    if (!state.optimizedCv && !state.cvText) {
        showError('Please first optimize your CV or have a CV in the field.');
        return;
    }

    showLoading('Generating cover letter...');

    const payload = {
        cv_text: state.cvText,
        optimized_cv: state.optimizedCv || state.cvText,
        job_description: state.jobDescription,
        api_key: elements.apiKeyInput.value,
        language: elements.languageSelect.value,
        model: elements.modelSelect.value,
        temperature: parseFloat(elements.temperatureInput.value),
        target_words: parseInt(elements.letterWords.value)
    };

    try {
        const response = await fetch('/api/generate-letter', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (data.error) {
            showError(data.error);
            return;
        }

        state.coverLetter = data.cover_letter;
        elements.coverLetterContent.textContent = data.cover_letter;
        elements.resultsSection.classList.remove('hidden');
        switchTab('cover-letter');
        
        // Save to history
        saveToHistory('letter', data.cover_letter, {
            language: payload.language,
            model: payload.model,
            temperature: payload.temperature,
            target_words: payload.target_words
        });
    } catch (error) {
        showError(`Error: ${error.message}`);
    } finally {
        hideLoading();
    }
}

// Validate inputs
function validateInputs() {
    if (!elements.apiKeyInput.value.trim()) {
        showError('Please enter your OpenAI API key');
        elements.apiKeyInput.focus();
        return false;
    }

    if (!state.cvText.trim()) {
        showError('Please enter or upload your CV');
        elements.cvTextarea.focus();
        return false;
    }

    if (!state.jobDescription.trim()) {
        showError('Please enter or upload the job description');
        elements.jdTextarea.focus();
        return false;
    }

    return true;
}

// Switch tabs
function switchTab(tabName) {
    console.log('Switching to tab:', tabName);
    
    // Re-fetch elements to ensure they're available
    const tabs = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    // Update tab buttons
    tabs.forEach(tab => {
        if (tab.dataset.tab === tabName) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });

    // Update tab contents
    tabContents.forEach(content => {
        if (content.id === `${tabName}-tab`) {
            content.classList.add('active');
        } else {
            content.classList.remove('active');
        }
    });
    
    // If switching to assistant tab, initialize assistant elements if needed
    if (tabName === 'assistant') {
        // Always re-initialize elements when switching to assistant tab
        elements.assistantMessages = document.getElementById('assistant-messages');
        elements.assistantInput = document.getElementById('assistant-input');
        elements.assistantSendBtn = document.getElementById('assistant-send-btn');
        elements.clearAssistantBtn = document.getElementById('clear-assistant-btn');
        
        if (elements.assistantSendBtn && elements.assistantInput && elements.clearAssistantBtn) {
            // Only setup listeners if not already set up
            if (!elements.assistantSendBtn.hasAttribute('data-listeners-setup')) {
                setupAssistantListeners();
                elements.assistantSendBtn.setAttribute('data-listeners-setup', 'true');
            }
        }
        
        // Update button state after a short delay to ensure elements are ready
        setTimeout(() => {
            updateAssistantSendButton();
        }, 100);
    }
    
    console.log('Tab switched to:', tabName);
}

// Copy to clipboard
async function copyToClipboard(type) {
    let text = '';
    if (type === 'optimized-cv') {
        text = state.optimizedCv;
    } else if (type === 'cover-letter') {
        text = state.coverLetter;
    }

    if (!text) {
        showError('No content to copy');
        return;
    }

    try {
        await navigator.clipboard.writeText(text);
        // Show a brief success message (using a simple alert for positive feedback)
        const originalText = elements.errorModalClose.textContent;
        elements.errorModalClose.textContent = '✓ Copied!';
        setTimeout(() => {
            elements.errorModalClose.textContent = originalText;
        }, 2000);
    } catch (error) {
        showError(`Copy error: ${error.message}`);
    }
}

// Download content
async function downloadContent(type) {
    if (type === 'optimized-cv') {
        if (!state.optimizedCv) {
            showError('No optimized CV to download');
            return;
        }
        
        // Generate PDF instead of TXT
        try {
            const response = await fetch('/api/generate-pdf', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    cv_text: state.optimizedCv
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Error generating PDF');
            }
            
            // Download PDF
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'optimized_cv.pdf';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Error generating PDF:', error);
            showError('Error generating PDF: ' + error.message);
            // Fallback to TXT if PDF generation fails
            const blob = new Blob([state.optimizedCv], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'optimized_cv.txt';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
    } else if (type === 'cover-letter') {
        const text = state.coverLetter;
        if (!text) {
            showError('No cover letter to download');
            return;
        }
        
        const blob = new Blob([text], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'cover_letter.txt';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
}

// Auto-resize textarea
function autoResizeTextarea(textarea) {
    if (!textarea) return;
    
    // Reset height to get accurate scrollHeight
    textarea.style.height = 'auto';
    
    // Different min/max heights for assistant textarea vs regular textareas
    const isAssistant = textarea.id === 'assistant-input';
    const minHeight = isAssistant ? 60 : 150;
    const maxHeight = isAssistant ? 300 : 800;
    
    const newHeight = Math.min(Math.max(textarea.scrollHeight, minHeight), maxHeight);
    
    textarea.style.height = newHeight + 'px';
    
    // Show scrollbar if content exceeds max height
    if (textarea.scrollHeight > maxHeight) {
        textarea.style.overflowY = 'auto';
    } else {
        textarea.style.overflowY = 'hidden';
    }
}

// Loading overlay
function showLoading(message = 'Processing...') {
    elements.loadingText.textContent = message;
    elements.loadingOverlay.classList.remove('hidden');
}

function hideLoading() {
    elements.loadingOverlay.classList.add('hidden');
}

// Error modal
function showError(message) {
    elements.errorMessage.textContent = message;
    elements.errorModal.classList.remove('hidden');
    // Focus on close button for accessibility
    elements.errorModalClose.focus();
}

function hideError() {
    elements.errorModal.classList.add('hidden');
}

// Skills Extraction and Matching
let extractSkillsTimeout = null;

async function extractSkillsFromText(text, textType) {
    if (!text || !text.trim()) return;
    if (!elements.apiKeyInput.value.trim()) {
        // Hide skills section if no API key
        elements.skillsContainer.classList.add('hidden');
        elements.skillsLoading.classList.add('hidden');
        elements.skillsEmpty.classList.remove('hidden');
        return;
    }
    
    // Show loading
    elements.skillsLoading.classList.remove('hidden');
    elements.skillsContainer.classList.add('hidden');
    elements.skillsEmpty.classList.add('hidden');
    
    try {
        const response = await fetch('/api/extract-skills', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text,
                text_type: textType,
                api_key: elements.apiKeyInput.value,
                model: elements.modelSelect.value,
                temperature: parseFloat(elements.skillsTemperatureInput ? elements.skillsTemperatureInput.value : 0.2)
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            console.error('Error extracting skills:', data.error);
            elements.skillsLoading.classList.add('hidden');
            return;
        }
        
        // Store skills
        if (textType === 'cv') {
            state.cvSkills = data.skills || [];
        } else {
            state.jobSkills = data.skills || [];
        }
        
        // If both are ready, match them
        if (state.cvSkills.length > 0 && state.jobSkills.length > 0) {
            matchSkills();
        }
    } catch (error) {
        console.error('Error extracting skills:', error);
        elements.skillsLoading.classList.add('hidden');
    }
}

async function matchSkills() {
    if (state.cvSkills.length === 0 || state.jobSkills.length === 0) {
        return;
    }
    
    elements.skillsLoading.classList.remove('hidden');
    elements.skillsContainer.classList.add('hidden');
    elements.skillsEmpty.classList.add('hidden');
    
    try {
        const response = await fetch('/api/match-skills', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                cv_skills: state.cvSkills,
                job_skills: state.jobSkills,
                cv_text: state.cvText,
                job_text: state.jobDescription,
                api_key: elements.apiKeyInput.value,
                model: elements.modelSelect.value,
                temperature: parseFloat(elements.skillsTemperatureInput ? elements.skillsTemperatureInput.value : 0.3)
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            console.error('Error matching skills:', data.error);
            elements.skillsLoading.classList.add('hidden');
            return;
        }
        
        // Display matched skills
        displaySkills(data);
        state.skillsMatched = true;
        state.matchedSkillsData = data; // Store for assistant context
    } catch (error) {
        console.error('Error matching skills:', error);
        elements.skillsLoading.classList.add('hidden');
    }
}

function displaySkills(matchData) {
    elements.skillsLoading.classList.add('hidden');
    elements.skillsEmpty.classList.add('hidden');
    elements.skillsContainer.classList.remove('hidden');
    
    // Display stats
    const stats = matchData.stats || {};
    elements.skillsStats.innerHTML = `
        <div class="stat-item">
            <div class="stat-label">Match</div>
            <div class="stat-value" style="color: var(--success-color);">${stats.match_percentage || 0}%</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">CV Skills</div>
            <div class="stat-value">${stats.total_cv || 0}</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">Job Skills</div>
            <div class="stat-value">${stats.total_job || 0}</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">Matches</div>
            <div class="stat-value" style="color: var(--success-color);">${stats.matched_count || 0}</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">Missing</div>
            <div class="stat-value" style="color: var(--error-color);">${stats.missing_count || 0}</div>
        </div>
    `;
    
    // Display skills tags in order: Gray, Red, Green, Blue
    let tagsHTML = '';
    
    // Gray: CV only (not interesting, not in job)
    if (matchData.cv_only && matchData.cv_only.length > 0) {
        matchData.cv_only.forEach(skill => {
            tagsHTML += `<span class="skill-tag gray">${escapeHtml(skill)}</span>`;
        });
    }
    
    // Red: Job only (missing from CV)
    if (matchData.job_only && matchData.job_only.length > 0) {
        matchData.job_only.forEach(skill => {
            tagsHTML += `<span class="skill-tag red">${escapeHtml(skill)}</span>`;
        });
    }
    
    // Green: Matched (in both CV and job)
    if (matchData.matched && matchData.matched.length > 0) {
        matchData.matched.forEach(skill => {
            tagsHTML += `<span class="skill-tag green">${escapeHtml(skill)}</span>`;
        });
    }
    
    // Blue: Interesting (CV skills valuable for job but not in job description)
    if (matchData.interesting && matchData.interesting.length > 0) {
        matchData.interesting.forEach(skill => {
            tagsHTML += `<span class="skill-tag blue">${escapeHtml(skill)}</span>`;
        });
    }
    
    elements.skillsTags.innerHTML = tagsHTML || '<p style="color: var(--text-secondary);">No skills to display</p>';
}

// ==================== ASSISTANT FUNCTIONALITY ====================

// Setup assistant event listeners
function setupAssistantListeners() {
    // Check if assistant elements exist (they're in the results section which may be hidden)
    if (!elements.assistantSendBtn || !elements.assistantInput || !elements.clearAssistantBtn) {
        return; // Elements not available yet, will be set up when results section is shown
    }
    
    // Send button
    elements.assistantSendBtn.addEventListener('click', sendAssistantRequest);
    
    // Enter key to send (Shift+Enter for new line)
    elements.assistantInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (elements.assistantSendBtn && !elements.assistantSendBtn.disabled) {
                sendAssistantRequest();
            }
        }
    });
    
    // Enable/disable send button based on input and CV
    // Auto-resize textarea as user types
    elements.assistantInput.addEventListener('input', () => {
        autoResizeTextarea(elements.assistantInput);
        updateAssistantSendButton();
    });
    
    // Auto-resize on paste
    elements.assistantInput.addEventListener('paste', () => {
        setTimeout(() => autoResizeTextarea(elements.assistantInput), 10);
    });
    
    // Clear assistant
    elements.clearAssistantBtn.addEventListener('click', clearAssistantHistory);
}

// Send assistant request
async function sendAssistantRequest() {
    if (!elements.assistantInput) {
        showError('Éléments assistant non disponibles');
        return;
    }
    
    const request = elements.assistantInput.value.trim();
    
    if (!request) return;
    
    // Use optimized CV if available, otherwise use original CV
    const cvToUse = state.optimizedCv || state.cvText;
    if (!cvToUse || !cvToUse.trim()) {
        showError('Please first load your CV');
        return;
    }
    if (!elements.apiKeyInput.value.trim()) {
        showError('Please enter your OpenAI API key');
        return;
    }
    
    // Add user message to UI
    addAssistantMessage('user', request);
    
    // Clear input
    elements.assistantInput.value = '';
    updateAssistantSendButton();
    
    // Show loading
    const loadingId = addAssistantMessage('assistant', '...', true);
    
    try {
        const response = await fetch('/api/assistant', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                request: request,
                session_id: state.assistantSessionId,
                api_key: elements.apiKeyInput.value,
                model: elements.modelSelect.value,
                temperature: parseFloat(elements.temperatureInput.value),
                language: elements.languageSelect.value,
                original_cv: state.cvText,
                optimized_cv: state.optimizedCv || state.cvText, // Use original if no optimized
                job_description: state.jobDescription,
                cv_skills: state.cvSkills,
                job_skills: state.jobSkills,
                matched_skills: state.matchedSkillsData || {}
            })
        });
        
        const data = await response.json();
        
        // Remove loading message
        removeAssistantMessage(loadingId);
        
        if (data.error) {
            // Format error message with line breaks
            let errorMsg = data.error;
            // Replace \n with <br> for HTML display
            errorMsg = errorMsg.replace(/\n/g, '<br>');
            showError(data.error);
            // Add error message with HTML support
            addAssistantMessageHTML('assistant', `❌ ${errorMsg}`, false);
            return;
        }
        
        // Process the response
        if (data.success) {
            let responseText = data.explanation || 'Modification completed';
            
            // Update CV if needed
            if (data.action === 'update_cv' || data.action === 'update_both') {
                state.optimizedCv = data.updated_cv;
                elements.optimizedCvContent.textContent = data.updated_cv;
                responseText += '\n\n✅ Optimized CV updated';
            }
            
            // Update skills if needed
            if (data.action === 'update_skills' || data.action === 'update_both') {
                const updatedSkills = data.updated_skills || {};
                if (updatedSkills.cv_skills) {
                    state.cvSkills = updatedSkills.cv_skills;
                }
                if (updatedSkills.job_skills) {
                    state.jobSkills = updatedSkills.job_skills;
                }
                // Re-match skills if both are updated
                if (state.cvSkills.length > 0 && state.jobSkills.length > 0) {
                    matchSkills();
                }
                responseText += '\n\n✅ Skills updated';
            }
            
            // Add assistant response
            addAssistantMessage('assistant', responseText, false);
            
            // Display RAG sources if available
            if (data.sources && data.sources.length > 0) {
                displayRAGSourcesInAssistant(data.sources);
            }
            
            // Save to history
            state.assistantHistory.push({
                request: request,
                response: data
            });
            saveAssistantHistory();
        } else {
            addAssistantMessage('assistant', `Error: ${data.error || 'Modification failed'}`, false);
        }
        
    } catch (error) {
        removeAssistantMessage(loadingId);
        showError(`Send error: ${error.message}`);
        addAssistantMessage('assistant', `Error: ${error.message}`, false);
    }
}

// Add assistant message to UI
function addAssistantMessage(role, content, isLoading = false) {
    if (!elements.assistantMessages) {
        console.error('Assistant messages container not found');
        return null;
    }
    
    const messageId = `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    // Remove empty state if exists
    const emptyState = elements.assistantMessages.querySelector('.assistant-empty');
    if (emptyState) {
        emptyState.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `assistant-message assistant-message-${role}`;
    messageDiv.id = messageId;
    
    if (isLoading) {
        messageDiv.innerHTML = `
            <div class="assistant-message-content">
                <div class="spinner-small"></div>
                <span>Processing...</span>
            </div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="assistant-message-content">
                <div class="assistant-text">${escapeHtml(content).replace(/\n/g, '<br>')}</div>
            </div>
        `;
    }
    
    elements.assistantMessages.appendChild(messageDiv);
    elements.assistantMessages.scrollTop = elements.assistantMessages.scrollHeight;
    
    return messageId;
}

// Add assistant message with HTML support (for error messages)
function addAssistantMessageHTML(role, content, isLoading = false) {
    if (!elements.assistantMessages) {
        console.error('Assistant messages container not found');
        return null;
    }
    
    const messageId = `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    // Remove empty state if exists
    const emptyState = elements.assistantMessages.querySelector('.assistant-empty');
    if (emptyState) {
        emptyState.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `assistant-message assistant-message-${role}`;
    messageDiv.id = messageId;
    
    if (isLoading) {
        messageDiv.innerHTML = `
            <div class="assistant-message-content">
                <div class="spinner-small"></div>
                <span>Processing...</span>
            </div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="assistant-message-content">
                <div class="assistant-text">${content}</div>
            </div>
        `;
    }
    
    elements.assistantMessages.appendChild(messageDiv);
    elements.assistantMessages.scrollTop = elements.assistantMessages.scrollHeight;
    
    return messageId;
}

// Remove assistant message
function removeAssistantMessage(messageId) {
    const message = document.getElementById(messageId);
    if (message) {
        message.remove();
    }
}

// Clear assistant messages UI
function clearAssistantMessages() {
    if (!elements.assistantMessages) {
        return;
    }
    elements.assistantMessages.innerHTML = `
        <div class="assistant-empty">
            <p>💬 Start by generating an optimized CV, then request adjustments here</p>
            <p class="assistant-examples">
                Examples:<br>
                • "Add advanced Excel skill"<br>
                • "Fix 'advanced exce' to 'advanced excel'"<br>
                • "Add a section about my Python projects"
            </p>
        </div>
    `;
}

// Update assistant send button state
function updateAssistantSendButton() {
    if (!elements.assistantSendBtn || !elements.assistantInput) {
        console.log('Assistant elements not found:', {
            sendBtn: !!elements.assistantSendBtn,
            input: !!elements.assistantInput
        });
        return; // Elements not available
    }
    const hasInput = elements.assistantInput.value.trim().length > 0;
    // Allow using assistant with either optimized CV or original CV
    const hasCv = (state.optimizedCv && state.optimizedCv.trim().length > 0) || 
                  (state.cvText && state.cvText.trim().length > 0);
    const shouldEnable = hasInput && hasCv;
    
    console.log('Assistant button state:', {
        hasInput,
        hasCv,
        optimizedCvLength: state.optimizedCv ? state.optimizedCv.length : 0,
        cvTextLength: state.cvText ? state.cvText.length : 0,
        shouldEnable,
        currentDisabled: elements.assistantSendBtn.disabled
    });
    
    elements.assistantSendBtn.disabled = !shouldEnable;
}

// Clear assistant history
async function clearAssistantHistory() {
    if (!confirm('Are you sure you want to clear the entire conversation?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/assistant-history', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: state.assistantSessionId
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            showError(data.error);
            return;
        }
        
        // Clear local state
        state.assistantHistory = [];
        clearAssistantMessages();
        saveAssistantHistory();
        
    } catch (error) {
        showError(`Clear error: ${error.message}`);
    }
}

// Load assistant history from localStorage
function loadAssistantHistory() {
    try {
        const saved = localStorage.getItem('assistantHistory');
        if (saved) {
            state.assistantHistory = JSON.parse(saved);
        }
    } catch (error) {
        console.error('Error loading assistant history:', error);
    }
}

// Save assistant history to localStorage
function saveAssistantHistory() {
    try {
        localStorage.setItem('assistantHistory', JSON.stringify(state.assistantHistory));
    } catch (error) {
        console.error('Error saving assistant history:', error);
    }
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Quick Navigation Menu
function setupQuickNavigation() {
    // Re-fetch elements to ensure they're available
    const quickNavToggle = document.getElementById('quick-nav-toggle');
    const quickNavPopup = document.getElementById('quick-nav-popup');
    const quickNavItems = document.querySelectorAll('.quick-nav-item');
    
    if (!quickNavToggle || !quickNavPopup) {
        console.warn('Quick navigation elements not found');
        return;
    }

    // Toggle popup on button click
    quickNavToggle.addEventListener('click', (e) => {
        e.stopPropagation();
        quickNavPopup.classList.toggle('hidden');
    });

    // Handle navigation item clicks - use event delegation for better reliability
    if (quickNavItems.length > 0) {
        quickNavItems.forEach(item => {
            // Remove any existing listeners to avoid duplicates
            const newItem = item.cloneNode(true);
            item.parentNode.replaceChild(newItem, item);
            
            newItem.addEventListener('click', (e) => {
                e.stopPropagation();
                e.preventDefault();
                const navTarget = newItem.dataset.nav;
                console.log('Quick nav clicked:', navTarget);
                if (navTarget) {
                    navigateTo(navTarget);
                    // Close popup after navigation
                    quickNavPopup.classList.add('hidden');
                }
            });
        });
    } else {
        // Fallback: use event delegation on the popup
        quickNavPopup.addEventListener('click', (e) => {
            const navItem = e.target.closest('.quick-nav-item');
            if (navItem) {
                e.stopPropagation();
                e.preventDefault();
                const navTarget = navItem.dataset.nav;
                console.log('Quick nav clicked (delegation):', navTarget);
                if (navTarget) {
                    navigateTo(navTarget);
                    quickNavPopup.classList.add('hidden');
                }
            }
        });
    }

    // Close popup when clicking outside
    document.addEventListener('click', (e) => {
        const quickNavMenu = document.getElementById('quick-nav-menu');
        if (quickNavMenu && !quickNavMenu.contains(e.target)) {
            quickNavPopup.classList.add('hidden');
        }
    });

    // Close popup on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !quickNavPopup.classList.contains('hidden')) {
            quickNavPopup.classList.add('hidden');
        }
    });
}

// Navigate to a specific section
function navigateTo(target) {
    console.log('Navigating to:', target);
    
    switch (target) {
        case 'config':
            // Switch to generation tab and scroll to config section
            switchMainTab('generation');
            setTimeout(() => {
                const configSection = document.querySelector('.config-section');
                if (configSection) {
                    configSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                } else {
                    // Fallback: scroll to top of generation content
                    const genContent = document.getElementById('generation-content');
                    if (genContent) {
                        genContent.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }
                }
            }, 200);
            break;

        case 'api-key':
            // Switch to generation tab and focus on API key input
            switchMainTab('generation');
            setTimeout(() => {
                const apiKeyInput = document.getElementById('api-key');
                if (apiKeyInput) {
                    apiKeyInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    setTimeout(() => apiKeyInput.focus(), 300);
                }
            }, 200);
            break;

        case 'optimized-cv':
            // Switch to generation tab and open CV optimized tab
            switchMainTab('generation');
            setTimeout(() => {
                // Make sure results section is visible
                const resultsSection = document.getElementById('results-section');
                if (resultsSection) {
                    // Remove hidden class first (it has !important)
                    resultsSection.classList.remove('hidden');
                }
                // Switch to the tab
                switchTab('optimized-cv');
                setTimeout(() => {
                    // Scroll to results section or the tab content
                    const optimizedCvTab = document.getElementById('optimized-cv-tab');
                    if (optimizedCvTab) {
                        optimizedCvTab.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    } else if (resultsSection) {
                        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }
                }, 300);
            }, 300);
            break;

        case 'cover-letter':
            // Switch to generation tab and open cover letter tab
            switchMainTab('generation');
            setTimeout(() => {
                // Make sure results section is visible
                const resultsSection = document.getElementById('results-section');
                if (resultsSection) {
                    // Remove hidden class first (it has !important)
                    resultsSection.classList.remove('hidden');
                }
                // Switch to the tab
                switchTab('cover-letter');
                setTimeout(() => {
                    // Scroll to results section or the tab content
                    const coverLetterTab = document.getElementById('cover-letter-tab');
                    if (coverLetterTab) {
                        coverLetterTab.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    } else if (resultsSection) {
                        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }
                }, 300);
            }, 300);
            break;

        case 'assistant':
            // Switch to generation tab and open assistant tab
            switchMainTab('generation');
            setTimeout(() => {
                // Make sure results section is visible
                const resultsSection = document.getElementById('results-section');
                if (resultsSection) {
                    // Remove hidden class first (it has !important)
                    resultsSection.classList.remove('hidden');
                }
                // Switch to the tab
                switchTab('assistant');
                setTimeout(() => {
                    // Scroll to assistant section
                    const assistantTab = document.getElementById('assistant-tab');
                    if (assistantTab) {
                        assistantTab.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    } else if (resultsSection) {
                        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }
                }, 300);
            }, 300);
            break;

        case 'history':
            // Switch to history tab
            switchMainTab('history');
            setTimeout(() => {
                // Scroll to top of history content
                const historyContent = document.getElementById('history-content');
                if (historyContent) {
                    historyContent.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }, 200);
            break;

        default:
            console.warn('Unknown navigation target:', target);
    }
}

// Helper function to switch main tabs
function switchMainTab(tabName) {
    console.log('Switching to main tab:', tabName);
    
    // Re-fetch elements to ensure they're available
    const mainTabs = document.querySelectorAll('.main-tab-btn');
    const mainTabContents = document.querySelectorAll('.main-tab-content');
    
    // Update tab buttons
    mainTabs.forEach(tab => {
        if (tab.dataset.mainTab === tabName) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });

    // Update tab contents
    mainTabContents.forEach(content => {
        if (content.id === `${tabName}-content`) {
            content.classList.add('active');
            // Ensure the content is visible
            content.style.display = '';
        } else {
            content.classList.remove('active');
        }
    });

    // Reload history when switching to history tab
    if (tabName === 'history') {
        loadHistory();
    }
    
    console.log('Main tab switched to:', tabName);
}

// Display RAG sources for optimized CV
function displayRAGSources(sources) {
    if (!sources) return;
    
    const sourcesSection = document.getElementById('rag-sources-section');
    const cvSourcesDiv = document.getElementById('rag-cv-sources');
    const jdSourcesDiv = document.getElementById('rag-jd-sources');
    
    if (!sourcesSection || !cvSourcesDiv || !jdSourcesDiv) return;
    
    const cvSources = sources.cv_sources || [];
    const jdSources = sources.jd_sources || [];
    
    if (cvSources.length === 0 && jdSources.length === 0) {
        sourcesSection.classList.add('hidden');
        return;
    }
    
    // Display CV sources
    if (cvSources.length > 0) {
        cvSourcesDiv.innerHTML = cvSources.map((source, index) => 
            `<div class="rag-source-item">
                <span class="rag-source-number">${index + 1}</span>
                <div class="rag-source-text">${escapeHtml(source.substring(0, 200))}${source.length > 200 ? '...' : ''}</div>
            </div>`
        ).join('');
    } else {
        cvSourcesDiv.innerHTML = '<div class="rag-source-empty">No CV chunks retrieved</div>';
    }
    
    // Display JD sources
    if (jdSources.length > 0) {
        jdSourcesDiv.innerHTML = jdSources.map((source, index) => 
            `<div class="rag-source-item">
                <span class="rag-source-number">${index + 1}</span>
                <div class="rag-source-text">${escapeHtml(source.substring(0, 200))}${source.length > 200 ? '...' : ''}</div>
            </div>`
        ).join('');
    } else {
        jdSourcesDiv.innerHTML = '<div class="rag-source-empty">No JD chunks retrieved</div>';
    }
    
    sourcesSection.classList.remove('hidden');
}

// Display RAG sources in assistant chat
function displayRAGSourcesInAssistant(sources) {
    if (!sources || sources.length === 0) return;
    
    const sourcesText = sources.map((source, index) => 
        `[Source ${index + 1}]: ${source.substring(0, 150)}${source.length > 150 ? '...' : ''}`
    ).join('\n\n');
    
    addAssistantMessage('assistant', `\n\n🔍 Sources used:\n${sourcesText}`, false);
}

// Show logs modal
function showLogsModal() {
    if (!state.lastExecutionLogs) {
        showError('No execution logs available. Please optimize a CV first.');
        return;
    }
    
    // Re-fetch elements in case they're not initialized
    if (!elements.simplifiedLogContent) {
        elements.simplifiedLogContent = document.getElementById('simplified-log-text');
    }
    if (!elements.fullLogContent) {
        elements.fullLogContent = document.getElementById('full-log-text');
    }
    if (!elements.logsModal) {
        elements.logsModal = document.getElementById('logs-modal');
    }
    
    // Generate simplified log
    const simplifiedLog = generateSimplifiedLog(state.lastExecutionLogs);
    if (elements.simplifiedLogContent) {
        elements.simplifiedLogContent.innerHTML = simplifiedLog;
    }
    
    // Generate full log
    const fullLog = generateFullLog(state.lastExecutionLogs);
    if (elements.fullLogContent) {
        elements.fullLogContent.innerHTML = fullLog;
    }
    
    // Show modal
    if (elements.logsModal) {
        elements.logsModal.classList.remove('hidden');
        switchLogsTab('simplified');
    }
}

// Switch logs tab
function switchLogsTab(tabName) {
    // Update tab buttons
    if (elements.logsTabBtns) {
        elements.logsTabBtns.forEach(btn => {
            if (btn.dataset.logTab === tabName) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
    }
    
    // Update tab content
    document.querySelectorAll('.logs-tab-content').forEach(content => {
        if (content.id === `${tabName}-log-content`) {
            content.classList.add('active');
        } else {
            content.classList.remove('active');
        }
    });
}

// Generate simplified log
function generateSimplifiedLog(logs) {
    let html = '<div class="simplified-log">';
    
    // Header
    html += '<div class="log-section"><h3>📋 Execution Summary</h3>';
    html += `<p><strong>Model:</strong> ${logs.model_used || 'N/A'}</p>`;
    html += `<p><strong>Temperature:</strong> ${logs.temperature || 'N/A'}</p>`;
    html += `<p><strong>Word Count:</strong> ${logs.word_count || 0}</p>`;
    html += '</div>';
    
    // RAG Vectorization
    if (logs.rag_details) {
        html += '<div class="log-section"><h3>🔍 RAG Vectorization</h3>';
        
        // CV Indexing
        if (logs.rag_details.cv_indexing) {
            const cvIdx = logs.rag_details.cv_indexing;
            html += '<div class="log-subsection"><h4>CV Vectorization</h4>';
            html += `<p>✓ CV split into <strong>${cvIdx.chunks_count}</strong> chunks</p>`;
            html += `<p>• Total characters: ${cvIdx.total_chars.toLocaleString()}</p>`;
            html += `<p>• Average chunk size: ${Math.round(cvIdx.avg_chunk_size)} characters</p>`;
            if (cvIdx.chunk_sizes && cvIdx.chunk_sizes.length > 0) {
                html += `<p>• Chunk size range: ${Math.min(...cvIdx.chunk_sizes)} - ${Math.max(...cvIdx.chunk_sizes)} characters</p>`;
            }
            html += '</div>';
        }
        
        // JD Indexing
        if (logs.rag_details.jd_indexing) {
            const jdIdx = logs.rag_details.jd_indexing;
            html += '<div class="log-subsection"><h4>Job Description Vectorization</h4>';
            html += `<p>✓ Job description split into <strong>${jdIdx.chunks_count}</strong> chunks</p>`;
            html += `<p>• Total characters: ${jdIdx.total_chars.toLocaleString()}</p>`;
            html += `<p>• Average chunk size: ${Math.round(jdIdx.avg_chunk_size)} characters</p>`;
            if (jdIdx.chunk_sizes && jdIdx.chunk_sizes.length > 0) {
                html += `<p>• Chunk size range: ${Math.min(...jdIdx.chunk_sizes)} - ${Math.max(...jdIdx.chunk_sizes)} characters</p>`;
            }
            html += '</div>';
        }
        
        // Retrieval
        if (logs.rag_details.retrieval) {
            const ret = logs.rag_details.retrieval;
            html += '<div class="log-subsection"><h4>Semantic Search & Retrieval</h4>';
            const query = ret.query || '';
            html += `<p>✓ Query: "${escapeHtml(query.substring(0, 100))}${query.length > 100 ? '...' : ''}"</p>`;
            html += `<p>• Retrieved <strong>${ret.cv_chunks_details?.length || 0}</strong> CV chunks (top ${ret.k_cv || 5})</p>`;
            html += `<p>• Retrieved <strong>${ret.jd_chunks_details?.length || 0}</strong> JD chunks (top ${ret.k_jd || 3})</p>`;
            
            // CV Chunks with scores
            if (ret.cv_chunks_details && ret.cv_chunks_details.length > 0) {
                html += '<div class="chunks-list"><h5>CV Chunks (Cosine Similarity):</h5><ul>';
                ret.cv_chunks_details.forEach((chunk) => {
                    const score = chunk.similarity_score ? (chunk.similarity_score * 100).toFixed(1) : 'N/A';
                    html += `<li>Chunk ${chunk.index || 'N/A'}: <strong>${score}%</strong> similarity`;
                    const content = chunk.content || '';
                    html += `<div class="chunk-preview">${escapeHtml(content.substring(0, 150))}${content.length > 150 ? '...' : ''}</div></li>`;
                });
                html += '</ul></div>';
            }
            
            // JD Chunks with scores
            if (ret.jd_chunks_details && ret.jd_chunks_details.length > 0) {
                html += '<div class="chunks-list"><h5>JD Chunks (Cosine Similarity):</h5><ul>';
                ret.jd_chunks_details.forEach((chunk) => {
                    const score = chunk.similarity_score ? (chunk.similarity_score * 100).toFixed(1) : 'N/A';
                    html += `<li>Chunk ${chunk.index || 'N/A'}: <strong>${score}%</strong> similarity`;
                    const content = chunk.content || '';
                    html += `<div class="chunk-preview">${escapeHtml(content.substring(0, 150))}${content.length > 150 ? '...' : ''}</div></li>`;
                });
                html += '</ul></div>';
            }
            
            html += '</div>';
        }
        
        html += '</div>';
    }
    
    // Skills
    if (logs.cv_skills && logs.cv_skills.length > 0) {
        html += '<div class="log-section"><h3>💼 Skills Extraction</h3>';
        html += `<p>✓ Extracted <strong>${logs.cv_skills.length}</strong> CV skills</p>`;
        if (logs.job_skills && logs.job_skills.length > 0) {
            html += `<p>✓ Extracted <strong>${logs.job_skills.length}</strong> job skills</p>`;
        }
        if (logs.skills_comparison) {
            const comp = logs.skills_comparison;
            html += `<p>• Matched: ${comp.matched?.length || 0} skills</p>`;
            html += `<p>• Missing: ${comp.job_only?.length || 0} skills</p>`;
            if (comp.stats && comp.stats.avg_similarity) {
                html += `<p>• Average similarity: <strong>${(comp.stats.avg_similarity * 100).toFixed(1)}%</strong></p>`;
            }
        }
        html += '</div>';
    }
    
    // Agent Steps
    if (logs.agent_logs && logs.agent_logs.length > 0) {
        html += '<div class="log-section"><h3>⚙️ Agent Execution Steps</h3><ul class="agent-steps">';
        logs.agent_logs.forEach(log => {
            html += `<li>${escapeHtml(log)}</li>`;
        });
        html += '</ul></div>';
    }
    
    html += '</div>';
    return html;
}

// Generate full log (JSON format)
function generateFullLog(logs) {
    let html = '<div class="full-log">';
    html += '<pre class="json-log">';
    html += escapeHtml(JSON.stringify(logs, null, 2));
    html += '</pre>';
    html += '</div>';
    return html;
}