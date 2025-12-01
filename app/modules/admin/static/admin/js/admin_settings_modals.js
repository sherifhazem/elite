// Modal wiring for admin settings lists.
document.addEventListener('DOMContentLoaded', () => {
    const addListModal = document.getElementById('addListModal');
    const editListModal = document.getElementById('editListModal');

    const modalConfig = {
        cities: {
            addAction: addListModal?.dataset?.addCityAction,
            editAction: (id) => (editListModal?.dataset?.updateCityAction || '').replace('__ID__', id),
        },
        industries: {
            addAction: addListModal?.dataset?.addIndustryAction,
            editAction: (id) => (editListModal?.dataset?.updateIndustryAction || '').replace('__ID__', id),
        },
    };

    addListModal?.addEventListener('show.bs.modal', (event) => {
        const trigger = event.relatedTarget;
        if (!trigger) {
            return;
        }
        const listType = trigger.getAttribute('data-list-type');
        const modalTitle = trigger.getAttribute('data-modal-title');
        const submitLabel = trigger.getAttribute('data-submit-label');

        const form = document.getElementById('addListForm');
        if (!form) {
            return;
        }
        form.reset();
        form.action = modalConfig[listType]?.addAction || '#';
        const addItemActive = document.getElementById('addItemActive');
        if (addItemActive) {
            addItemActive.checked = true;
        }
        const modalLabel = document.getElementById('addListModalLabel');
        if (modalLabel) {
            modalLabel.textContent = modalTitle || 'إضافة عنصر';
        }
        const addListSubmit = document.getElementById('addListSubmit');
        if (addListSubmit) {
            addListSubmit.textContent = submitLabel || 'حفظ';
        }
    });

    editListModal?.addEventListener('show.bs.modal', (event) => {
        const trigger = event.relatedTarget;
        if (!trigger) {
            return;
        }
        const listType = trigger.getAttribute('data-list-type');
        const itemId = trigger.getAttribute('data-item-id');
        const itemName = trigger.getAttribute('data-item-name');
        const itemActive = trigger.getAttribute('data-item-active');
        const modalTitle = trigger.getAttribute('data-modal-title');
        const submitLabel = trigger.getAttribute('data-submit-label');

        const form = document.getElementById('editListForm');
        if (!form) {
            return;
        }
        form.action = modalConfig[listType]?.editAction(itemId) || '#';
        const editItemName = document.getElementById('editItemName');
        if (editItemName) {
            editItemName.value = itemName || '';
        }
        const activeCheckbox = document.getElementById('editItemActive');
        if (activeCheckbox) {
            activeCheckbox.checked = itemActive === '1';
        }
        const modalLabel = document.getElementById('editListModalLabel');
        if (modalLabel) {
            modalLabel.textContent = modalTitle || 'تعديل عنصر';
        }
        const editListSubmit = document.getElementById('editListSubmit');
        if (editListSubmit) {
            editListSubmit.textContent = submitLabel || 'حفظ';
        }
    });
});
