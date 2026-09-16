// Experiments Lab JavaScript
document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();

    // Sidebar Navigation
    const sidebarItems = document.querySelectorAll('.experiments-sidebar-item');
    const experimentPanels = document.querySelectorAll('.experiment-panel');

    sidebarItems.forEach(item => {
        item.addEventListener('click', () => {
            const experimentId = item.dataset.experiment;

            // Update active states
            sidebarItems.forEach(i => i.classList.remove('active'));
            item.classList.add('active');

            experimentPanels.forEach(panel => {
                panel.classList.remove('active');
                if (panel.id === `${experimentId}-panel`) {
                    panel.classList.add('active');
                }
            });

            lucide.createIcons();
        });
    });

    // ASR Benchmarking
    setupASRBenchmarking();

    // Voice AI Stack
    setupVoiceAIStack();
});

function setupASRBenchmarking() {
    const form = document.getElementById('asr-form');
    const uploadZone = document.getElementById('asr-upload-zone');
    const uploadText = document.getElementById('asr-upload-text');
    const fileInput = document.getElementById('asr-file-input');
    const fileInfo = document.getElementById('asr-file-info');
    const filename = document.getElementById('asr-filename');
    const clearFileBtn = document.getElementById('asr-clear-file');
    const runBtn = document.getElementById('asr-run-btn');
    const btnText = document.getElementById('asr-btn-text');
    const btnSpinner = document.getElementById('asr-btn-spinner');
    const loadingState = document.getElementById('asr-loading');
    const resultsContainer = document.getElementById('asr-results');

    let selectedFile = null;

    // Provider logos mapping
    const providerLogos = {
        'openai': 'https://cdn.simpleicons.org/openai',
        'deepgram': 'https://avatars.githubusercontent.com/u/10355252?s=200',
        'assemblyai': 'https://avatars.githubusercontent.com/u/31171742?s=200',
        'google-v1': 'https://cdn.simpleicons.org/google',
        'google-v2-chirp2': 'https://cdn.simpleicons.org/google',
        'google-v2-chirp3': 'https://cdn.simpleicons.org/google',
        'aws': 'https://cdn.simpleicons.org/amazonaws'
    };

    function clearFile() {
        selectedFile = null;
        fileInput.value = '';
        fileInfo.style.display = 'none';
        uploadZone.classList.remove('dragover');
        uploadText.textContent = 'Click to upload or drag and drop';
    }

    // Upload zone click
    uploadZone.addEventListener('click', () => {
        if (!selectedFile) {
            fileInput.click();
        }
    });

    // Clear file button
    if (clearFileBtn) {
        clearFileBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            clearFile();
        });
    }

    // File selection
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            selectedFile = file;
            filename.textContent = file.name;
            fileInfo.style.display = 'block';
            uploadText.textContent = file.name;
            lucide.createIcons();
        }
    });

    // Drag and drop
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        if (!selectedFile) {
            uploadZone.classList.add('dragover');
        }
    });

    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('dragover');
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        if (!selectedFile) {
            const file = e.dataTransfer.files[0];
            if (file && file.type.match('audio.*')) {
                selectedFile = file;
                filename.textContent = file.name;
                fileInfo.style.display = 'block';
                uploadText.textContent = file.name;
                lucide.createIcons();
            }
        }
    });

    // Form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const selectedProviders = Array.from(
            document.querySelectorAll('input[name="provider"]:checked')
        ).map(cb => cb.value);

        if (selectedProviders.length === 0) {
            alert('Please select at least one provider.');
            return;
        }

        if (!selectedFile) {
            alert('Please upload an audio file.');
            return;
        }

        // Initialize status bar
        initializeStatusBar(selectedProviders);

        // Auto-scroll to status bar
        document.getElementById('asr-status-bar').scrollIntoView({ behavior: 'smooth', block: 'start' });

        // Disable button and show loading state
        runBtn.disabled = true;
        btnText.style.display = 'none';
        btnSpinner.style.display = 'inline';
        loadingState.classList.add('active');
        resultsContainer.classList.remove('active');

        let completedCount = 0;
        const totalProviders = selectedProviders.length;
        const allResults = [];
        const transcriptsForJudging = {};

        try {
            // Create a promise for each provider
            const promises = selectedProviders.map(async (provider) => {
                try {
                    // Update status to running
                    updateProviderStatus(provider, 'running');

                    const formData = new FormData();
                    formData.append('audio', selectedFile);
                    // Send single provider in list
                    formData.append('providers', JSON.stringify([provider]));

                    const response = await fetch('http://localhost:5000/api/asr/benchmark', {
                        method: 'POST',
                        body: formData
                    });

                    if (!response.ok) {
                        throw new Error(`API error: ${response.statusText}`);
                    }

                    const data = await response.json();

                    // Should receive exactly one result
                    if (data.results && data.results.length > 0) {
                        const result = data.results[0];
                        allResults.push(result);

                        // Store for judging
                        const providerKey = result.model && result.model !== 'default'
                            ? `${result.provider}_${result.model}`
                            : `${result.provider}_default`;
                        transcriptsForJudging[providerKey] = result.transcript;

                        // Update status to done
                        const isError = result.transcript && result.transcript.startsWith('ERROR:');
                        updateProviderStatus(provider, isError ? 'error' : 'done');
                    } else {
                        throw new Error('No result returned');
                    }
                } catch (err) {
                    console.error(`Error with ${provider}:`, err);
                    updateProviderStatus(provider, 'error');
                    allResults.push({
                        provider: provider,
                        model: 'default',
                        transcript: `ERROR: ${err.message}`,
                        wer: 'N/A',
                        latency: 0
                    });
                } finally {
                    // Update progress
                    completedCount++;
                    updateProgress(completedCount, totalProviders);
                }
            });

            // Wait for all providers to finish
            await Promise.all(promises);

            // Call Judge Endpoint if we have results
            let finalData = { results: allResults, consensus: 'N/A', winner: null };

            if (Object.keys(transcriptsForJudging).length >= 2) {
                try {
                    const judgeResponse = await fetch('http://localhost:5000/api/asr/judge', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ transcripts: transcriptsForJudging })
                    });

                    if (judgeResponse.ok) {
                        const judgeData = await judgeResponse.json();
                        finalData.consensus = judgeData.consensus || 'N/A';
                        finalData.winner = judgeData.winner;

                        // Update WERs in results
                        finalData.results.forEach(res => {
                            const key = res.model && res.model !== 'default'
                                ? `${res.provider}_${res.model}`
                                : `${res.provider}_default`;
                            if (judgeData.wers && judgeData.wers[key]) {
                                res.wer = judgeData.wers[key];
                            }
                        });
                    }
                } catch (judgeErr) {
                    console.error('Judging failed:', judgeErr);
                }
            }

            displayASRResults(finalData);

        } catch (error) {
            displayASRError(error.message);
        } finally {
            loadingState.classList.remove('active');
            runBtn.disabled = false;
            btnText.style.display = 'inline';
            btnSpinner.style.display = 'none';
        }
    });

    function initializeStatusBar(providers) {
        const statusBar = document.getElementById('asr-status-bar');
        const providerStatusList = document.getElementById('asr-provider-status');

        statusBar.style.display = 'block';

        // Reset progress
        document.getElementById('asr-status-percentage').textContent = '0%';
        document.getElementById('asr-progress-fill').style.width = '0%';

        // Initialize provider status items
        let html = '';
        providers.forEach(provider => {
            const logo = providerLogos[provider] || '';
            const displayName = formatProviderName(provider);

            html += `
                <div class="provider-status-item" id="status-${provider}">
                    <div class="status-icon pending">
                        <i data-lucide="circle"></i>
                    </div>
                    ${logo ? `<img src="${logo}" alt="${provider}" class="provider-logo" />` : ''}
                    <span>${displayName}</span>
                </div>
            `;
        });

        providerStatusList.innerHTML = html;
        lucide.createIcons();
    }

    function updateProviderStatus(provider, status) {
        const statusItem = document.getElementById(`status-${provider}`);
        if (!statusItem) return;

        const statusIcon = statusItem.querySelector('.status-icon');

        // Update classes
        statusItem.className = `provider-status-item ${status}`;
        statusIcon.className = `status-icon ${status}`;

        // Update icon
        let iconName = 'circle';
        switch (status) {
            case 'running':
                iconName = 'loader-2';
                break;
            case 'done':
                iconName = 'check-circle';
                break;
            case 'error':
                iconName = 'x-circle';
                break;
        }

        statusIcon.innerHTML = `<i data-lucide="${iconName}"></i>`;
        lucide.createIcons();
    }

    function updateProgress(completed, total) {
        const percentage = Math.round((completed / total) * 100);
        document.getElementById('asr-status-percentage').textContent = `${percentage}%`;
        document.getElementById('asr-progress-fill').style.width = `${percentage}%`;
    }

    function formatProviderName(provider) {
        const nameMap = {
            'openai': 'OpenAI Whisper',
            'deepgram': 'Deepgram',
            'assemblyai': 'AssemblyAI',
            'google-v1': 'Google V1',
            'google-v2-chirp2': 'Google V2 Chirp 2',
            'google-v2-chirp3': 'Google V2 Chirp 3',
            'aws': 'AWS Transcribe'
        };
        return nameMap[provider] || provider;
    }

    function displayASRResults(data) {
        const resultsContainer = document.getElementById('asr-results');

        let html = '<h2 style="margin-bottom: 1.5rem;">Benchmark Results</h2>';

        if (data.results && data.results.length > 0) {
            html += '<div class="results-table"><table>';
            html += `
                <thead>
                    <tr>
                        <th>Provider</th>
                        <th>Transcript</th>
                        <th style="text-align: right;">WER</th>
                        <th style="text-align: right;">Engine Latency</th>
                        <th style="text-align: right;">Upload Time</th>
                        <th style="text-align: right;">Total Latency</th>
                    </tr>
                </thead>
                <tbody>
            `;

            // Add consensus row if available
            if (data.consensus && data.consensus !== 'N/A') {
                html += `
                    <tr class="consensus-row">
                        <td><strong>🎯 LLM Consensus</strong></td>
                        <td class="transcript-cell">
                            <div class="transcript-truncated">${truncateText(data.consensus, 100)}</div>
                            ${data.consensus.length > 100 ? `<button class="transcript-expand-btn" onclick="expandTranscript(this, '${escapeHtml(data.consensus)}')">View full text</button>` : ''}
                        </td>
                        <td style="text-align: right;">—</td>
                        <td style="text-align: right;">—</td>
                    </tr>
                `;
            }

            // Add provider rows
            data.results.forEach(result => {
                const isWinner = result.provider === data.winner?.split('_')[0];
                const isError = result.transcript && result.transcript.startsWith('ERROR:');
                const rowClass = isError ? 'error-row' : (isWinner ? 'winner-row' : '');
                const logo = providerLogos[result.provider] || providerLogos[`${result.provider}-${result.model}`] || '';

                html += `<tr class="${rowClass}">`;

                // Provider cell with logo
                html += `
                    <td>
                        <div class="provider-cell">
                            ${logo ? `<img src="${logo}" alt="${result.provider}" class="provider-logo">` : ''}
                            <div>
                                <div style="font-weight: 500;">${result.provider}</div>
                                ${result.model && result.model !== 'default' ? `<div style="font-size: 0.75rem; color: var(--muted-foreground);">${result.model}</div>` : ''}
                            </div>
                            ${isWinner ? '<div class="winner-badge">🏆 Winner</div>' : ''}
                        </div>
                    </td>
                `;

                // Transcript cell
                html += `
                    <td class="transcript-cell">
                        <div class="transcript-truncated">${truncateText(result.transcript, 100)}</div>
                        ${result.transcript.length > 100 && !isError ? `<button class="transcript-expand-btn" onclick="expandTranscript(this, '${escapeHtml(result.transcript)}')">View full text</button>` : ''}
                    </td>
                `;

                // WER cell
                html += `<td style="text-align: right;">${result.wer !== 'N/A' ? (result.wer * 100).toFixed(1) + '%' : 'N/A'}</td>`;

                // Latency cell
                // Latency cells
                const timing = result.timing || {};
                const engineLatency = result.latency.toFixed(2) + 's';
                const uploadTime = timing.upload_time_sec !== undefined && timing.upload_time_sec > 0
                    ? timing.upload_time_sec.toFixed(2) + 's'
                    : 'N/A';
                const totalTime = timing.total_pipeline_time_sec !== undefined
                    ? timing.total_pipeline_time_sec.toFixed(2) + 's'
                    : engineLatency; // Fallback if no timing info

                html += `<td style="text-align: right;">${engineLatency}</td>`;
                html += `<td style="text-align: right; color: var(--muted-foreground);">${uploadTime}</td>`;
                html += `<td style="text-align: right; font-weight: 500;">${totalTime}</td>`;

                html += `</tr>`;
            });

            html += '</tbody></table></div>';
        } else {
            html += '<p>No results available.</p>';
        }

        resultsContainer.innerHTML = html;
        resultsContainer.classList.add('active');

        // Auto-scroll to results section
        resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function truncateText(text, maxLength) {
        if (!text) return 'N/A';
        if (text.length <= maxLength) return escapeHtml(text);
        return escapeHtml(text.substring(0, maxLength)) + '...';
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Global function for expanding transcripts
window.expandTranscript = function (button, fullText) {
    const cell = button.parentElement;
    const truncatedDiv = cell.querySelector('.transcript-truncated');

    if (button.textContent === 'View full text') {
        truncatedDiv.innerHTML = fullText;
        button.textContent = 'Show less';
    } else {
        // Re-apply truncation and escaping
        const maxLength = 100; // This should match the truncation length used in displayASRResults
        const truncatedText = fullText.length <= maxLength ? escapeHtml(fullText) : escapeHtml(fullText.substring(0, maxLength)) + '...';
        truncatedDiv.innerHTML = truncatedText;
        button.textContent = 'View full text';
    }
};

// Helper functions for truncation and HTML escaping, made global for window.expandTranscript
function truncateText(text, maxLength) {
    if (!text) return 'N/A';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function displayASRError(message) {
    const resultsContainer = document.getElementById('asr-results');
    resultsContainer.innerHTML = `
        <div class="error-message">
            <strong>Error:</strong> ${message}
            <p style="margin-top: 0.5rem; font-size: 0.875rem;">Make sure the Flask API server is running on port 5000.</p>
        </div>
    `;
    resultsContainer.classList.add('active');
}

function setupVoiceAIStack() {
    const form = document.getElementById('voice-ai-form');
    const uploadZone = document.getElementById('voice-ai-upload-zone');
    const fileInput = document.getElementById('voice-ai-file-input');
    const fileInfo = document.getElementById('voice-ai-file-info');
    const filename = document.getElementById('voice-ai-filename');
    const loadingState = document.getElementById('voice-ai-loading');
    const resultsContainer = document.getElementById('voice-ai-results');

    let selectedFile = null;

    // Upload zone click
    uploadZone.addEventListener('click', () => fileInput.click());

    // File selection
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            selectedFile = file;
            filename.textContent = file.name;
            fileInfo.style.display = 'block';
        }
    });

    // Drag and drop
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });

    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('dragover');
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file && file.type.match('audio.*')) {
            selectedFile = file;
            filename.textContent = file.name;
            fileInfo.style.display = 'block';
        }
    });

    // Form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (!selectedFile) {
            alert('Please upload an audio file.');
            return;
        }

        const sttProvider = form.querySelector('[name="stt-provider"]').value;
        const llmModel = form.querySelector('[name="llm-model"]').value;
        const ttsProvider = form.querySelector('[name="tts-provider"]').value;

        // Show loading state
        loadingState.classList.add('active');
        resultsContainer.classList.remove('active');

        try {
            const formData = new FormData();
            formData.append('audio', selectedFile);
            formData.append('stt_provider', sttProvider);
            formData.append('llm_model', llmModel);
            formData.append('tts_provider', ttsProvider);

            const response = await fetch('http://localhost:5000/api/voice-ai/run', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`API error: ${response.statusText}`);
            }

            const data = await response.json();
            displayVoiceAIResults(data);
        } catch (error) {
            displayVoiceAIError(error.message);
        } finally {
            loadingState.classList.remove('active');
        }
    });
}

function displayVoiceAIResults(data) {
    const resultsContainer = document.getElementById('voice-ai-results');

    let html = '<h2 style="margin-bottom: 1.5rem;">Voice AI Stack Results</h2>';

    html += `
        <div class="result-card">
            <h4>Pipeline Output</h4>
            <div style="margin-top: 1rem;">
                <div style="margin-bottom: 1rem;">
                    <strong>STT Transcript:</strong>
                    <div style="padding: 0.75rem; background: var(--secondary); border-radius: 6px; margin-top: 0.5rem;">
                        ${data.transcript || 'N/A'}
                    </div>
                </div>
                <div style="margin-bottom: 1rem;">
                    <strong>LLM Response:</strong>
                    <div style="padding: 0.75rem; background: var(--secondary); border-radius: 6px; margin-top: 0.5rem;">
                        ${data.llm_response || 'N/A'}
                    </div>
                </div>
                ${data.audio_url ? `
                <div style="margin-bottom: 1rem;">
                    <strong>TTS Output:</strong>
                    <audio controls style="width: 100%; margin-top: 0.5rem;">
                        <source src="${data.audio_url}" type="audio/mpeg">
                    </audio>
                </div>
                ` : ''}
            </div>
        </div>
    `;

    if (data.metrics) {
        html += `
            <div class="result-card">
                <h4>Performance Metrics</h4>
                <div class="result-metrics">
                    ${data.metrics.stt_latency_ms ? `
                    <div class="metric-item">
                        <div class="metric-label">STT Latency</div>
                        <div class="metric-value">${data.metrics.stt_latency_ms}ms</div>
                    </div>
                    ` : ''}
                    ${data.metrics.llm_latency_ms ? `
                    <div class="metric-item">
                        <div class="metric-label">LLM Latency</div>
                        <div class="metric-value">${data.metrics.llm_latency_ms}ms</div>
                    </div>
                    ` : ''}
                    ${data.metrics.tts_latency_ms ? `
                    <div class="metric-item">
                        <div class="metric-label">TTS Latency</div>
                        <div class="metric-value">${data.metrics.tts_latency_ms}ms</div>
                    </div>
                    ` : ''}
                    ${data.metrics.e2e_latency_ms ? `
                    <div class="metric-item">
                        <div class="metric-label">E2E Latency</div>
                        <div class="metric-value">${data.metrics.e2e_latency_ms}ms</div>
                    </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    resultsContainer.innerHTML = html;
    resultsContainer.classList.add('active');
}

function displayVoiceAIError(message) {
    const resultsContainer = document.getElementById('voice-ai-results');
    resultsContainer.innerHTML = `
        <div class="error-message">
            <strong>Error:</strong> ${message}
            <p style="margin-top: 0.5rem; font-size: 0.875rem;">Make sure the Flask API server is running on port 5000.</p>
        </div>
    `;
    resultsContainer.classList.add('active');
}
