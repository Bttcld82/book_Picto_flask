/**
 * AAC Builder Flask - Minimal JavaScript
 * Manteniamo il JavaScript al minimo, solo per UX essenziali
 */

// Auto-hide flash messages dopo 5 secondi
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash');
    flashMessages.forEach(function(flash) {
        setTimeout(function() {
            flash.style.opacity = '0';
            flash.style.transform = 'translateX(100%)';
            setTimeout(function() {
                flash.remove();
            }, 300);
        }, 5000);
    });
});

// Conferma eliminazioni
function confirmDelete(message) {
    return confirm(message || 'Sei sicuro di voler procedere con l\'eliminazione?');
}

// Auto-save form data in localStorage (per draft)
function enableAutoSave(formId) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    const inputs = form.querySelectorAll('input[type="text"], textarea, select');
    
    // Carica dati salvati
    inputs.forEach(function(input) {
        const savedValue = localStorage.getItem(`autosave_${formId}_${input.name}`);
        if (savedValue && !input.value) {
            input.value = savedValue;
        }
    });
    
    // Salva modifiche
    inputs.forEach(function(input) {
        input.addEventListener('input', function() {
            localStorage.setItem(`autosave_${formId}_${input.name}`, input.value);
        });
    });
    
    // Pulisci dopo submit
    form.addEventListener('submit', function() {
        inputs.forEach(function(input) {
            localStorage.removeItem(`autosave_${formId}_${input.name}`);
        });
    });
}

// Preview immagini prima dell'upload
function previewImage(input, previewId) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const preview = document.getElementById(previewId);
            if (preview) {
                preview.src = e.target.result;
                preview.style.display = 'block';
            }
        };
        reader.readAsDataURL(input.files[0]);
    }
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl+N per nuovo libro
    if (e.ctrlKey && e.key === 'n') {
        e.preventDefault();
        const newBookLink = document.querySelector('a[href*="new"]');
        if (newBookLink) {
            newBookLink.click();
        }
    }
    
    // Ctrl+/ per focus su ricerca
    if (e.ctrlKey && e.key === '/') {
        e.preventDefault();
        const searchInput = document.querySelector('.search-input');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // ESC per chiudere flash messages
    if (e.key === 'Escape') {
        const flashMessages = document.querySelectorAll('.flash');
        flashMessages.forEach(function(flash) {
            flash.remove();
        });
    }
});

// Loading states per form submission
function addLoadingState() {
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function() {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '⏳ Attendere...';
                setTimeout(function() {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = submitBtn.dataset.originalText || submitBtn.innerHTML.replace('⏳ Attendere...', '');
                }, 3000);
            }
        });
    });
}

// Inizializza tutto quando il DOM è pronto
document.addEventListener('DOMContentLoaded', function() {
    addLoadingState();
    
    // Auto-save per form lunghi
    enableAutoSave('book-form');
    
    // Focus automatico sui campi principali
    const titleInput = document.getElementById('title');
    if (titleInput) {
        titleInput.focus();
    }
    
    // Smooth scroll per anchor links
    document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
});

// Utility: mostra notifica temporanea
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `flash flash-${type}`;
    notification.innerHTML = `
        ${message}
        <button class="flash-close" onclick="this.parentElement.remove()">×</button>
    `;
    
    let container = document.querySelector('.flash-messages');
    if (!container) {
        container = document.createElement('div');
        container.className = 'flash-messages';
        document.body.appendChild(container);
    }
    
    container.appendChild(notification);
    
    // Auto-remove dopo 5 secondi
    setTimeout(function() {
        notification.remove();
    }, 5000);
}

// Export per uso globale
window.confirmDelete = confirmDelete;
window.previewImage = previewImage;
window.showNotification = showNotification;