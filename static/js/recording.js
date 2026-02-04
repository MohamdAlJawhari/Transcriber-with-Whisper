(function () {
    const startBtn = document.getElementById('start-record-btn');
    const stopBtn = document.getElementById('stop-record-btn');
    const statusEl = document.getElementById('record-status');
    const playbackEl = document.getElementById('playback');
    const uploadForm = document.getElementById('upload-form');
    const spinnerEl = document.getElementById('spinner');
    const spinnerChunkEl = document.getElementById('spinner-chunk');
    const spinnerPercentEl = document.getElementById('spinner-percent');
    const spinnerProgressBarEl = document.getElementById('spinner-progress-bar');
    const spinnerProgressTrackEl = document.getElementById('spinner-progress-track');

    if (!startBtn || !stopBtn || !statusEl || !playbackEl) {
        return;
    }

    let mediaRecorder = null;
    let audioChunks = [];

    function setSpinnerProgress(chunk, total) {
        if (!spinnerChunkEl || !spinnerPercentEl || !spinnerProgressBarEl) {
            return;
        }

        const safeTotal = Number.isFinite(total) && total > 0 ? total : 0;
        const safeChunk = Number.isFinite(chunk) && chunk >= 0 ? chunk : 0;

        if (!safeTotal) {
            spinnerChunkEl.textContent = 'Chunk 0/0';
            spinnerPercentEl.textContent = '0%';
            spinnerProgressBarEl.style.width = '0%';
            if (spinnerProgressTrackEl) {
                spinnerProgressTrackEl.setAttribute('aria-valuenow', '0');
            }
            return;
        }

        const clampedChunk = Math.min(safeChunk, safeTotal);
        const percent = Math.floor((clampedChunk / safeTotal) * 100);

        spinnerChunkEl.textContent = `Chunk ${clampedChunk}/${safeTotal}`;
        spinnerPercentEl.textContent = `${percent}%`;
        spinnerProgressBarEl.style.width = `${percent}%`;
        if (spinnerProgressTrackEl) {
            spinnerProgressTrackEl.setAttribute('aria-valuenow', String(percent));
        }
    }

    function resetSpinnerProgress() {
        setSpinnerProgress(0, 0);
    }

    function showSpinner() {
        if (spinnerEl) {
            resetSpinnerProgress();
            spinnerEl.style.display = 'flex';
        }
    }

    function hideSpinner() {
        if (spinnerEl) {
            spinnerEl.style.display = 'none';
        }
    }

    const transcribeUrl = document.body ? document.body.dataset.transcribeUrl : null;

    async function transcribeWithProgress(formData) {
        showSpinner();
        if (statusEl) {
            statusEl.textContent = 'Status: uploading & transcribing...';
        }

        let doneReceived = false;

        function handlePayload(payload) {
            if (!payload || typeof payload !== 'object') {
                return;
            }

            if (payload.type === 'progress') {
                setSpinnerProgress(payload.chunk, payload.total);
                return;
            }

            if (payload.type === 'done') {
                doneReceived = true;
                if (payload.saved) {
                    if (statusEl) {
                        statusEl.textContent = 'Status: transcription complete. Reloading...';
                    }
                    window.location.reload();
                } else {
                    if (statusEl) {
                        statusEl.textContent = 'Status: transcription finished with no text.';
                    }
                    hideSpinner();
                    alert(payload.message || 'Transcription finished but no text was produced.');
                }
                return;
            }

            if (payload.type === 'error') {
                doneReceived = true;
                if (statusEl) {
                    statusEl.textContent = 'Status: error during transcription.';
                }
                hideSpinner();
                alert(payload.message || 'Error during transcription. Check server logs.');
            }
        }

        function processBuffer(buffer) {
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';
            for (const line of lines) {
                const trimmed = line.trim();
                if (!trimmed) {
                    continue;
                }
                try {
                    handlePayload(JSON.parse(trimmed));
                } catch (err) {
                    console.warn('Failed to parse progress update:', trimmed);
                }
            }
            return buffer;
        }

        try {
            const response = await fetch(transcribeUrl || '/transcribe', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Transcribe-Stream': '1',
                },
            });

            if (!response.ok || !response.body) {
                throw new Error('Transcription failed with status ' + response.status);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) {
                    break;
                }
                buffer += decoder.decode(value, { stream: true });
                buffer = processBuffer(buffer);
            }

            buffer += decoder.decode();
            processBuffer(buffer);

            if (!doneReceived) {
                hideSpinner();
            }
        } catch (err) {
            console.error(err);
            if (statusEl) {
                statusEl.textContent = 'Status: error during transcription.';
            }
            hideSpinner();
            alert('Error during transcription. Check server logs.');
        }
    }

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
                if (statusEl) {
                    statusEl.textContent = 'Status: recording stopped. Preparing upload...';
                }

                const blob = new Blob(audioChunks, { type: 'audio/webm' });

                const audioUrl = URL.createObjectURL(blob);
                playbackEl.src = audioUrl;
                playbackEl.style.display = 'block';

                const formData = new FormData();
                const fileName = 'recording.webm';
                formData.append('audio', blob, fileName);

                await transcribeWithProgress(formData);
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
        uploadForm.addEventListener('submit', (event) => {
            event.preventDefault();
            if (!uploadForm.checkValidity()) {
                uploadForm.reportValidity();
                return;
            }
            const formData = new FormData(uploadForm);
            transcribeWithProgress(formData);
        });
    }
})();
