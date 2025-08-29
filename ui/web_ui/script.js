let maxSteps = 1;
let autoProgress = false;
let autoTimeout = 0;
let autoInterval = null;

function startScenario(id) {
  window.pywebview.api.start_scenario(id).then(() => {
    window.location.href = "scenario.html"; // neue Seite statt ausblenden
  });
}

document.addEventListener("DOMContentLoaded", () => {
  createNumpad();
  const logo = document.getElementById("logo");
  if (logo) {
    logo.addEventListener("click", handleLogoClick);
  }

  waitForPywebviewApi(() => {
    loadDeviceListOnce();
    setInterval(updateDeviceStatuses, 5000); // alle 5 Sekunden
  });
});

function waitForPywebviewApi(callback, retries = 20, delay = 200) {
  if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.get_device_list === 'function') {
    console.log("pywebview.api ist bereit");
    callback();
  } else if (retries > 0) {
    console.log("Warte auf pywebview.api...");
    setTimeout(() => waitForPywebviewApi(callback, retries - 1, delay), delay);
  } else {
    console.error("pywebview API nicht verfügbar.");
  }
}

function handleLogoClick() {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.logo_clicked().then(triggered => {
      if (triggered) {
        openPinOverlay();
      }
    });
  }
}

let enteredPin = "";

function openPinOverlay() {
  enteredPin = "";
  document.getElementById("pin-input").value = "";
  document.getElementById("pin-error").style.display = "none";
  
  // Nur Inhalte verstecken, nicht den body
  document.getElementById("top-bar").style.display = "none";
  document.getElementById("scenario-selection").style.display = "none";
  document.getElementById("scenario-display").style.display = "none";


  // PIN-Feld zeigen
  document.getElementById("pin-overlay").style.display = "flex";
}

function closePinOverlay() {
  document.getElementById("pin-overlay").style.display = "none";

  // Nur den oberen Bereich wieder einblenden – Szenarioanzeige bleibt separat gesteuert
  document.getElementById("top-bar").style.display = "";
  document.getElementById("scenario-selection").style.display = "";
}

function checkPin() {
  window.pywebview.api.check_pin(enteredPin).then(correct => {
    if (correct) {
      window.location.href = "admin.html"; // ← neue Seite statt Overlay
    } else {
      document.getElementById("pin-error").style.display = "block";
      enteredPin = "";
      document.getElementById("pin-input").value = "";
    }
  });
}


function createNumpad() {
  const keys = ['1','2','3','4','5','6','7','8','9','←','0','OK'];
  const np = document.getElementById("numpad");
  keys.forEach(k => {
    const btn = document.createElement("button");
    btn.innerText = k;
    btn.onclick = () => handleNumpadClick(k);
    np.appendChild(btn);
  });
}

function handleNumpadClick(key) {
  if (key === '←') {
    enteredPin = enteredPin.slice(0, -1);
  } else if (key === 'OK') {
    checkPin();
    return;
  } else {
    enteredPin += key;
  }
  document.getElementById("pin-input").value = "*".repeat(enteredPin.length);
}

function loadDeviceListOnce() {
  if (!window.pywebview || !window.pywebview.api.get_device_list) return;

  window.pywebview.api.get_device_list().then(devices => {
    const tbody = document.getElementById("device-status-body");
    tbody.innerHTML = "";

    devices.forEach(dev => {
      const row = document.createElement("tr");
      row.id = `row-${dev.name}`;

      const name = document.createElement("td");
      name.innerText = dev.name;
      row.appendChild(name);

      const status = document.createElement("td");
      status.innerText = "...";
      status.id = `status-${dev.name}`;
      row.appendChild(status);

      const role = document.createElement("td");
      role.textContent = "...";
      role.id = `role-${dev.name}`;
      row.appendChild(role);

      tbody.appendChild(row);
    });

    // Erstes Mal Status laden nach Aufbau
    updateDeviceStatuses();
  }).catch(err => {
    console.error("Fehler beim Abrufen der Geräteliste:", err);
  });
}

function updateDeviceStatuses() {
  window.pywebview.api.get_all_device_statuses().then(statuses => {
    statuses.forEach(result => {
      const row = document.getElementById(`row-${result.name}`);
      if (!row) return;

      const cell = document.getElementById(`status-${result.name}`);
      const roleCell = document.getElementById(`role-${result.name}`);
      if (cell) cell.innerText = result.status;
      if (roleCell) roleCell.textContent = result.role || "no role";
    });
  }).catch(err => {
    console.error("Fehler bei get_all_device_statuses:", err);
  });
}