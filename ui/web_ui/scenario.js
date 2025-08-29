let maxSteps = 1;
let autoProgress = false;
let autoTimeout = 0;
let autoInterval = null;
let stepLock = false;

window.addEventListener('pywebviewready', () => {
  window.pywebview.api.get_max_steps().then(max => {
    maxSteps = max;
    return window.pywebview.api.get_auto_timeout();
  }).then(timeout => {
    autoTimeout = timeout;
    updateStatus();
    updateImage();
    updateAutoButton();
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "ArrowLeft") previousStep();
    if (event.key === "ArrowRight") nextStep();
    if (event.key === "Enter") handleAutoButtonClick();
  });
});

function nextStep() {
  if (stepLock) return;
  stepLock = true;
  stopAutoProgress();

  window.pywebview.api.get_status().then(state => {
    if (state.step + 1 < maxSteps) {
      return window.pywebview.api.next_step().then(() => true);
    }
    return false;
  }).then(advanced => {
    if (advanced) {
      updateStatus();
      updateImage();
      updateNavigationButtons();
      updateAutoButton();
    }
  }).finally(() => {
    stepLock = false;
  });
}

function previousStep() {
  if (stepLock) return;
  stepLock = true;
  stopAutoProgress();

  window.pywebview.api.get_status().then(state => {
    if (state.step > 0) {
      return window.pywebview.api.previous_step().then(() => true);
    }
    return false;
  }).then(wentBack => {
    if (wentBack) {
      updateStatus();
      updateImage();
      updateNavigationButtons();
      updateAutoButton();
    }
  }).finally(() => {
    stepLock = false;
  });
}

function restartScenario() {
  stopAutoProgress();
  window.pywebview.api.get_status().then(state => {
    window.pywebview.api.start_scenario(state.scenario).then(() => {
      updateStatus();
      updateImage();
      updateAutoButton();
    });
  });
}

function exitScenario() {
  window.pywebview.api.exit_scenario().then(() => {
    window.location.href = "index.html"; // ← zurück zur Auswahlseite
  });
}

function updateStatus() {
  window.pywebview.api.get_status().then(state => {
    document.getElementById("status").innerText = "Schritt: " + (state.step + 1) + " / " + maxSteps;
  });
  updateNavigationButtons();
}

function updateImage() {
  window.pywebview.api.get_image().then(base64img => {
    document.getElementById("scenarioImage").src = base64img;
  });
}

function startAutoProgress() {
  autoProgress = true;
  updateAutoButton();

  if (autoInterval) clearInterval(autoInterval);

  autoInterval = setInterval(() => {
    window.pywebview.api.get_status().then(state => {
      if (state.step + 1 >= maxSteps) {
        stopAutoProgress();
        updateAutoButton();
      } else {
        window.pywebview.api.next_step().then(() => {
          updateStatus();
          updateImage();
          updateAutoButton();
        });
      }
    });
  }, autoTimeout);
}

function updateNavigationButtons() {
  window.pywebview.api.get_status().then(state => {
    const prevBtn = document.querySelector("#controls button:nth-child(1)");
    const nextBtn = document.querySelector("#controls button:nth-child(3)");

    prevBtn.disabled = state.step === 0;
    nextBtn.disabled = state.step + 1 >= maxSteps;
  });
}

function stopAutoProgress() {
  autoProgress = false;
  clearInterval(autoInterval);
  autoInterval = null;
  updateAutoButton();
}

function restartScenario() {
  stopAutoProgress();

  // Dann sofort Szenario zurücksetzen
  window.pywebview.api.get_status().then(state => {
    window.pywebview.api.start_scenario(state.scenario).then(() => {
      updateStatus();
      updateImage();

      // Extra kurze Verzögerung, damit Auto-Schleife garantiert durch ist
      setTimeout(() => {
        updateAutoButton();
      }, 50); // 50–100ms reichen aus
    });
  });
}

function handleAutoButtonClick() {
  window.pywebview.api.get_status().then(state => {
    const isLastStep = state.step + 1 >= maxSteps;

    if (autoProgress) {
      stopAutoProgress();
      if (isLastStep) {
        // Entkoppelt, damit pywebview nicht kollidiert
        setTimeout(() => restartScenario(), 50);
      }
    } else if (isLastStep) {
      restartScenario();
    } else {
      startAutoProgress();
    }
  });
}

function updateAutoButton() {
  const btn = document.getElementById("auto-restart-btn");
  window.pywebview.api.get_status().then(state => {
    if (state.step + 1 >= maxSteps) {
      btn.innerText = "Neustart";
    } else if (autoProgress) {
      btn.innerText = "Stop";
    } else {
      btn.innerText = "Start";
    }
  });
}