document.getElementById('uploadServiceAccountForm').addEventListener('submit', function(e) {
  e.preventDefault();
  let formData = new FormData(this);
  fetch('/upload_service_account', {
    method: 'POST',
    body: formData
  }).then(r => r.json()).then(data => {
    alert(JSON.stringify(data));
    loadServiceAccounts();
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

window.onload = function() {
  loadServiceAccounts();
};
