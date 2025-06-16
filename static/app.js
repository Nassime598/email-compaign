function startCampaign() {
  const campaignId = prompt("Enter Campaign ID to Start:");
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

document.getElementById('uploadServiceAccountForm').addEventListener('submit', function(e) {
  e.preventDefault();
  let formData = new FormData(this);
  fetch('/upload_service_account', {
    method: 'POST',
    body: formData
  }).then(r => r.json()).then(data => {
    alert(JSON.stringify(data));
    loadServiceAccounts(); // reload service accounts after upload
    loadServiceAccountsForCampaign();
  });
});

document.getElementById('uploadUserListForm').addEventListener('submit', function(e) {
  e.preventDefault();
  let formData = new FormData(this);
  fetch('/upload_user_list', {
    method: 'POST',
    body: formData
  }).then(r => r.json()).then(data => alert(JSON.stringify(data)));
});

document.getElementById('createCampaignForm').addEventListener('submit', function(e) {
  e.preventDefault();
  const formData = new FormData(this);
  const jsonObject = {};
  formData.forEach((value, key) => { jsonObject[key] = value; });
  jsonObject['user_ids'] = document.getElementById('userIdsInput').value.split(',').map(id => parseInt(id.trim()));
  fetch('/create_campaign', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(jsonObject)
  }).then(r => r.json()).then(data => alert(JSON.stringify(data)));
});

document.getElementById('uploadRecipientsForm').addEventListener('submit', function(e) {
  e.preventDefault();
  let formData = new FormData(this);
  fetch('/upload_recipients', {
    method: 'POST',
    body: formData
  }).then(r => r.json()).then(data => alert(JSON.stringify(data)));
});

function loadServiceAccounts() {
  fetch('/api/service_accounts')
    .then(response => response.json())
    .then(data => {
      const dropdown = document.getElementById('serviceAccountsDropdown');
      dropdown.innerHTML = '<option value="">Select Service Account</option>';
      data.forEach(account => {
        const option = document.createElement('option');
        option.value = account.id;
        option.textContent = account.name;
        dropdown.appendChild(option);
      });
    });
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

document.getElementById('serviceAccountsDropdownForCampaign').addEventListener('change', function() {
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

// Initialize everything on page load
window.onload = function() {
  loadServiceAccounts();
  loadServiceAccountsForCampaign();
  fetchLogs();
  fetchDashboard();
  setInterval(fetchLogs, 5000);
  setInterval(fetchDashboard, 10000);
};
