// Admin Dashboard and Management Scripts

document.addEventListener('DOMContentLoaded', () => {
    initAdminCharts();
    initUserControls();
    initPromptModals();
});

function initAdminCharts() {
    const adminChartCanvas = document.getElementById('adminOverviewChart');
    if (!adminChartCanvas) return;

    const pos = parseInt(adminChartCanvas.dataset.pos || '0');
    const neg = parseInt(adminChartCanvas.dataset.neg || '0');
    const neu = parseInt(adminChartCanvas.dataset.neu || '0');

    new Chart(adminChartCanvas, {
        type: 'doughnut',
        data: {
            labels: ['Tích cực', 'Tiêu cực', 'Trung tính'],
            datasets: [{
                data: [pos, neg, neu],
                backgroundColor: [
                    'rgba(16, 185, 129, 0.85)',
                    'rgba(244, 63, 94, 0.85)',
                    'rgba(245, 158, 11, 0.85)'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
}

function initUserControls() {
    const toggleBtns = document.querySelectorAll('.btn-toggle-user');
    toggleBtns.forEach(btn => {
        btn.addEventListener('click', async () => {
            const userId = btn.dataset.userId;
            try {
                const resp = await fetch(`/admin/users/${userId}/toggle-status`, {
                    method: 'POST'
                });
                const data = await resp.json();
                if (data.success) {
                    showToast(data.message, 'success');
                    setTimeout(() => location.reload(), 800);
                } else {
                    showToast(data.error, 'danger');
                }
            } catch (e) {
                showToast('Lỗi cập nhật', 'danger');
            }
        });
    });

    const roleSelects = document.querySelectorAll('.select-user-role');
    roleSelects.forEach(sel => {
        sel.addEventListener('change', async () => {
            const userId = sel.dataset.userId;
            const role = sel.value;
            try {
                const resp = await fetch(`/admin/users/${userId}/change-role`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ role })
                });
                const data = await resp.json();
                if (data.success) {
                    showToast(data.message, 'success');
                } else {
                    showToast(data.error, 'danger');
                }
            } catch (e) {
                showToast('Lỗi thay đổi quyền', 'danger');
            }
        });
    });
}

function initPromptModals() {
    const modal = document.getElementById('prompt-modal');
    const addBtn = document.getElementById('btn-add-prompt');
    const saveBtn = document.getElementById('btn-save-prompt');
    const closeBtn = document.getElementById('btn-close-prompt-modal');
    const deleteBtns = document.querySelectorAll('.btn-delete-prompt');

    if (!modal) return;

    if (addBtn) {
        addBtn.addEventListener('click', () => {
            document.getElementById('prompt-id').value = '';
            document.getElementById('prompt-title').value = '';
            document.getElementById('prompt-text').value = '';
            document.getElementById('prompt-desc').value = '';
            modal.style.display = 'flex';
        });
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', () => modal.style.display = 'none');
    }

    if (saveBtn) {
        saveBtn.addEventListener('click', async () => {
            const id = document.getElementById('prompt-id').value;
            const title = document.getElementById('prompt-title').value.trim();
            const text = document.getElementById('prompt-text').value.trim();
            const desc = document.getElementById('prompt-desc').value.trim();

            if (!title || !text) {
                showToast('Vui lòng điền tiêu đề và nội dung prompt', 'warning');
                return;
            }

            try {
                const resp = await fetch('/admin/prompts/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id, title, prompt_text: text, description: desc })
                });
                const data = await resp.json();
                if (data.success) {
                    showToast(data.message, 'success');
                    modal.style.display = 'none';
                    setTimeout(() => location.reload(), 800);
                } else {
                    showToast(data.error, 'danger');
                }
            } catch (e) {
                showToast('Lỗi lưu prompt', 'danger');
            }
        });
    }

    deleteBtns.forEach(btn => {
        btn.addEventListener('click', async () => {
            if (!confirm('Bạn có chắc chắn muốn xóa Prompt mẫu này?')) return;
            const id = btn.dataset.promptId;
            try {
                const resp = await fetch(`/admin/prompts/${id}/delete`, { method: 'POST' });
                const data = await resp.json();
                if (data.success) {
                    showToast(data.message, 'success');
                    setTimeout(() => location.reload(), 800);
                } else {
                    showToast(data.error, 'danger');
                }
            } catch (e) {
                showToast('Lỗi xóa', 'danger');
            }
        });
    });
}
