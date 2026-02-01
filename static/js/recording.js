(function () {
    const startBtn = document.getElementById('start-record-btn');
    const stopBtn = document.getElementById('stop-record-btn');
    const statusEl = document.getElementById('record-status');
    const playbackEl = document.getElementById('playback');
    const uploadForm = document.getElementById('upload-form');
    const spinnerEl = document.getElementById('spinner');

    if (!startBtn || !stopBtn || !statusEl || !playbackEl) {
        return;
    }

    let mediaRecorder = null;
    let audioChunks = [];

    function showSpinner() {
        if (spinnerEl) {
            spinnerEl.style.display = 'flex';
        }
    }

    function hideSpinner() {
        if (spinnerEl) {
            spinnerEl.style.display = 'none';
        }
    }

    const transcribeUrl = document.body ? document.body.dataset.transcribeUrl : null;

    async function initMedia() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);

            mediaRecorder.onstart = () => {
                audioChunks = [];
                statusEl.textContent = 'Status: recording...';
                playbackEl.style.display = 'none';
                playbackEl.src = '';
            };

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunks.push(event.data);
                }
            };

            mediaRecorder.onstop = async () => {
                statusEl.textContent = 'Status: recording stopped. Preparing upload...';

                const blob = new Blob(audioChunks, { type: 'audio/webm' });

                const audioUrl = URL.createObjectURL(blob);
                playbackEl.src = audioUrl;
                playbackEl.style.display = 'block';

                const formData = new FormData();
                const fileName = 'recording.webm';
                formData.append('audio', blob, fileName);

                try {
                    statusEl.textContent = 'Status: uploading & transcribing...';
                    showSpinner();
                    const response = await fetch(transcribeUrl || '/transcribe', {
                        method: 'POST',
                        body: formData,
                    });

                    if (response.ok) {
                        statusEl.textContent = 'Status: transcription complete. Reloading...';
                        window.location.reload();
                    } else {
                        statusEl.textContent = 'Status: error during transcription (HTTP ' + response.status + ')';
                        hideSpinner();
                        alert('Error during transcription. Check server logs.');
                    }
                } catch (err) {
                    console.error(err);
                    statusEl.textContent = 'Status: error sending recording.';
                    hideSpinner();
                    alert('Failed to send recording to server.');
                }
            };
        } catch (err) {
            console.error('Could not access microphone:', err);
            statusEl.textContent = 'Status: microphone permission denied or not available.';
            startBtn.disabled = true;
            stopBtn.disabled = true;
        }
    }

    window.addEventListener('load', initMedia);

    startBtn.addEventListener('click', () => {
        if (mediaRecorder && mediaRecorder.state === 'inactive') {
            mediaRecorder.start();
            startBtn.disabled = true;
            stopBtn.disabled = false;
        }
    });

    stopBtn.addEventListener('click', () => {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
            startBtn.disabled = false;
            stopBtn.disabled = true;
        }
    });

    if (uploadForm) {
        uploadForm.addEventListener('submit', () => {
            showSpinner();
        });
    }
})();
