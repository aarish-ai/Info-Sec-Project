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
  initTotpInputs();
});

/**
 * Initializes close buttons and auto-dismissal for flash alerts.
 * Uses CSS keyframe class toggling (.alert-dismissing) instead of inline styles.
 */
function initAlertDismissal() {
  document.querySelectorAll('.alert').forEach(alert => {
    // Avoid duplicate event listener bindings
    if (alert._alertDismissInitialized) return;
    alert._alertDismissInitialized = true;

    // Wire close button
    const closeBtn = alert.querySelector('.alert-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', (e) => {
        e.preventDefault();
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

/**
 * Dismisses an alert element via CSS keyframe animation class.
 */
function dismissAlert(alertElement) {
  if (!alertElement || alertElement.classList.contains('alert-dismissing')) return;
  alertElement.classList.add('alert-dismissing');

  alertElement.addEventListener('animationend', () => {
    alertElement.remove();
  }, { once: true });

  // Graceful fallback if animations are disabled or interrupted
  setTimeout(() => {
    if (alertElement.parentNode) {
      alertElement.remove();
    }
  }, 400);
}

/**
 * Validates file sizes client-side (Max 50MB) and provides instant telemetry UI feedback.
 */
function initFileInputs() {
  const MAX_FILE_BYTES = 50 * 1024 * 1024; // 50MB cap

  document.querySelectorAll('input[type="file"]').forEach(input => {
    if (input._fileInputInitialized) return;
    input._fileInputInitialized = true;

    input.addEventListener('change', () => {
      const file = input.files && input.files.length ? input.files[0] : null;
      const feedback = input.closest('.dropzone')?.querySelector('.file-feedback')
                    || input.closest('.form-group')?.querySelector('.file-feedback, .form-hint') 
                    || input.parentElement?.querySelector('.file-feedback');

      if (!file) return;

      const sizeFormatted = formatBytes(file.size);

      if (file.size > MAX_FILE_BYTES) {
        if (feedback) {
          feedback.textContent = `REJECTED: File size (${sizeFormatted}) exceeds the 50MB security threshold.`;
          feedback.classList.add('text-danger');
          feedback.classList.remove('text-dim', 'text-success');
        }
        input.value = ''; // Reset invalid file
      } else {
        if (feedback) {
          feedback.textContent = `INGESTED: ${file.name} (${sizeFormatted})`;
          feedback.classList.add('text-success');
          feedback.classList.remove('text-danger', 'text-dim');
        }
      }
    });
  });
}

/**
 * Enhances drag-and-drop zones with active laser sweep and immediate tactical telemetry readout.
 */
function initDropzones() {
  const MAX_FILE_BYTES = 50 * 1024 * 1024; // 50MB security threshold

  document.querySelectorAll('.dropzone').forEach(dropzone => {
    if (dropzone._dropzoneInitialized) return;
    dropzone._dropzoneInitialized = true;

    const fileInput = dropzone.querySelector('input[type="file"]') 
                   || document.getElementById(dropzone.getAttribute('data-target-input'));

    ['dragenter', 'dragover'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add('dragover');
        dropzone.classList.add('laser-active');
      });
    });

    ['dragleave'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (!dropzone.contains(e.relatedTarget)) {
          dropzone.classList.remove('dragover');
          dropzone.classList.remove('laser-active');
        }
      });
    });

    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('dragover');
      dropzone.classList.remove('laser-active');

      const dt = e.dataTransfer;
      const files = dt ? dt.files : null;
      if (!files || !files.length) return;

      const file = files[0];
      const sizeFormatted = formatBytes(file.size);
      const ext = file.name.includes('.') ? file.name.slice(file.name.lastIndexOf('.') + 1).toLowerCase() : '';

      // Bind dropped files to associated file input
      if (fileInput) {
        try {
          fileInput.files = files;
        } catch (err) {
          console.warn('Unable to directly assign files to fileInput:', err);
        }
      }

      // Locate feedback display aperture
      let feedback = dropzone.querySelector('.file-feedback')
                  || dropzone.closest('.form-group')?.querySelector('.file-feedback, .form-hint')
                  || dropzone.parentElement?.querySelector('.file-feedback');

      if (!feedback) {
        feedback = document.createElement('div');
        feedback.className = 'file-feedback font-mono text-xs mt-xs';
        dropzone.appendChild(feedback);
      }

      // Check file size threshold
      if (file.size > MAX_FILE_BYTES) {
        feedback.textContent = `REJECTED: File size (${sizeFormatted}) exceeds 50MB security threshold.`;
        feedback.classList.add('text-danger');
        feedback.classList.remove('text-success', 'text-dim');
        if (fileInput) fileInput.value = '';
      } else {
        // Immediate tactical telemetry readout
        feedback.textContent = `INGESTED: ${file.name} (${sizeFormatted})`;
        feedback.classList.add('text-success');
        feedback.classList.remove('text-danger', 'text-dim');

        // Dispatch change event to trigger validation pipeline
        if (fileInput) {
          fileInput.dispatchEvent(new Event('change', { bubbles: true }));
        }
      }
    });

    // Clicking dropzone triggers the underlying hidden file input
    dropzone.addEventListener('click', (e) => {
      if (fileInput && e.target !== fileInput) {
        fileInput.click();
      }
    });
  });
}

/**
 * Copies text to system clipboard with fallback support for all browser environments.
 */
async function copyTextToClipboard(text) {
  if (!text) return false;
  if (navigator.clipboard && window.isSecureContext) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (err) {
      // Fall through to textarea fallback
    }
  }

  try {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-9999px';
    textArea.style.top = '0';
    textArea.setAttribute('readonly', '');
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    const successful = document.execCommand('copy');
    document.body.removeChild(textArea);
    return successful;
  } catch (err) {
    console.error('Failed to copy to clipboard:', err);
    return false;
  }
}

/**
 * Applies tactile white-hot flash and temporary text update [COPIED // 256-BIT] for 1.8s.
 */
function applyCopiedFeedback(element) {
  if (!element) return;

  if (element._copyResetTimer) {
    clearTimeout(element._copyResetTimer);
  } else {
    element._originalHtml = element.innerHTML;
  }

  element.textContent = '[COPIED // 256-BIT]';
  element.classList.add('copied-flash');

  element._copyResetTimer = setTimeout(() => {
    if (element._originalHtml !== undefined) {
      element.innerHTML = element._originalHtml;
      delete element._originalHtml;
    }
    element.classList.remove('copied-flash');
    delete element._copyResetTimer;
  }, 1800);
}

/**
 * Enables one-click clipboard copying for cryptographic hashes, digest badges, and TOTP keys.
 * Triggers white-hot flash (.copied-flash) and [COPIED // 256-BIT] readout for 1.8s.
 */
function initCopyButtons() {
  const copySelector = '[data-copy-target], .btn-copy-digest, .hash-badge, [data-copy-trigger], .btn-copy';

  document.querySelectorAll(copySelector).forEach(trigger => {
    if (trigger._copyHandlerAttached) return;
    trigger._copyHandlerAttached = true;

    trigger.addEventListener('click', async (e) => {
      const targetId = trigger.getAttribute('data-copy-target');
      const targetEl = targetId ? document.getElementById(targetId) : null;
      let textToCopy = '';

      if (targetEl) {
        textToCopy = (targetEl.getAttribute('title') && targetEl.getAttribute('title').trim())
                  || targetEl.dataset.copyValue
                  || targetEl.value
                  || targetEl.textContent.trim();
      } else {
        textToCopy = (trigger.getAttribute('title') && trigger.getAttribute('title').trim())
                  || trigger.dataset.copyValue
                  || trigger.value
                  || trigger.textContent.trim();
      }

      if (!textToCopy) return;

      const success = await copyTextToClipboard(textToCopy);
      if (success) {
        applyCopiedFeedback(trigger);

        // If trigger points to a separate target, flash it with white-hot feedback as well
        if (targetEl && targetEl !== trigger) {
          targetEl.classList.add('copied-flash');
          setTimeout(() => {
            targetEl.classList.remove('copied-flash');
          }, 1800);
        }
      }
    });
  });
}

/**
 * Handles 6-character monospace TOTP inputs (both individual character apertures and numeric inputs).
 * Automatically advances focus, validates numeric digits, and handles backspace navigation.
 */
function initTotpInputs() {
  // Mode 1: Individual character apertures (.totp-group, .totp-slots, .aperture-slots, [data-totp-group])
  const apertureGroups = document.querySelectorAll('.totp-group, .totp-slots, .aperture-slots, [data-totp-group]');
  apertureGroups.forEach(group => {
    const slots = Array.from(group.querySelectorAll('input.totp-char, input.totp-digit, input[data-totp-index]'));
    if (!slots.length) return;

    slots.forEach((slot, index) => {
      slot.setAttribute('maxlength', '1');
      slot.setAttribute('inputmode', 'numeric');
      slot.setAttribute('pattern', '[0-9]');

      slot.addEventListener('input', () => {
        const val = slot.value.replace(/\D/g, '');
        slot.value = val ? val[0] : '';
        if (slot.value && index < slots.length - 1) {
          slots[index + 1].focus();
          slots[index + 1].select();
        } else if (slot.value && index === slots.length - 1) {
          // All slots complete: advance focus to submit button
          const form = slot.closest('form');
          const submitBtn = form?.querySelector('button[type="submit"], input[type="submit"]');
          if (submitBtn) submitBtn.focus();
        }
      });

      slot.addEventListener('keydown', (e) => {
        if (e.key === 'Backspace') {
          if (!slot.value && index > 0) {
            slots[index - 1].focus();
            slots[index - 1].value = '';
            e.preventDefault();
          }
        } else if (e.key === 'ArrowLeft' && index > 0) {
          slots[index - 1].focus();
          e.preventDefault();
        } else if (e.key === 'ArrowRight' && index < slots.length - 1) {
          slots[index + 1].focus();
          e.preventDefault();
        }
      });

      slot.addEventListener('paste', (e) => {
        e.preventDefault();
        const pasteData = (e.clipboardData || window.clipboardData)?.getData('text') || '';
        const digits = pasteData.replace(/\D/g, '').slice(0, slots.length);
        digits.split('').forEach((digit, i) => {
          if (slots[i]) slots[i].value = digit;
        });
        const targetIndex = Math.min(digits.length, slots.length - 1);
        if (digits.length >= slots.length) {
          const form = slot.closest('form');
          const submitBtn = form?.querySelector('button[type="submit"], input[type="submit"]');
          if (submitBtn) submitBtn.focus();
        } else if (slots[targetIndex]) {
          slots[targetIndex].focus();
        }
      });
    });
  });

  // Mode 2: Monospace 6-character single TOTP inputs (#totp_code, #code, .aperture-totp-*)
  const totpSingleInputs = document.querySelectorAll(
    '#totp_code, #code, .aperture-totp-input, .aperture-totp-compact, input[name="totp_code"], input[name="code"][maxlength="6"]'
  );

  totpSingleInputs.forEach(input => {
    if (input._totpInitialized) return;
    input._totpInitialized = true;

    input.setAttribute('inputmode', 'numeric');
    input.setAttribute('autocomplete', 'one-time-code');
    input.setAttribute('maxlength', '6');

    input.addEventListener('input', () => {
      const rawVal = input.value;
      const cleanVal = rawVal.replace(/\D/g, '').slice(0, 6);
      if (rawVal !== cleanVal) {
        input.value = cleanVal;
      }

      if (cleanVal.length === 6) {
        input.classList.add('totp-complete');
        // Automatically advance focus to submit button
        const form = input.closest('form');
        const submitBtn = form?.querySelector('button[type="submit"], input[type="submit"]');
        if (submitBtn) {
          submitBtn.focus();
        }
      } else {
        input.classList.remove('totp-complete');
      }
    });

    input.addEventListener('keydown', (e) => {
      if (e.key === 'Backspace' && input.value.length === 0) {
        // Move to previous form input if one exists
        const formInputs = Array.from(input.form?.querySelectorAll('input:not([type="hidden"])') || []);
        const idx = formInputs.indexOf(input);
        if (idx > 0) {
          formInputs[idx - 1].focus();
        }
      }
    });

    input.addEventListener('paste', (e) => {
      e.preventDefault();
      const pasteData = (e.clipboardData || window.clipboardData)?.getData('text') || '';
      const digits = pasteData.replace(/\D/g, '').slice(0, 6);
      input.value = digits;
      input.dispatchEvent(new Event('input', { bubbles: true }));
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

// Module and Global Exports for test harnesses & browser environments
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    initAlertDismissal,
    dismissAlert,
    initFileInputs,
    initDropzones,
    initCopyButtons,
    initTotpInputs,
    formatBytes,
    copyTextToClipboard,
    applyCopiedFeedback
  };
} else if (typeof window !== 'undefined') {
  window.MediaGuard = {
    initAlertDismissal,
    dismissAlert,
    initFileInputs,
    initDropzones,
    initCopyButtons,
    initTotpInputs,
    formatBytes,
    copyTextToClipboard,
    applyCopiedFeedback
  };
}
