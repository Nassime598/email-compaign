function collectHeaders() {
  const headers = [];
  const textarea = document.getElementById('headers');
  if (!textarea) {
    return headers;
  }
  const lines = textarea.value.split('\n');
  lines.forEach(line => {
    const parts = line.split(':');
    if (parts.length >= 2) {
      const name = parts[0].trim();
      const value = parts.slice(1).join(':').trim();
      if (name && value) {
        headers.push({ name, value });
      }
    }
  });
  return headers;
}

function loadServiceAccountsForCampaign() {
  fetch('/api/service_accounts')
    .then(response => response.json())
    .then(data => {
      const dropdown = document.getElementById('serviceAccountsDropdownForCampaign');
      dropdown.innerHTML = '<option value="">Select Service Account</option>';
      data.forEach(account => {
        const option = document.createElement('option');
        option.value = account.id;
        option.textContent = account.name;
        dropdown.appendChild(option);
      });
    });
}

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
  const campaignId = document.getElementById('campaignSelect').value;
  if (!campaignId) {
    alert('Please select a campaign to pause.');
    return;
  }
  fetch('/pause_campaign', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ campaign_id: parseInt(campaignId) })
  })
    .then(response => response.json())
    .then(data => alert(JSON.stringify(data)));
}

function resumeCampaign() {
  const campaignId = document.getElementById('campaignSelect').value;
  if (!campaignId) {
    alert('Please select a campaign to resume.');
    return;
  }
  fetch('/resume_campaign', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ campaign_id: parseInt(campaignId) })
  })
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

document.getElementById('createCampaignForm').addEventListener('submit', function (e) {
  e.preventDefault();
  const formData = new FormData(this);
  const jsonObject = {};
  formData.forEach((value, key) => { jsonObject[key] = value; });

  // Collect headers from textarea
  jsonObject['headers'] = collectHeaders();

  // Collect user IDs
  jsonObject['user_ids'] = document.getElementById('userIdsInput').value
    .split(',')
    .map(id => parseInt(id.trim()))
    .filter(id => !isNaN(id));

  fetch('/create_campaign', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(jsonObject)
  }).then(r => r.json()).then(data => alert(JSON.stringify(data)));
});

document.getElementById('uploadRecipientsForm').addEventListener('submit', function (e) {
  e.preventDefault();
  const formData = new FormData(this);
  fetch('/upload_recipients', {
    method: 'POST',
    body: formData
  }).then(r => r.json()).then(data => alert(JSON.stringify(data)));
});

document.getElementById('serviceAccountsDropdownForCampaign').addEventListener('change', function () {
  const serviceAccountId = this.value;
  if (serviceAccountId) {
    fetch(`/users?service_account_id=${serviceAccountId}`)
      .then(response => response.json())
      .then(data => {
        const userIds = data.map(user => user.id);
        document.getElementById('userIdsInput').value = userIds.join(',');
      });
  } else {
    document.getElementById('userIdsInput').value = '';
  }
});

window.onload = function () {
  loadServiceAccountsForCampaign();
  fetchLogs();
  fetchDashboard();
  loadCampaigns();
  fetchDashboardCampaigns();
  fetchDashboardServiceAccounts();
  setInterval(fetchLogs, 5000);
  setInterval(fetchDashboard, 10000);
  setInterval(fetchDashboardCampaigns, 10000);
  setInterval(fetchDashboardServiceAccounts, 10000);
};
