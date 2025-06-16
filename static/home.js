function startCampaign() {
  const campaignId = document.getElementById('campaignSelect').value;
  if (!campaignId) {
    alert('Please select a campaign to start.');
    return;
  }
  fetch(`/start_campaign/${campaignId}`, { method: 'POST' })
    .then(response => response.json())
    .then(data => alert(JSON.stringify(data)));
}

function pauseCampaign() {
  fetch('/pause_campaign', { method: 'POST' })
    .then(response => response.json())
    .then(data => alert(JSON.stringify(data)));
}

function resumeCampaign() {
  fetch('/resume_campaign', { method: 'POST' })
    .then(response => response.json())
    .then(data => alert(JSON.stringify(data)));
}

function clearLogs() {
  fetch('/clear_logs', { method: 'POST' })
    .then(response => response.json())
    .then(data => {
      alert(JSON.stringify(data));
      fetchLogs();
    });
}

function fetchLogs() {
  fetch('/logs')
    .then(response => response.json())
    .then(data => {
      const logDiv = document.getElementById('logs');
      logDiv.innerHTML = data.logs.map(log => `<div>${log}</div>`).join('');
    });
}

function fetchDashboard() {
  fetch('/dashboard_data')
    .then(response => response.json())
    .then(data => {
      const ctx = document.getElementById('dashboardChart').getContext('2d');
      if (window.myChart) {
        window.myChart.destroy();
      }
      window.myChart = new Chart(ctx, {
        type: 'pie',
        data: {
          labels: ['Success', 'Failed'],
          datasets: [{
            data: [data.success, data.failed],
            backgroundColor: ['#4CAF50', '#F44336']
          }]
        }
      });
    });
}

function loadCampaigns() {
  fetch('/api/campaigns')
    .then(response => response.json())
    .then(data => {
      const select = document.getElementById('campaignSelect');
      select.innerHTML = '<option value="">Select Campaign to Start</option>';
      data.forEach(campaign => {
        const option = document.createElement('option');
        option.value = campaign.id;
        option.textContent = campaign.name;
        select.appendChild(option);
      });
    });
}

function fetchDashboardCampaigns() {
  fetch('/api/dashboard_campaigns')
    .then(response => response.json())
    .then(data => {
      const tbody = document.getElementById('campaignsTable').querySelector('tbody');
      tbody.innerHTML = '';
      data.forEach(campaign => {
        const row = `<tr>
          <td>${campaign.id}</td>
          <td>${campaign.name}</td>
          <td>${campaign.sent}</td>
          <td>${campaign.failed}</td>
          <td>${campaign.status}</td>
        </tr>`;
        tbody.innerHTML += row;
      });
    });
}

function fetchDashboardServiceAccounts() {
  fetch('/api/dashboard_service_accounts')
    .then(response => response.json())
    .then(data => {
      const tbody = document.getElementById('serviceAccountsTable').querySelector('tbody');
      tbody.innerHTML = '';
      data.forEach(account => {
        const row = `<tr>
          <td>${account.id}</td>
          <td>${account.name}</td>
          <td>${account.quota}</td>
        </tr>`;
        tbody.innerHTML += row;
      });
    });
}


window.onload = function() {
  fetchLogs();
  fetchDashboard();
  loadCampaigns();
  fetchDashboardCampaigns();
  fetchDashboardServiceAccounts();
  setInterval(fetchLogs, 5000);
  setInterval(fetchDashboard, 10000);
  setInterval(fetchDashboardCampaigns, 10000); // Optional auto-refresh
  setInterval(fetchDashboardServiceAccounts, 10000); // Optional auto-refresh
};
