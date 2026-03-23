// Handle audio file upload
document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('upload-form');
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const fileInput = document.getElementById('audio-file');
            if (!fileInput.files.length) return;
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('upload-result').textContent = data.result || 'No result';
            })
            .catch(() => {
                document.getElementById('upload-result').textContent = 'Error processing file.';
            });
        });
    }
});
function updateDashboard() {
    fetch('/status')
        .then(response => {
            if (!response.ok) throw new Error('Offline');
            return response.json();
        })
        .then(data => {
            // Update live indicator
            const liveIndicator = document.getElementById('live-indicator');
            liveIndicator.textContent = 'Live';
            liveIndicator.classList.remove('offline');
            liveIndicator.classList.add('live');
            // Update level bar (max 100%)
            let level = Math.min(data.level * 100, 100);
            document.getElementById('level-bar').style.width = level + '%';
            // Update status message
            document.getElementById('status-msg').textContent = 'Status: ' + data.status;
        })
        .catch(() => {
            // If fetch fails, show offline
            const liveIndicator = document.getElementById('live-indicator');
            liveIndicator.textContent = 'Offline';
            liveIndicator.classList.remove('live');
            liveIndicator.classList.add('offline');
            document.getElementById('level-bar').style.width = '0%';
            document.getElementById('status-msg').textContent = 'Status: --';
        });
}
setInterval(updateDashboard, 200);
