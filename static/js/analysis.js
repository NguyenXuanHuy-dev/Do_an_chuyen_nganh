// Analysis & Visual Charts Logic

document.addEventListener('DOMContentLoaded', () => {
    initApiKeyManager();
    initQuickTest();
    initFileUpload();
    initSessionCharts();
    initTableFilters();
});

// 0. API Key Manager & Prompt Presets
let currentPromptTemplates = {};

async function initApiKeyManager() {
    const statusBadge = document.getElementById('api-key-status-badge');
    const inputKey = document.getElementById('gemini-api-key-input');
    const btnSave = document.getElementById('btn-save-api-key');
    const promptSelect = document.getElementById('prompt-mode-select');
    const promptPreviewArea = document.getElementById('custom-prompt-preview');
    const btnTogglePromptView = document.getElementById('btn-toggle-prompt-view');

    // 1. Fetch current API Key status
    try {
        const resp = await fetch('/analysis/api-key');
        const data = await resp.json();
        if (data.has_key) {
            if (statusBadge) {
                statusBadge.className = 'badge badge-pos';
                statusBadge.innerHTML = '🟢 Đã gán API Key (Gemini LLM Active)';
            }
            if (inputKey && data.masked_key) {
                inputKey.placeholder = `Đã lưu: ${data.masked_key}`;
            }
        } else {
            if (statusBadge) {
                statusBadge.className = 'badge badge-neu';
                statusBadge.innerHTML = '⚪ Chưa gán API Key (Dùng engine nội bộ)';
            }
        }
    } catch (e) {
        console.error('Error checking API key:', e);
    }

    // 2. Fetch Prompt Templates
    try {
        const resp = await fetch('/analysis/prompts-list');
        currentPromptTemplates = await resp.json();
        if (promptPreviewArea && promptSelect) {
            promptPreviewArea.value = currentPromptTemplates[promptSelect.value] || '';
        }
    } catch (e) {
        console.error('Error fetching prompts:', e);
    }

    // 3. Prompt Mode change listener
    if (promptSelect && promptPreviewArea) {
        promptSelect.addEventListener('change', () => {
            const mode = promptSelect.value;
            promptPreviewArea.value = currentPromptTemplates[mode] || '';
        });
    }

    // Toggle Prompt View
    if (btnTogglePromptView && promptPreviewArea) {
        btnTogglePromptView.addEventListener('click', () => {
            const container = document.getElementById('prompt-preview-container');
            if (container) {
                container.style.display = container.style.display === 'none' ? 'block' : 'none';
            }
        });
    }

    // 4. Save API Key button
    if (btnSave && inputKey) {
        btnSave.addEventListener('click', async () => {
            const keyVal = inputKey.value.trim();
            if (!keyVal) {
                showToast('Vui lòng nhập API Key', 'warning');
                return;
            }

            btnSave.disabled = true;
            btnSave.innerHTML = '<span>⏳</span> Đang lưu...';

            try {
                const resp = await fetch('/analysis/api-key', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ api_key: keyVal })
                });
                const data = await resp.json();
                btnSave.disabled = false;
                btnSave.innerHTML = '<span>💾</span> Lưu API Key';

                if (data.success) {
                    showToast(data.message, 'success');
                    if (statusBadge) {
                        statusBadge.className = 'badge badge-pos';
                        statusBadge.innerHTML = '🟢 Đã gán API Key (Gemini LLM Active)';
                    }
                    inputKey.value = '';
                    inputKey.placeholder = 'Đã cập nhật API Key thành công!';
                } else {
                    showToast(data.error || 'Lỗi lưu key', 'danger');
                }
            } catch (e) {
                btnSave.disabled = false;
                btnSave.innerHTML = '<span>💾</span> Lưu API Key';
                showToast('Lỗi kết nối máy chủ', 'danger');
            }
        });
    }
}

// 1. Quick Test Single Sentence & Visual Sentiment Inspector (DevToolKit Style)
function initQuickTest() {
    const btn = document.getElementById('btn-quick-analyze');
    const input = document.getElementById('quick-text-input');
    const wordCountSpan = document.getElementById('quick-word-count');
    const presetBtns = document.querySelectorAll('.preset-sample-btn');
    const promptSelect = document.getElementById('prompt-mode-select');
    const promptPreviewArea = document.getElementById('custom-prompt-preview');

    if (!btn || !input) return;

    // Live word count listener
    input.addEventListener('input', () => {
        const words = input.value.trim().split(/\s+/).filter(w => w.length > 0);
        if (wordCountSpan) {
            wordCountSpan.textContent = `${words.length} từ (${input.value.length} ký tự)`;
        }
    });

    // Preset Sample Buttons
    presetBtns.forEach(pBtn => {
        pBtn.addEventListener('click', () => {
            input.value = pBtn.dataset.sampleText;
            const words = input.value.trim().split(/\s+/).filter(w => w.length > 0);
            if (wordCountSpan) {
                wordCountSpan.textContent = `${words.length} từ (${input.value.length} ký tự)`;
            }
            runDetailedAnalysis();
        });
    });

    btn.addEventListener('click', runDetailedAnalysis);

    async function runDetailedAnalysis() {
        const text = input.value.trim();
        if (!text) {
            showToast('Vui lòng nhập văn bản để phân tích', 'warning');
            return;
        }

        const promptMode = promptSelect ? promptSelect.value : 'general';
        const customPrompt = promptPreviewArea ? promptPreviewArea.value : null;

        btn.disabled = true;
        btn.innerHTML = '<span>⏳</span> Đang gửi tới AI phân tích...';

        try {
            const resp = await fetch('/analysis/quick-analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    text: text,
                    prompt_mode: promptMode,
                    custom_prompt: customPrompt
                })
            });

            const data = await resp.json();
            btn.disabled = false;
            btn.innerHTML = '<span>🚀</span> Phân tích cảm xúc bằng AI';

            if (data.error) {
                showToast(data.error, 'danger');
                return;
            }

            // Update DevToolKit-style Inspector Panels
            renderInspectorUI(data);
            showToast(`Phân tích thành công bằng [${data.engine || 'AI'}]!`, 'success');
        } catch (err) {
            btn.disabled = false;
            btn.innerHTML = '<span>🚀</span> Phân tích cảm xúc bằng AI';
            showToast('Lỗi kết nối máy chủ', 'danger');
        }
    }

    function renderInspectorUI(data) {
        // Sentiment Emoji & Label
        const emojiEl = document.getElementById('inspector-emoji');
        const labelEl = document.getElementById('inspector-label');
        const scoreEl = document.getElementById('inspector-score');
        const pointerEl = document.getElementById('spectrum-pointer');
        const engineBadge = document.getElementById('inspector-engine-badge');

        if (emojiEl) {
            emojiEl.textContent = data.sentiment === 'Tích cực' ? '😊' : data.sentiment === 'Tiêu cực' ? '😡' : '😐';
        }

        if (labelEl) {
            labelEl.textContent = data.sentiment;
            labelEl.style.color = data.sentiment === 'Tích cực' ? 'var(--pos-color)' : data.sentiment === 'Tiêu cực' ? 'var(--neg-color)' : 'var(--neu-color)';
        }

        if (scoreEl) {
            scoreEl.textContent = `Score: ${data.score} · Comparative: ${data.comparative || 0}`;
        }

        if (engineBadge) {
            engineBadge.textContent = data.engine || 'AI Engine';
            engineBadge.className = data.engine && data.engine.includes('Gemini') ? 'badge badge-pos' : 'badge badge-primary';
        }

        // Spectrum Bar Needle Position (0% to 100%)
        if (pointerEl) {
            pointerEl.style.left = `${data.spectrum_pct || 50}%`;
        }

        // 4 Stat Metric Boxes
        const wordsEl = document.getElementById('stat-words-analyzed');
        const matchesEl = document.getElementById('stat-lexicon-matches');
        const posWordsEl = document.getElementById('stat-pos-words');
        const negWordsEl = document.getElementById('stat-neg-words');

        if (wordsEl) wordsEl.textContent = data.words_analyzed || 0;
        if (matchesEl) matchesEl.textContent = `${data.lexicon_matches_count || 0} (${data.lexicon_matches_pct || 0}%)`;

        if (posWordsEl) {
            const posList = data.positive_words || [];
            if (posList.length === 0) {
                posWordsEl.innerHTML = '<span style="color: var(--text-muted); font-size: 0.85rem;">0</span>';
            } else {
                posWordsEl.innerHTML = `<strong>${posList.length}</strong> <div style="margin-top: 0.25rem;">${posList.map(w => `<span class="word-chip word-chip-pos">${w}</span>`).join('')}</div>`;
            }
        }

        if (negWordsEl) {
            const negList = data.negative_words || [];
            if (negList.length === 0) {
                negWordsEl.innerHTML = '<span style="color: var(--text-muted); font-size: 0.85rem;">0</span>';
            } else {
                negWordsEl.innerHTML = `<strong>${negList.length}</strong> <div style="margin-top: 0.25rem;">${negList.map(w => `<span class="word-chip word-chip-neg">${w}</span>`).join('')}</div>`;
            }
        }

        // Additional aspects & AI insights
        const cleanedTextEl = document.getElementById('inspector-cleaned-text');
        const aspectBadgeEl = document.getElementById('inspector-aspect-badge');
        const starEl = document.getElementById('inspector-stars');
        const emotionDetailEl = document.getElementById('inspector-emotion-detail');
        const reasoningEl = document.getElementById('inspector-reasoning');

        if (cleanedTextEl) cleanedTextEl.textContent = data.cleaned_text || data.original_text;
        if (aspectBadgeEl) aspectBadgeEl.textContent = `Khía cạnh: ${data.aspect || 'Chung'}`;
        if (starEl) starEl.textContent = '⭐'.repeat(data.rating_star || 3);
        
        if (emotionDetailEl) {
            emotionDetailEl.textContent = data.emotion_detail || 'Đã phân loại';
        }
        if (reasoningEl) {
            reasoningEl.textContent = data.reasoning || 'Dựa trên ngữ cảnh và từ khóa cảm xúc.';
        }

        const engineFooterEl = document.getElementById('inspector-model-footer');
        if (engineFooterEl && data.engine) {
            engineFooterEl.textContent = `Động cơ: ${data.engine}`;
        }

        // Sentence Breakdown Table
        const sentencesContainer = document.getElementById('sentence-breakdown-list');
        const sentencesCountHeader = document.getElementById('sentence-breakdown-count');

        if (sentencesContainer && data.sentence_breakdown) {
            sentencesContainer.innerHTML = '';
            if (sentencesCountHeader) {
                sentencesCountHeader.textContent = `(${data.sentence_breakdown.length})`;
            }

            data.sentence_breakdown.forEach((s, idx) => {
                const item = document.createElement('div');
                item.className = 'sentence-item';
                
                let badgeStyle = 'color: var(--neu-color);';
                if (s.score > 0) badgeStyle = 'color: var(--pos-color); font-weight: 700;';
                if (s.score < 0) badgeStyle = 'color: var(--neg-color); font-weight: 700;';

                item.innerHTML = `
                    <div style="display: flex; gap: 0.5rem; align-items: center; max-width: 82%;">
                        <span style="color: var(--text-muted); font-weight: 700; font-size: 0.8rem;">${idx + 1}</span>
                        <span>"${s.sentence}"</span>
                    </div>
                    <div style="text-align: right; min-width: 80px;">
                        <span style="${badgeStyle}">${s.score > 0 ? '+' + s.score : s.score}</span>
                        <div style="font-size: 0.75rem; color: var(--text-muted);">${s.sentiment}</div>
                    </div>
                `;
                sentencesContainer.appendChild(item);
            });
        }

        const resultCard = document.getElementById('inspector-result-card');
        if (resultCard) resultCard.style.display = 'block';
    }
}

// 2. Drag & Drop File Upload & Error Diagnosis
function initFileUpload() {
    const dropzone = document.getElementById('upload-dropzone');
    const fileInput = document.getElementById('file-input');
    const modal = document.getElementById('clean-preview-modal');
    const processDirectBtn = document.getElementById('btn-process-direct');

    if (!dropzone || !fileInput) return;

    dropzone.addEventListener('click', () => fileInput.click());

    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            handleFileUpload(fileInput.files[0]);
        }
    });

    async function handleFileUpload(file) {
        const formData = new FormData();
        formData.append('file', file);

        dropzone.innerHTML = `
            <div class="upload-icon">⏳</div>
            <h3>Đang quét & kiểm tra cấu trúc dữ liệu...</h3>
            <p style="color: var(--text-muted);">Tự động phát hiện dòng trống, trùng lặp và ngôn ngữ nhiễu</p>
        `;

        try {
            const resp = await fetch('/analysis/upload', {
                method: 'POST',
                body: formData
            });

            const data = await resp.json();

            if (data.error) {
                showToast(data.error, 'danger');
                resetDropzone();
                return;
            }

            // Populate Preview Modal
            document.getElementById('modal-file-name').textContent = data.file_name;
            document.getElementById('modal-total-rows').textContent = data.total_rows;
            document.getElementById('modal-empty-rows').textContent = data.empty_rows;
            document.getElementById('modal-duplicate-rows').textContent = data.duplicate_rows;
            document.getElementById('modal-clean-rows').textContent = data.clean_rows;

            const previewList = document.getElementById('modal-preview-samples');
            previewList.innerHTML = '';
            data.preview_samples.forEach(sample => {
                const li = document.createElement('li');
                li.style.padding = '0.5rem 0';
                li.style.borderBottom = '1px solid var(--border-light)';
                li.innerHTML = `
                    <div style="font-weight: 600; font-size: 0.88rem;">"${sample.original_text}"</div>
                    <div style="font-size: 0.78rem; color: var(--text-muted);">➜ Chuẩn hóa: <em>${sample.cleaned_text}</em></div>
                `;
                previewList.appendChild(li);
            });

            modal.style.display = 'flex';
            resetDropzone();

        } catch (err) {
            resetDropzone();
            showToast('Lỗi khi tải tệp', 'danger');
        }
    }

    function resetDropzone() {
        dropzone.innerHTML = `
            <div class="upload-icon">📁</div>
            <h3>Kéo thả tệp hoặc bấm vào đây để tải lên</h3>
            <p style="color: var(--text-muted); font-size: 0.88rem; margin-top: 0.35rem;">
                Hỗ trợ định dạng Excel (.xlsx, .xls), CSV, Word (.docx), Văn bản (.txt)
            </p>
        `;
    }

    // Modal Confirmation & Run Analysis
    const confirmBtn = document.getElementById('btn-confirm-process');
    if (confirmBtn) {
        confirmBtn.addEventListener('click', async () => {
            const title = document.getElementById('session-title-input').value.trim() || 'Phiên phân tích ' + new Date().toLocaleDateString('vi-VN');
            const cleanEmpty = document.getElementById('chk-clean-empty').checked;
            const cleanDuplicates = document.getElementById('chk-clean-duplicates').checked;

            confirmBtn.disabled = true;
            confirmBtn.innerHTML = '<span>⚡</span> Đang chạy mô hình AI...';

            try {
                const resp = await fetch('/analysis/process', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        source_type: 'file',
                        title: title,
                        clean_empty: cleanEmpty,
                        clean_duplicates: cleanDuplicates
                    })
                });

                const data = await resp.json();
                if (data.success) {
                    showToast('Phân tích hoàn tất! Đang chuyển trang...', 'success');
                    window.location.href = data.redirect_url;
                } else {
                    confirmBtn.disabled = false;
                    confirmBtn.innerHTML = 'Bắt đầu phân tích ngay';
                    showToast(data.error || 'Có lỗi xảy ra', 'danger');
                }
            } catch (err) {
                confirmBtn.disabled = false;
                confirmBtn.innerHTML = 'Bắt đầu phân tích ngay';
                showToast('Lỗi kết nối khi phân tích', 'danger');
            }
        });
    }

    // Direct multi-line text analyze button
    if (processDirectBtn) {
        processDirectBtn.addEventListener('click', async () => {
            const directText = document.getElementById('direct-text-area').value.trim();
            const directTitle = document.getElementById('direct-title-input').value.trim() || 'Phiên phân tích văn bản';

            if (!directText) {
                showToast('Vui lòng nhập ít nhất một dòng văn bản phản hồi', 'warning');
                return;
            }

            processDirectBtn.disabled = true;
            processDirectBtn.innerHTML = '<span>⚡</span> Đang phân tích...';

            try {
                const resp = await fetch('/analysis/process', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        source_type: 'direct_text',
                        title: directTitle,
                        direct_text: directText
                    })
                });

                const data = await resp.json();
                if (data.success) {
                    window.location.href = data.redirect_url;
                } else {
                    processDirectBtn.disabled = false;
                    processDirectBtn.innerHTML = 'Phân tích danh sách';
                    showToast(data.error || 'Lỗi xử lý', 'danger');
                }
            } catch (err) {
                processDirectBtn.disabled = false;
                processDirectBtn.innerHTML = 'Phân tích danh sách';
                showToast('Lỗi hệ thống', 'danger');
            }
        });
    }

    const closeModalBtn = document.getElementById('btn-close-modal');
    if (closeModalBtn && modal) {
        closeModalBtn.addEventListener('click', () => modal.style.display = 'none');
    }
}

// 3. Dynamic Visual Charts with Type Switcher (Pie / Bar / Line)
let currentSentimentChart = null;
let currentAspectChart = null;
let currentSentimentChartType = 'doughnut'; // default

function initSessionCharts() {
    const canvasSentiment = document.getElementById('sentimentDistributionChart');
    const canvasAspect = document.getElementById('aspectBreakdownChart');

    if (!canvasSentiment) return;

    const pos = parseInt(canvasSentiment.dataset.positive || '0');
    const neg = parseInt(canvasSentiment.dataset.negative || '0');
    const neu = parseInt(canvasSentiment.dataset.neutral || '0');

    renderSentimentChart(canvasSentiment, pos, neg, neu, currentSentimentChartType);

    // Chart Type Switcher Buttons
    const switchBtns = document.querySelectorAll('.chart-switch-btn');
    switchBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            switchBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentSentimentChartType = btn.dataset.chartType; // 'doughnut', 'bar', 'line'
            renderSentimentChart(canvasSentiment, pos, neg, neu, currentSentimentChartType);
        });
    });

    // Aspect Chart
    if (canvasAspect) {
        renderAspectChart(canvasAspect);
    }
}

function renderSentimentChart(canvas, pos, neg, neu, type) {
    if (currentSentimentChart) {
        currentSentimentChart.destroy();
    }

    const isLine = type === 'line';
    const isBar = type === 'bar';

    const config = {
        type: type,
        data: {
            labels: ['Tích cực', 'Tiêu cực', 'Trung tính'],
            datasets: [{
                label: 'Số lượng phản hồi',
                data: [pos, neg, neu],
                backgroundColor: [
                    'rgba(16, 185, 129, 0.85)',
                    'rgba(244, 63, 94, 0.85)',
                    'rgba(245, 158, 11, 0.85)'
                ],
                borderColor: [
                    '#10b981',
                    '#f43f5e',
                    '#f59e0b'
                ],
                borderWidth: isLine ? 3 : 1,
                fill: isLine,
                tension: 0.35
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: getComputedStyle(document.documentElement).getPropertyValue('--text-main').trim(),
                        font: { family: 'Plus Jakarta Sans', weight: '600' }
                    }
                }
            },
            scales: (isBar || isLine) ? {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(150, 150, 150, 0.1)' }
                },
                x: {
                    grid: { display: false }
                }
            } : {}
        }
    };

    currentSentimentChart = new Chart(canvas, config);
}

function renderAspectChart(canvas) {
    if (currentAspectChart) {
        currentAspectChart.destroy();
    }

    let aspectData = {};
    try {
        aspectData = JSON.parse(canvas.dataset.aspectJson || '{}');
    } catch (e) {
        aspectData = {};
    }

    const labels = Object.keys(aspectData);
    const posCounts = labels.map(k => aspectData[k].pos || 0);
    const negCounts = labels.map(k => aspectData[k].neg || 0);
    const neuCounts = labels.map(k => aspectData[k].neu || 0);

    currentAspectChart = new Chart(canvas, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Tích cực',
                    data: posCounts,
                    backgroundColor: 'rgba(16, 185, 129, 0.85)',
                    borderRadius: 6
                },
                {
                    label: 'Tiêu cực',
                    data: negCounts,
                    backgroundColor: 'rgba(244, 63, 94, 0.85)',
                    borderRadius: 6
                },
                {
                    label: 'Trung tính',
                    data: neuCounts,
                    backgroundColor: 'rgba(245, 158, 11, 0.85)',
                    borderRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom' }
            },
            scales: {
                x: { stacked: true },
                y: { stacked: true, beginAtZero: true }
            }
        }
    });
}

// 4. Table Filter & Live Search
function initTableFilters() {
    const searchInput = document.getElementById('table-search-input');
    const filterSentiment = document.getElementById('filter-sentiment-select');
    const filterAspect = document.getElementById('filter-aspect-select');
    const rows = document.querySelectorAll('.feedback-row');

    if (!rows.length) return;

    function applyFilters() {
        const query = (searchInput ? searchInput.value : '').toLowerCase().trim();
        const sent = filterSentiment ? filterSentiment.value : 'all';
        const asp = filterAspect ? filterAspect.value : 'all';

        rows.forEach(row => {
            const text = row.dataset.text.toLowerCase();
            const rowSent = row.dataset.sentiment;
            const rowAsp = row.dataset.aspect;

            const matchQuery = !query || text.includes(query);
            const matchSent = (sent === 'all') || (rowSent === sent);
            const matchAsp = (asp === 'all') || (rowAsp === asp);

            if (matchQuery && matchSent && matchAsp) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }

    if (searchInput) searchInput.addEventListener('input', applyFilters);
    if (filterSentiment) filterSentiment.addEventListener('change', applyFilters);
    if (filterAspect) filterAspect.addEventListener('change', applyFilters);
}
