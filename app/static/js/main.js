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
  initAuditChainVerify();
  initAttackSimulations();
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

/**
 * Initializes 1-click blockchain hash-chain integrity sweep via AJAX.
 */
function initAuditChainVerify() {
  const verifyForm = document.getElementById('verify-chain-form');
  const verifyBtn = document.getElementById('btn-verify-chain');
  const statusBanner = document.getElementById('chain-status-banner');

  if (verifyForm && verifyBtn && statusBanner) {
    if (verifyForm._auditChainInitialized) return;
    verifyForm._auditChainInitialized = true;

    verifyForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      verifyBtn.disabled = true;
      const originalText = verifyBtn.innerHTML;
      verifyBtn.innerHTML = `
        <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <line x1="12" y1="2" x2="12" y2="6"/>
          <line x1="12" y1="18" x2="12" y2="22"/>
          <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/>
          <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/>
          <line x1="2" y1="12" x2="6" y2="12"/>
          <line x1="18" y1="12" x2="22" y2="12"/>
        </svg>
        <span>SWEEPING CHAIN...</span>
      `;

      statusBanner.innerHTML = `
        <div class="sweep-hud-container font-mono">
          <div class="sweep-scan-banner">
            <div class="flex-row justify-between items-center text-xs">
              <span class="text-primary font-bold">[INTEGRITY_SWEEP_ACTIVE]</span>
              <span class="text-dim">RECOMPUTING MERKLE RECURSIVE HASHES...</span>
            </div>
            <div class="sweep-progress-track">
              <div class="sweep-progress-bar"></div>
            </div>
            <div class="text-dim text-xs">
              SWEEPING LEDGER BLOCKS [0x00 ... HEAD] // VERIFYING LINKAGE INTEGRITY
            </div>
          </div>
        </div>
      `;

      try {
        const res = await fetch('/audit/verify-chain', {
          method: 'POST',
          headers: {
            'Accept': 'application/json'
          }
        });
        const data = await res.json();

        if (data.valid) {
          statusBanner.innerHTML = `
            <div class="alert alert-success">
              <div class="alert-content">
                <span class="badge-status badge-authentic font-mono">[CHAIN_VERIFIED_INTACT]</span>
                <span class="font-mono text-sm">${data.message}</span>
                <span class="text-dim font-mono text-xs ml-auto">0xMG SHA-256 HASH-CHAIN INTEGRITY: 100% VALID</span>
              </div>
            </div>
          `;
        } else {
          statusBanner.innerHTML = `
            <div class="alert alert-danger pulse-danger">
              <div class="alert-content">
                <span class="badge-status badge-modified font-mono">[CHAIN_INTEGRITY_BREACH]</span>
                <span class="font-mono text-sm">${data.message}</span>
                <span class="text-danger font-mono text-xs ml-auto font-bold">FAULT DETECTED AT BLOCK ID: #${data.corrupted_log_id}</span>
              </div>
            </div>
          `;
        }
      } catch (err) {
        statusBanner.innerHTML = `
          <div class="alert alert-danger">
            <div class="alert-content">
              <span class="badge-status badge-modified font-mono">[ERROR]</span>
              <span class="font-mono text-sm">Failed to execute hash-chain integrity sweep request.</span>
            </div>
          </div>
        `;
      } finally {
        verifyBtn.disabled = false;
        verifyBtn.innerHTML = originalText;
      }
    });
  }
}

/**
 * Initializes adversarial attack simulation suite and real-time oscilloscope console.
 */
function initAttackSimulations() {
  const runButtons = document.querySelectorAll('.btn-run-attack');
  const emptyBox = document.getElementById('simulation-output-empty');
  const activeBox = document.getElementById('simulation-output-active');
  const consolePill = document.getElementById('console-status-pill');
  const titleEl = document.getElementById('result-title');
  const owaspEl = document.getElementById('result-owasp');
  const statusContainer = document.getElementById('result-status-container');
  const defenseEl = document.getElementById('result-defense');
  const logEl = document.getElementById('result-log');
  const terminalCard = document.getElementById('terminal-card');
  const clockEl = document.getElementById('telemetry-clock');

  if (!runButtons.length && !clockEl) return;

  // Real-time oscilloscope UTC microsecond clock
  function updateClock() {
    if (!clockEl) return;
    const now = new Date();
    const h = String(now.getUTCHours()).padStart(2, '0');
    const m = String(now.getUTCMinutes()).padStart(2, '0');
    const s = String(now.getUTCSeconds()).padStart(2, '0');
    const ms = String(now.getUTCMilliseconds()).padStart(3, '0');
    clockEl.textContent = `UTC ${h}:${m}:${s}.${ms}000`;
  }
  if (clockEl && !window._clockIntervalSet) {
    window._clockIntervalSet = true;
    setInterval(updateClock, 100);
    updateClock();
  }

  runButtons.forEach(btn => {
    if (btn._attackBtnInitialized) return;
    btn._attackBtnInitialized = true;

    btn.addEventListener('click', async () => {
      const attackId = btn.getAttribute('data-attack-id');
      btn.disabled = true;
      const originalText = btn.innerHTML;
      btn.innerHTML = '<span>[DISPATCHING VECTOR...]</span>';
      if (consolePill) {
        consolePill.textContent = '[EXECUTING TELEMETRY...]';
        consolePill.className = 'badge-status badge-warning font-mono text-xs pulse-amber';
      }

      try {
        const res = await fetch(`/experiments/run/${attackId}`, {
          method: 'POST',
          headers: {
            'Accept': 'application/json'
          }
        });
        const data = await res.json();

        if (data.success) {
          if (emptyBox) emptyBox.classList.add('hidden');
          if (activeBox) activeBox.classList.remove('hidden');

          if (titleEl) titleEl.textContent = data.title;
          if (owaspEl) owaspEl.textContent = data.owasp;
          if (defenseEl) defenseEl.textContent = data.cryptographic_defense;

          const now = new Date();
          const timestamp = `[${now.toISOString()}] [VECTOR: ${attackId.toUpperCase()}]\n`;
          if (logEl) logEl.textContent = timestamp + data.diagnostic_log;

          if (statusContainer) {
            if (data.status === 'BLOCKED' || data.status === 'DETECTED') {
              statusContainer.innerHTML = `<span class="badge-status badge-authentic font-mono text-sm">${data.status}: ATTACK MITIGATED</span>`;
              if (consolePill) {
                consolePill.textContent = `[${data.status} // DEFENSE VERIFIED]`;
                consolePill.className = 'badge-status badge-authentic font-mono text-xs';
              }
            } else {
              statusContainer.innerHTML = `<span class="badge-status badge-modified font-mono text-sm pulse-danger">${data.status}</span>`;
              if (consolePill) {
                consolePill.textContent = `[${data.status} // BREACH]`;
                consolePill.className = 'badge-status badge-modified font-mono text-xs pulse-danger';
              }
            }
          }

          if (terminalCard) {
            terminalCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
          }
        } else {
          alert('Failed to execute simulation: ' + (data.error || 'Server Error'));
        }
      } catch (err) {
        alert('Network or server error executing simulation: ' + err.message);
      } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
      }
    });
  });
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
    initAuditChainVerify,
    initAttackSimulations,
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
    initAuditChainVerify,
    initAttackSimulations,
    formatBytes,
    copyTextToClipboard,
    applyCopiedFeedback
  };
}
