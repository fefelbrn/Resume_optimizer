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
    matchedSkillsData: null
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
    // Assistant elements (may be null if results section is hidden)
    assistantMessages: document.getElementById('assistant-messages'),
    assistantInput: document.getElementById('assistant-input'),
    assistantSendBtn: document.getElementById('assistant-send-btn'),
    clearAssistantBtn: document.getElementById('clear-assistant-btn'),
    // Quick navigation menu
    quickNavToggle: document.getElementById('quick-nav-toggle'),
    quickNavPopup: document.getElementById('quick-nav-popup'),
    quickNavItems: document.querySelectorAll('.quick-nav-item')
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
        showError('Erreur lors de l\'initialisation de l\'application: ' + error.message);
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
                <p>📭 Aucun historique pour le moment</p>
                <p class="history-empty-subtitle">Vos générations apparaîtront ici après utilisation de la section Génération</p>
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
                <p>📭 Aucun élément dans cette catégorie</p>
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
        
        const typeLabel = item.type === 'cv' ? 'CV Optimisé' : 'Lettre de Motivation';
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
                    ${item.metadata.target_words ? `<span>📝 ${item.metadata.target_words} mots</span>` : ''}
                </div>
                <div class="history-item-content">${escapeHtml(preview)}</div>
                <div class="history-item-actions">
                    <button class="history-btn" onclick="loadHistoryItem(${item.id})">
                        🔄 Recharger
                    </button>
                    <button class="history-btn secondary" onclick="copyHistoryItem(${item.id})">
                        📋 Copier
                    </button>
                    <button class="history-btn secondary" onclick="downloadHistoryItem(${item.id})">
                        💾 Télécharger
                    </button>
                    <button class="history-btn" onclick="deleteHistoryItem(${item.id})" style="background: var(--error-color); color: white; border-color: var(--error-color);">
                        🗑️ Supprimer
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
    if (confirm('Êtes-vous sûr de vouloir effacer tout l\'historique ?')) {
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
        showError('✓ Contenu copié dans le presse-papier !');
        setTimeout(() => {
            elements.errorModal.classList.add('hidden');
        }, 2000);
    }).catch(() => {
        showError('Erreur lors de la copie');
    });
}

function downloadHistoryItem(id) {
    const history = getHistory();
    const item = history.find(h => h.id === id);
    if (!item) return;
    
    const filename = item.type === 'cv' ? 'cv_optimise.txt' : 'lettre_motivation.txt';
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
    if (!confirm('Supprimer cet élément de l\'historique ?')) return;
    
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
        elements.cvCount.textContent = `${cvWords} mots`;
    }
    if (elements.jdCount && elements.jdTextarea && !elements.jdTextarea.classList.contains('hidden')) {
        const jdWords = elements.jdTextarea.value.trim().split(/\s+/).filter(w => w.length > 0).length;
        elements.jdCount.textContent = `${jdWords} mots`;
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
        showLoading('Extraction du texte...');

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
            showError('Le fichier est vide ou n\'a pas pu être extrait');
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
        showError(`Erreur lors de l'upload: ${error.message}`);
    } finally {
        hideLoading();
    }
}

// Optimize CV
async function optimizeCv() {
    // Validation
    if (!validateInputs()) return;

    showLoading('Optimisation du CV en cours...');

    const payload = {
        cv_text: state.cvText,
        job_description: state.jobDescription,
        api_key: elements.apiKeyInput.value,
        language: elements.languageSelect.value,
        model: elements.modelSelect.value,
        temperature: parseFloat(elements.temperatureInput.value),
        min_experiences: parseInt(elements.minExperiences.value),
        max_experiences: parseInt(elements.maxExperiences.value),
        max_date_years: elements.maxDateYears.value || null
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
        showError(`Erreur: ${error.message}`);
    } finally {
        hideLoading();
    }
}

// Generate cover letter
async function generateLetter() {
    // Validation
    if (!validateInputs()) return;

    if (!state.optimizedCv && !state.cvText) {
        showError('Veuillez d\'abord optimiser votre CV ou avoir un CV dans le champ.');
        return;
    }

    showLoading('Génération de la lettre de motivation...');

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
        showError(`Erreur: ${error.message}`);
    } finally {
        hideLoading();
    }
}

// Validate inputs
function validateInputs() {
    if (!elements.apiKeyInput.value.trim()) {
        showError('Veuillez entrer votre clé API OpenAI');
        elements.apiKeyInput.focus();
        return false;
    }

    if (!state.cvText.trim()) {
        showError('Veuillez entrer ou uploader votre CV');
        elements.cvTextarea.focus();
        return false;
    }

    if (!state.jobDescription.trim()) {
        showError('Veuillez entrer ou uploader la description du poste');
        elements.jdTextarea.focus();
        return false;
    }

    return true;
}

// Switch tabs
function switchTab(tabName) {
    // Update tab buttons
    elements.tabs.forEach(tab => {
        if (tab.dataset.tab === tabName) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });

    // Update tab contents
    elements.tabContents.forEach(content => {
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
        showError('Aucun contenu à copier');
        return;
    }

    try {
        await navigator.clipboard.writeText(text);
        // Show a brief success message (using a simple alert for positive feedback)
        const originalText = elements.errorModalClose.textContent;
        elements.errorModalClose.textContent = '✓ Copié !';
        setTimeout(() => {
            elements.errorModalClose.textContent = originalText;
        }, 2000);
    } catch (error) {
        showError(`Erreur lors de la copie: ${error.message}`);
    }
}

// Download content
async function downloadContent(type) {
    if (type === 'optimized-cv') {
        if (!state.optimizedCv) {
            showError('Aucun CV optimisé à télécharger');
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
                throw new Error(error.error || 'Erreur lors de la génération du PDF');
            }
            
            // Download PDF
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'cv_optimise.pdf';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Error generating PDF:', error);
            showError('Erreur lors de la génération du PDF: ' + error.message);
            // Fallback to TXT if PDF generation fails
            const blob = new Blob([state.optimizedCv], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'cv_optimise.txt';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
    } else if (type === 'cover-letter') {
        const text = state.coverLetter;
        if (!text) {
            showError('Aucune lettre de motivation à télécharger');
            return;
        }
        
        const blob = new Blob([text], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'lettre_motivation.txt';
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
function showLoading(message = 'Traitement en cours...') {
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
                model: elements.modelSelect.value
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
                model: elements.modelSelect.value
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
            <div class="stat-label">Correspondance</div>
            <div class="stat-value" style="color: var(--success-color);">${stats.match_percentage || 0}%</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">Compétences CV</div>
            <div class="stat-value">${stats.total_cv || 0}</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">Compétences Offre</div>
            <div class="stat-value">${stats.total_job || 0}</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">Correspondances</div>
            <div class="stat-value" style="color: var(--success-color);">${stats.matched_count || 0}</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">Manquantes</div>
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
    
    elements.skillsTags.innerHTML = tagsHTML || '<p style="color: var(--text-secondary);">Aucune compétence à afficher</p>';
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
        showError('Veuillez d\'abord charger votre CV');
        return;
    }
    if (!elements.apiKeyInput.value.trim()) {
        showError('Veuillez entrer votre clé API OpenAI');
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
            let responseText = data.explanation || 'Modification effectuée';
            
            // Update CV if needed
            if (data.action === 'update_cv' || data.action === 'update_both') {
                state.optimizedCv = data.updated_cv;
                elements.optimizedCvContent.textContent = data.updated_cv;
                responseText += '\n\n✅ CV optimisé mis à jour';
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
                responseText += '\n\n✅ Compétences mises à jour';
            }
            
            // Add assistant response
            addAssistantMessage('assistant', responseText, false);
            
            // Save to history
            state.assistantHistory.push({
                request: request,
                response: data
            });
            saveAssistantHistory();
        } else {
            addAssistantMessage('assistant', `Erreur: ${data.error || 'Modification échouée'}`, false);
        }
        
    } catch (error) {
        removeAssistantMessage(loadingId);
        showError(`Erreur lors de l'envoi: ${error.message}`);
        addAssistantMessage('assistant', `Erreur: ${error.message}`, false);
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
                <span>Traitement en cours...</span>
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
                <span>Traitement en cours...</span>
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
            <p>💬 Commencez par générer un CV optimisé, puis demandez des ajustements ici</p>
            <p class="assistant-examples">
                Exemples :<br>
                • "Ajoute la compétence Excel avancé"<br>
                • "Corrige 'advanced exce' en 'advanced excel'"<br>
                • "Ajoute une section sur mes projets Python"
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
    if (!confirm('Êtes-vous sûr de vouloir effacer toute la conversation ?')) {
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
        showError(`Erreur lors de l'effacement: ${error.message}`);
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
    if (!elements.quickNavToggle || !elements.quickNavPopup) {
        console.warn('Quick navigation elements not found');
        return;
    }

    // Toggle popup on button click
    elements.quickNavToggle.addEventListener('click', (e) => {
        e.stopPropagation();
        elements.quickNavPopup.classList.toggle('hidden');
    });

    // Handle navigation item clicks
    elements.quickNavItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.stopPropagation();
            const navTarget = item.dataset.nav;
            navigateTo(navTarget);
            // Close popup after navigation
            elements.quickNavPopup.classList.add('hidden');
        });
    });

    // Close popup when clicking outside
    document.addEventListener('click', (e) => {
        const quickNavMenu = document.getElementById('quick-nav-menu');
        if (quickNavMenu && !quickNavMenu.contains(e.target)) {
            elements.quickNavPopup.classList.add('hidden');
        }
    });

    // Close popup on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !elements.quickNavPopup.classList.contains('hidden')) {
            elements.quickNavPopup.classList.add('hidden');
        }
    });
}

// Navigate to a specific section
function navigateTo(target) {
    switch (target) {
        case 'config':
            // Switch to generation tab and scroll to config section
            switchMainTab('generation');
            setTimeout(() => {
                const configSection = document.querySelector('.config-section');
                if (configSection) {
                    configSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }, 100);
            break;

        case 'api-key':
            // Switch to generation tab and focus on API key input
            switchMainTab('generation');
            setTimeout(() => {
                const apiKeyInput = document.getElementById('api-key');
                if (apiKeyInput) {
                    apiKeyInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    apiKeyInput.focus();
                }
            }, 100);
            break;

        case 'optimized-cv':
            // Switch to generation tab and open CV optimized tab
            switchMainTab('generation');
            setTimeout(() => {
                switchTab('optimized-cv');
                const resultsSection = document.getElementById('results-section');
                if (resultsSection) {
                    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }, 100);
            break;

        case 'cover-letter':
            // Switch to generation tab and open cover letter tab
            switchMainTab('generation');
            setTimeout(() => {
                switchTab('cover-letter');
                const resultsSection = document.getElementById('results-section');
                if (resultsSection) {
                    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }, 100);
            break;

        case 'assistant':
            // Switch to generation tab and open assistant tab
            switchMainTab('generation');
            setTimeout(() => {
                switchTab('assistant');
                const resultsSection = document.getElementById('results-section');
                if (resultsSection) {
                    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }, 100);
            break;

        case 'history':
            // Switch to history tab
            switchMainTab('history');
            break;

        default:
            console.warn('Unknown navigation target:', target);
    }
}

// Helper function to switch main tabs
function switchMainTab(tabName) {
    // Update tab buttons
    elements.mainTabs.forEach(tab => {
        if (tab.dataset.mainTab === tabName) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });

    // Update tab contents
    elements.mainTabContents.forEach(content => {
        if (content.id === `${tabName}-content`) {
            content.classList.add('active');
        } else {
            content.classList.remove('active');
        }
    });

    // Reload history when switching to history tab
    if (tabName === 'history') {
        loadHistory();
    }
}