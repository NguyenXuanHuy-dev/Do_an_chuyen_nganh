// Chat Agent Frontend Logic

document.addEventListener('DOMContentLoaded', () => {
    const chatContainer = document.querySelector('.chat-container');
    if (!chatContainer) return;

    const sessionId = chatContainer.dataset.sessionId;
    const messagesArea = document.getElementById('chat-messages-area');
    const inputField = document.getElementById('chat-input-text');
    const sendBtn = document.getElementById('chat-send-btn');
    const promptChips = document.querySelectorAll('.prompt-chip');

    // Scroll chat to bottom
    scrollToBottom();

    // Send button event
    sendBtn.addEventListener('click', () => sendMessage());

    inputField.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Quick prompt chip click
    promptChips.forEach(chip => {
        chip.addEventListener('click', () => {
            const promptText = chip.dataset.promptText || chip.textContent.trim();
            inputField.value = promptText;
            sendMessage(chip.textContent.trim());
        });
    });

    async function sendMessage(templateTitle = '') {
        const text = inputField.value.trim();
        if (!text) return;

        // Render user message immediately
        appendMessage('user', text);
        inputField.value = '';
        scrollToBottom();

        // Show typing indicator
        const typingEl = appendTypingIndicator();
        scrollToBottom();

        try {
            const resp = await fetch('/chat/api/message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    message: text,
                    prompt_template: templateTitle
                })
            });

            const data = await resp.json();
            typingEl.remove();

            if (data.success && data.ai_message) {
                appendMessage('assistant', data.ai_message.content, data.ai_message.id);
                scrollToBottom();
            } else {
                appendMessage('assistant', '⚠️ Xin lỗi, đã có lỗi khi tạo phản hồi. Vui lòng thử lại.');
                scrollToBottom();
            }
        } catch (err) {
            typingEl.remove();
            appendMessage('assistant', '⚠️ Lỗi kết nối máy chủ.');
            scrollToBottom();
        }
    }

    function appendMessage(role, content, messageId = null) {
        const bubble = document.createElement('div');
        bubble.className = `chat-bubble ${role}`;

        // Convert simple markdown to HTML (headings, bold, lists)
        let htmlContent = formatMarkdown(content);

        bubble.innerHTML = `
            <div class="message-content">${htmlContent}</div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.5rem; font-size: 0.75rem; opacity: 0.8;">
                <span>${role === 'user' ? 'Bạn' : '🤖 AI Phân Tích'}</span>
                ${role === 'assistant' && messageId ? `
                    <div class="rating-actions" style="display: flex; gap: 0.35rem;">
                        <button class="btn-rate" data-id="${messageId}" data-rate="like" title="Hữu ích" style="background: none; border: none; cursor: pointer;">👍</button>
                        <button class="btn-rate" data-id="${messageId}" data-rate="dislike" title="Chưa chính xác" style="background: none; border: none; cursor: pointer;">👎</button>
                    </div>
                ` : ''}
            </div>
        `;

        messagesArea.appendChild(bubble);

        // Bind rating clicks
        if (role === 'assistant' && messageId) {
            const rateBtns = bubble.querySelectorAll('.btn-rate');
            rateBtns.forEach(btn => {
                btn.addEventListener('click', () => {
                    rateResponse(btn.dataset.id, btn.dataset.rate);
                    rateBtns.forEach(b => b.disabled = true);
                    btn.style.transform = 'scale(1.2)';
                });
            });
        }

        return bubble;
    }

    function appendTypingIndicator() {
        const typing = document.createElement('div');
        typing.className = 'chat-bubble assistant typing-indicator';
        typing.innerHTML = `
            <span style="display: inline-flex; gap: 4px; align-items: center;">
                <span class="dot">●</span><span class="dot">●</span><span class="dot">●</span> Đang truy xuất và tổng hợp dữ liệu...
            </span>
        `;
        messagesArea.appendChild(typing);
        return typing;
    }

    function scrollToBottom() {
        if (messagesArea) {
            messagesArea.scrollTop = messagesArea.scrollHeight;
        }
    }

    async function rateResponse(messageId, rating) {
        try {
            await fetch('/chat/api/rate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    message_id: messageId,
                    rating: rating
                })
            });
            showToast(rating === 'like' ? 'Cảm ơn đánh giá tích cực của bạn!' : 'Đã ghi nhận phản hồi để tinh chỉnh mô hình.', 'info');
        } catch (e) {
            console.error(e);
        }
    }

    function formatMarkdown(text) {
        if (!text) return '';
        let html = text
            .replace(/### (.*?)\n/g, '<h4 style="margin: 0.5rem 0; font-weight: 700;">$1</h4>')
            .replace(/## (.*?)\n/g, '<h3 style="margin: 0.6rem 0; font-weight: 800;">$1</h3>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`([^`]+)`/g, '<code style="background: rgba(120, 120, 120, 0.15); padding: 0.15rem 0.4rem; border-radius: 4px; font-family: monospace;">$1</code>')
            .replace(/\n- (.*?)/g, '<br>• $1')
            .replace(/\n\n/g, '<br><br>');
        return html;
    }
});
