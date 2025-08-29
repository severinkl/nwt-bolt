function goBack() {
  window.location.href = "index.html";
}

window.addEventListener("pywebviewready", async () => {
  const devices = await window.pywebview.api.get_device_list();
  const roles = await window.pywebview.api.get_device_roles();

  const tbody = document.getElementById("admin-table-body");

  devices.forEach(dev => {
    const row = document.createElement("tr");
    row.id = `row-${dev.name}`;

    // Name
    const nameCell = document.createElement("td");
    nameCell.textContent = dev.name;
    row.appendChild(nameCell);

    // Status
    const statusCell = document.createElement("td");
    statusCell.id = `status-${dev.name}`;
    statusCell.textContent = "...";
    row.appendChild(statusCell);

    // Role
    const roleCell = document.createElement("td");
    roleCell.id = `role-${dev.name}`;
    roleCell.textContent = "...";
    row.appendChild(roleCell);

    // Reboot / Shutdown / Exit
    const makeBtn = (text, handler) => {
      const btn = document.createElement("button");
      btn.textContent = text;
      btn.onclick = handler;
      btn.disabled = true;
      const td = document.createElement("td");
      td.appendChild(btn);
      return td;
    };

    row.appendChild(makeBtn("Reboot", () => window.pywebview.api.remote_reboot(dev.name)));
    row.appendChild(makeBtn("Shutdown", () => window.pywebview.api.remote_shutdown(dev.name)));
    row.appendChild(makeBtn("Exit", () => window.pywebview.api.remote_exit(dev.name)));

    // Dropdown Typ
    const typCell = document.createElement("td");
    const select = document.createElement("select");
    select.disabled = true;

    const types = ["router", "firewall", "server", "dns", "switch", "main"];
    const defaultType = roles[dev.name.toLowerCase()] || "router";

    types.forEach(type => {
      const option = document.createElement("option");
      option.value = type;
      option.textContent = type;
      if (type === defaultType) option.selected = true;
      select.appendChild(option);
    });

    typCell.appendChild(select);
    row.appendChild(typCell);

    // Start
    row.appendChild(makeBtn("Start", () =>
      window.pywebview.api.remote_start(dev.name, select.value)
    ));

    tbody.appendChild(row);
  });

  updateAllDeviceStatuses(); // Initialer Aufruf
  setInterval(updateAllDeviceStatuses, 5000); // Wiederholung alle 5s
});

function updateAllDeviceStatuses() {
  window.pywebview.api.get_all_device_statuses().then(statuses => {
    statuses.forEach(result => {
      const row = document.getElementById(`row-${result.name}`);
      if (!row) return;

      const statusCell = document.getElementById(`status-${result.name}`);
      const roleCell = document.getElementById(`role-${result.name}`);

      if (statusCell) statusCell.textContent = result.status;
      if (roleCell) roleCell.textContent = result.role || "no role";

      const shouldDisable = result.status !== "✅";

      row.querySelectorAll("button").forEach(btn => {
        btn.disabled = shouldDisable;
      });

      const select = row.querySelector("select");
      if (select) select.disabled = shouldDisable;
    });
  }).catch(err => {
    console.error("Fehler bei get_all_device_statuses:", err);
  });
}
