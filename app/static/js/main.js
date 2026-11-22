/**
 * MediaGuard - Client-Side Interactivity & Form Utilities
 * CS-353 Information Security · NUST SEECS
 * Strict relative API calls (zero hardcoded localhost).
 */

document.addEventListener('DOMContentLoaded', () => {
  initAlertDismissal();
  initFileInputs();
  initDropzones();
  initCopyButtons();
});

/**
 * Initializes close buttons and auto-dismissal for flash alerts.
 */
function initAlertDismissal() {
  document.querySelectorAll('.alert').forEach(alert => {
    // Wire close button
    const closeBtn = alert.querySelector('.alert-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        dismissAlert(alert);
      });
    }

    // Auto dismiss after 6 seconds for success/info alerts
    if (alert.classList.contains('alert-success') || alert.classList.contains('alert-info')) {
      setTimeout(() => {
        dismissAlert(alert);
      }, 6000);
    }
  });
}

function dismissAlert(alertElement) {
  if (!alertElement) return;
  alertElement.style.opacity = '0';
  alertElement.style.transform = 'translateY(-6px)';
  setTimeout(() => {
    alertElement.remove();
  }, 250);
}

/**
 * Validates file sizes client-side (Max 50MB) and provides instant UI feedback.
 */
function initFileInputs() {
  const MAX_FILE_BYTES = 50 * 1024 * 1024; // 50MB cap

  document.querySelectorAll('input[type="file"]').forEach(input => {
    input.addEventListener('change', () => {
      const file = input.files[0];
      const feedback = input.closest('.form-group')?.querySelector('.form-hint') 
                    || input.parentElement?.querySelector('.file-feedback');

      if (!file) return;

      const sizeFormatted = formatBytes(file.size);

      if (file.size > MAX_FILE_BYTES) {
        if (feedback) {
          feedback.textContent = `Error: File size (${sizeFormatted}) exceeds the 50MB security threshold.`;
          feedback.classList.add('text-danger');
          feedback.classList.remove('text-dim', 'text-success');
        }
        input.value = ''; // Reset invalid file
      } else {
        if (feedback) {
          feedback.textContent = `Selected: ${file.name} (${sizeFormatted})`;
          feedback.classList.add('text-success');
          feedback.classList.remove('text-danger', 'text-dim');
        }
      }
    });
  });
}

/**
 * Enhances drag-and-drop zones with visual feedback and file binding.
 */
function initDropzones() {
  document.querySelectorAll('.dropzone').forEach(dropzone => {
    const fileInput = dropzone.querySelector('input[type="file"]') 
                   || document.getElementById(dropzone.getAttribute('data-target-input'));

    ['dragenter', 'dragover'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add('dragover');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove('dragover');
      });
    });

    dropzone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      const files = dt.files;
      if (files.length && fileInput) {
        fileInput.files = files;
        // Trigger change event for validation
        fileInput.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });

    // Clicking dropzone triggers the underlying hidden file input
    dropzone.addEventListener('click', (e) => {
      if (e.target !== fileInput && fileInput) {
        fileInput.click();
      }
    });
  });
}

/**
 * Enables one-click clipboard copying for cryptographic hashes and TOTP keys.
 */
function initCopyButtons() {
  document.querySelectorAll('[data-copy-target]').forEach(button => {
    button.addEventListener('click', async () => {
      const targetId = button.getAttribute('data-copy-target');
      const targetEl = document.getElementById(targetId);
      if (!targetEl) return;

      const text = targetEl.textContent.trim() || targetEl.value;
      try {
        await navigator.clipboard.writeText(text);
        const originalText = button.textContent;
        button.textContent = 'Copied!';
        button.classList.add('btn-primary');
        setTimeout(() => {
          button.textContent = originalText;
          button.classList.remove('btn-primary');
        }, 2000);
      } catch (err) {
        console.error('Failed to copy to clipboard:', err);
      }
    });
  });
}

/**
 * Helper to format bytes into readable KB/MB notation.
 */
function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}
