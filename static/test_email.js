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

function loadUsersForServiceAccount(serviceAccountId) {
  fetch(`/users?service_account_id=${serviceAccountId}`)
    .then(response => response.json())
    .then(data => {
      const dropdown = document.getElementById('usersDropdown');
      dropdown.innerHTML = '<option value="">Select User Email</option>';
      data.forEach(user => {
        const option = document.createElement('option');
        option.value = user.id;
        option.textContent = user.email;
        dropdown.appendChild(option);
      });
    });
}

document.getElementById('serviceAccountsDropdown').addEventListener('change', function () {
  const serviceAccountId = this.value;
  if (serviceAccountId) {
    loadUsersForServiceAccount(serviceAccountId);
  } else {
    document.getElementById('usersDropdown').innerHTML = '<option value="">Select User Email</option>';
  }
});

document.getElementById('testEmailForm').addEventListener('submit', function (e) {
  e.preventDefault();
  const formData = new FormData(this);

  const payload = {
    service_account_id: parseInt(formData.get('service_account_id')),
    user_id: parseInt(formData.get('user_id')),
    raw_headers: formData.get('raw_headers'),
    body_html: formData.get('body_html')
  };

  fetch('/send_test_email', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  })
    .then(response => response.json())
    .then(data => {
      alert(JSON.stringify(data));
      fetchLogs();
    });
});

function fetchLogs() {
  fetch('/logs')
    .then(response => response.json())
    .then(data => {
      const logDiv = document.getElementById('logs');
      logDiv.innerHTML = data.logs.map(log => `<div>${log}</div>`).join('');
    });
}

window.onload = function () {
  loadServiceAccounts();
  fetchLogs();
  setInterval(fetchLogs, 5000);
};
