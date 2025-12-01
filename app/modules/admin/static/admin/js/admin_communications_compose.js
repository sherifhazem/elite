// Compose page logic for selecting audiences and recipients.
document.addEventListener('DOMContentLoaded', () => {
    const audienceField = document.getElementById('audience');
    const composeForm = document.getElementById('composeForm');
    const searchContainer = document.getElementById('manualRecipientTools');
    const searchInput = document.getElementById('recipientSearch');
    const resultsContainer = document.getElementById('recipientResults');
    const selectedContainer = document.getElementById('selectedRecipients');
    const manualSearchLabel = document.getElementById('manualSearchLabel');

    const lookupEndpoint = composeForm?.dataset.lookupEndpoint || '/admin/communications/lookup';

    const selectedRecipients = new Map();

    function audienceRequiresManualSelection(value) {
        return value === 'selected_users' || value === 'selected_companies';
    }

    function currentLookupType(value) {
        return value === 'selected_companies' ? 'company' : 'user';
    }

    function updateManualSelectionVisibility() {
        const value = audienceField.value;
        if (audienceRequiresManualSelection(value)) {
            searchContainer.classList.remove('d-none');
            manualSearchLabel.textContent = value === 'selected_companies' ? 'اختر الشركات' : 'اختر المستخدمين';
            searchInput.value = '';
            resultsContainer.innerHTML = '<span class="text-muted">ابدأ بالكتابة للبحث.</span>';
        } else {
            searchContainer.classList.add('d-none');
            selectedRecipients.clear();
            selectedContainer.innerHTML = '';
            removeHiddenInputs();
        }
    }

    function removeHiddenInputs() {
        document.querySelectorAll('input[name="selected_users"], input[name="selected_companies"]').forEach((input) => input.remove());
    }

    function renderSelectedRecipients() {
        selectedContainer.innerHTML = '';
        selectedRecipients.forEach((item, key) => {
            const badge = document.createElement('span');
            badge.className = 'badge bg-primary d-inline-flex align-items-center gap-2 px-3 py-2';
            badge.innerHTML = `
                <i class="fa-solid fa-user"></i>
                <span>${item.name}</span>
                <button type="button" class="btn btn-sm btn-light ms-2" aria-label="إزالة" data-id="${key}">
                    <i class="fa-solid fa-xmark"></i>
                </button>
            `;
            const removeButton = badge.querySelector('button');
            removeButton.addEventListener('click', () => {
                selectedRecipients.delete(key);
                removeHiddenInputs();
                renderSelectedRecipients();
            });
            selectedContainer.appendChild(badge);
        });
    }

    function addHiddenInput(value) {
        if (!value) {
            return;
        }
        const input = document.createElement('input');
        const lookupType = currentLookupType(audienceField.value);
        input.type = 'hidden';
        input.name = lookupType === 'company' ? 'selected_companies' : 'selected_users';
        input.value = value;
        composeForm?.appendChild(input);
    }

    function renderResults(results) {
        if (!Array.isArray(results) || !results.length) {
            resultsContainer.innerHTML = '<span class="text-muted">لا توجد نتائج.</span>';
            return;
        }

        resultsContainer.innerHTML = '';
        results.forEach((item) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'btn btn-outline-primary d-flex align-items-center justify-content-between w-100';
            button.innerHTML = `
                <span>${item.name}</span>
                <i class="fa-solid fa-plus"></i>
            `;
            button.addEventListener('click', () => {
                if (!selectedRecipients.has(item.id)) {
                    selectedRecipients.set(item.id, item);
                    addHiddenInput(item.id);
                    renderSelectedRecipients();
                }
            });
            resultsContainer.appendChild(button);
        });
    }

    function searchRecipients(query) {
        const value = (query || '').trim();
        if (!value) {
            resultsContainer.innerHTML = '<span class="text-muted">ابدأ بالكتابة للبحث.</span>';
            return;
        }

        const type = currentLookupType(audienceField.value);
        fetch(`${lookupEndpoint}?type=${type}&q=${encodeURIComponent(value)}`)
            .then((response) => response.json())
            .then((data) => renderResults(data.results || []))
            .catch(() => {
                resultsContainer.innerHTML = '<span class="text-danger">تعذر جلب النتائج.</span>';
            });
    }

    audienceField?.addEventListener('change', updateManualSelectionVisibility);

    searchInput?.addEventListener('input', (event) => {
        searchRecipients(event.target.value);
    });

    updateManualSelectionVisibility();
});
