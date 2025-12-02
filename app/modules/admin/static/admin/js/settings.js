// Admin settings management backed by the centralized registry.
(function () {
    const root = document.getElementById('admin-settings-root');
    const contextScript = document.getElementById('admin-settings-context');
    if (!root || !contextScript) {
        return;
    }

    let context = {};
    try {
        context = JSON.parse(contextScript.textContent || '{}');
    } catch (error) {
        console.error('Failed to parse admin settings context', error);
    }

    const registry = {
        cities: Array.isArray(context.cities) ? [...context.cities] : [],
        industries: Array.isArray(context.industries) ? [...context.industries] : [],
    };
    const endpoints = context.endpoints || {};

    const toastElement = document.getElementById('adminToast');
    const toastBody = toastElement?.querySelector('.toast-body');
    const toastInstance = toastElement ? bootstrap.Toast.getOrCreateInstance(toastElement) : null;

    const editModalElement = document.getElementById('editItemModal');
    const editForm = document.getElementById('editItemForm');
    const editItemName = document.getElementById('editItemName');
    const editCurrentValue = document.getElementById('editCurrentValue');
    const editModal = editModalElement ? bootstrap.Modal.getOrCreateInstance(editModalElement) : null;

    const entityKey = (listType) => (listType === 'industries' ? 'industry' : 'city');
    const endpointFor = (action, listType) => endpoints[`${action}_${entityKey(listType)}`];

    function showToast(message, isError = false) {
        if (!toastElement || !toastBody || !toastInstance) return;
        toastElement.classList.remove('text-bg-success', 'text-bg-danger');
        toastElement.classList.add(isError ? 'text-bg-danger' : 'text-bg-success');
        toastBody.textContent = message || (isError ? 'حدث خطأ أثناء حفظ التغييرات.' : 'تم حفظ التغييرات بنجاح.');
        toastInstance.show();
    }

    function setFeedback(listType, message) {
        const feedback = root.querySelector(`[data-feedback="${listType}"]`);
        if (!feedback) return;
        if (message) {
            feedback.textContent = message;
            feedback.classList.remove('d-none');
        } else {
            feedback.textContent = '';
            feedback.classList.add('d-none');
        }
    }

    function buildRow(listType, value) {
        const row = document.createElement('tr');
        row.dataset.value = value;

        const nameCell = document.createElement('td');
        nameCell.className = 'fw-medium';
        nameCell.textContent = value;

        const actionsCell = document.createElement('td');
        actionsCell.className = 'text-end';
        const group = document.createElement('div');
        group.className = 'btn-group';
        group.setAttribute('role', 'group');

        const editButton = document.createElement('button');
        editButton.type = 'button';
        editButton.className = 'btn btn-sm btn-outline-primary js-edit-item';
        editButton.dataset.listType = listType;
        editButton.dataset.currentValue = value;
        editButton.setAttribute('data-bs-toggle', 'modal');
        editButton.setAttribute('data-bs-target', '#editItemModal');
        editButton.textContent = '✏️ تعديل';

        const deleteButton = document.createElement('button');
        deleteButton.type = 'button';
        deleteButton.className = 'btn btn-sm btn-outline-danger js-delete-item';
        deleteButton.dataset.listType = listType;
        deleteButton.dataset.value = value;
        deleteButton.textContent = '🗑 حذف';

        group.appendChild(editButton);
        group.appendChild(deleteButton);
        actionsCell.appendChild(group);

        row.appendChild(nameCell);
        row.appendChild(actionsCell);
        return row;
    }

    function renderList(listType) {
        const tbody = root.querySelector(`[data-list-table="${listType}"]`);
        if (!tbody) return;
        tbody.innerHTML = '';

        const values = registry[listType] || [];
        if (!values.length) {
            const emptyRow = document.createElement('tr');
            emptyRow.className = 'js-empty-row';
            emptyRow.dataset.listType = listType;
            const emptyCell = document.createElement('td');
            emptyCell.colSpan = 2;
            emptyCell.className = 'text-center text-muted py-4';
            emptyCell.textContent = listType === 'cities' ? 'لا توجد مدن مسجلة.' : 'لا توجد مجالات عمل مسجلة.';
            emptyRow.appendChild(emptyCell);
            tbody.appendChild(emptyRow);
            return;
        }

        values.forEach((value) => {
            tbody.appendChild(buildRow(listType, value));
        });
    }

    function handleSuccess(listType, data) {
        if (!data || data.status !== 'success' || !Array.isArray(data.items)) {
            setFeedback(listType, data?.message || 'تعذر تحديث القائمة.');
            showToast(data?.message || 'تعذر تحديث القائمة.', true);
            return;
        }
        registry[listType] = data.items;
        renderList(listType);
        setFeedback(listType, null);
        showToast(data.message || 'تم الحفظ بنجاح.');
    }

    async function postJSON(url, payload) {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Accept: 'application/json',
            },
            body: JSON.stringify(payload),
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            const error = new Error(data?.message || 'Unexpected error');
            error.response = data;
            throw error;
        }
        return data;
    }

    function bindAddForms() {
        const forms = root.querySelectorAll('.js-add-form');
        forms.forEach((form) => {
            form.addEventListener('submit', async (event) => {
                event.preventDefault();
                const listType = form.dataset.listType;
                const input = form.querySelector('input[name="name"]');
                const value = (input?.value || '').trim();
                if (!listType || !value) {
                    setFeedback(listType, 'الاسم مطلوب.');
                    return;
                }

                try {
                    const url = endpointFor('add', listType);
                    const data = await postJSON(url, { name: value });
                    handleSuccess(listType, data);
                    if (input) {
                        input.value = '';
                        input.focus();
                    }
                } catch (error) {
                    const message = error.response?.message || 'تعذر إضافة العنصر.';
                    setFeedback(listType, message);
                    showToast(message, true);
                }
            });
        });
    }

    function bindDeleteActions() {
        root.addEventListener('click', async (event) => {
            const trigger = event.target.closest('.js-delete-item');
            if (!trigger) return;

            const listType = trigger.dataset.listType;
            const value = trigger.dataset.value || '';
            if (!listType || !value) {
                return;
            }

            const confirmed = window.confirm('هل أنت متأكد من الحذف؟');
            if (!confirmed) {
                return;
            }

            try {
                const url = endpointFor('delete', listType);
                const data = await postJSON(url, { value });
                handleSuccess(listType, data);
            } catch (error) {
                const message = error.response?.message || 'تعذر حذف العنصر.';
                setFeedback(listType, message);
                showToast(message, true);
            }
        });
    }

    function bindEditModal() {
        root.addEventListener('click', (event) => {
            const trigger = event.target.closest('.js-edit-item');
            if (!trigger || !editForm) return;

            const listType = trigger.dataset.listType;
            const currentValue = trigger.dataset.currentValue || '';
            editForm.dataset.listType = listType;
            editForm.action = endpointFor('update', listType) || '#';
            editItemName.value = currentValue;
            editCurrentValue.value = currentValue;
        });

        editForm?.addEventListener('submit', async (event) => {
            event.preventDefault();
            const listType = editForm.dataset.listType;
            const newName = (editItemName.value || '').trim();
            const currentValue = editCurrentValue.value || '';
            if (!listType || !newName || !currentValue) {
                setFeedback(listType, 'الاسم مطلوب.');
                return;
            }

            try {
                const url = endpointFor('update', listType);
                const data = await postJSON(url, {
                    current_value: currentValue,
                    name: newName,
                });
                handleSuccess(listType, data);
                if (editModal) {
                    editModal.hide();
                }
            } catch (error) {
                const message = error.response?.message || 'تعذر تحديث العنصر.';
                setFeedback(listType, message);
                showToast(message, true);
            }
        });
    }

    function bootstrapPage() {
        renderList('cities');
        renderList('industries');
        bindAddForms();
        bindDeleteActions();
        bindEditModal();
    }

    bootstrapPage();
})();
