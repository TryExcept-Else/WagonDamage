document.addEventListener('DOMContentLoaded', function () {
    const extractionForm = document.getElementById('extractionForm');
    const videoFile = document.getElementById('videoFile');
    const submitBtn = document.getElementById('submitBtn');
    const uploadCard = document.getElementById('uploadCard');
    const processingCard = document.getElementById('processingCard');
    const resultsCard = document.getElementById('resultsCard');
    const progressBar = document.getElementById('progressBar');
    const progressStatus = document.getElementById('progressStatus');
    const videoPreviewCard = document.getElementById('videoPreviewCard');
    const videoPlayer = document.getElementById('videoPlayer');
    const videoFileName = document.getElementById('videoFileName');
    const changeVideoBtn = document.getElementById('changeVideoBtn');
    const resultsContainer = document.getElementById('resultsContainer');
    const resultsMessage = document.getElementById('resultsMessage');


    // Enable submit button only when a file is selected
    videoFile.addEventListener('change', () => {
        if (videoFile.files.length > 0) {
            submitBtn.disabled = false;
            // Show video preview
            const file = videoFile.files[0];
            const videoURL = URL.createObjectURL(file);
            videoPlayer.src = videoURL;
            videoFileName.textContent = file.name;
            
            uploadCard.style.display = 'none';
            videoPreviewCard.style.display = 'block';

        } else {
            submitBtn.disabled = true;
        }
    });
    
    // Allow user to change the selected video
    changeVideoBtn.addEventListener('click', () => {
        videoFile.value = ''; // Reset file input
        videoPreviewCard.style.display = 'none';
        uploadCard.style.display = 'block';
        submitBtn.disabled = true;
    });

    // Handle form submission
    extractionForm.addEventListener('submit', function (e) {
        e.preventDefault();

        const formData = new FormData();
        formData.append('video', videoFile.files[0]);

        // Hide upload/preview and show processing card
        uploadCard.style.display = 'none';
        videoPreviewCard.style.display = 'none';
        processingCard.style.display = 'block';
        
        // Reset progress bar
        updateProgressBar(0, 'Submitting...');

        fetch("{{ url_for('frame_extraction') }}", {
            method: 'POST',
            body: formData,
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const taskId = data.task_id;
                // Start polling for task status
                pollTaskStatus(taskId);
            } else {
                alert('Error starting process: ' + data.error);
                resetToUploadState();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An unexpected error occurred.');
            resetToUploadState();
        });
    });

    function pollTaskStatus(taskId) {
        const interval = setInterval(() => {
            fetch(`/task-status/${taskId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.state === 'SUCCESS') {
                        clearInterval(interval);
                        processingCard.style.display = 'none';
                        displayResults(data.result);
                    } else if (data.state === 'FAILURE') {
                        clearInterval(interval);
                        alert('Processing failed: ' + data.status);
                        resetToUploadState();
                    } else {
                        // Update progress bar
                        updateProgressBar(data.progress, data.status);
                    }
                })
                .catch(error => {
                    clearInterval(interval);
                    console.error('Polling error:', error);
                    alert('Error checking task status.');
                    resetToUploadState();
                });
        }, 2000); // Poll every 2 seconds
    }
    
    function updateProgressBar(progress, status) {
        progressBar.style.width = progress + '%';
        progressBar.textContent = progress + '%';
        progressBar.setAttribute('aria-valuenow', progress);
        progressStatus.textContent = status;
    }

    function displayResults(resultData) {
        const frames = resultData.result;
        const count = resultData.count;

        resultsMessage.textContent = `Successfully extracted ${count} frames.`;
        
        // Clear previous results
        resultsContainer.innerHTML = ''; 
        
        if (frames && frames.length > 0) {
            frames.forEach(frameDataUrl => {
                const col = document.createElement('div');
                col.className = 'col-lg-3 col-md-4 col-6 mb-4';
                
                const link = document.createElement('a');
                link.href = frameDataUrl;
                link.target = '_blank';
                
                const img = document.createElement('img');
                img.src = frameDataUrl;
                img.className = 'img-fluid rounded shadow-sm frame-img';
                img.alt = 'Extracted Frame';
                
                link.appendChild(img);
                col.appendChild(link);
                resultsContainer.appendChild(col);
            });
        } else {
            resultsContainer.innerHTML = '<p class="text-center text-muted">No wagons were detected in the video.</p>';
        }
        
        resultsCard.style.display = 'block';
    }
    
    function resetToUploadState() {
        processingCard.style.display = 'none';
        resultsCard.style.display = 'none';
        videoPreviewCard.style.display = 'none';
        uploadCard.style.display = 'block';
        videoFile.value = '';
        submitBtn.disabled = true;
    }
});