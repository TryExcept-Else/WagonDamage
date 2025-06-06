document.addEventListener('DOMContentLoaded', function() {
    const dateInput = document.getElementById('dateInput');
    const videoSelect = document.getElementById('videoSelect');
    const processBtn = document.getElementById('processBtn');
    const videoPreviewCard = document.getElementById('videoPreviewCard');
    const processingCard = document.getElementById('processingCard');
    const resultsCard = document.getElementById('resultsCard');
    const videoPlayer = document.getElementById('videoPlayer');
    const videoSource = document.getElementById('videoSource');
    const videoDetails = document.getElementById('videoDetails');
    const detectionProgressBar = document.getElementById('detectionProgressBar');
    const cancelProcessingBtn = document.getElementById('cancelProcessingBtn');
    const newDetectionBtn = document.getElementById('newDetectionBtn');
    
    // Status elements
    const statusInitializing = document.getElementById('statusInitializing');
    const statusFrameExtraction = document.getElementById('statusFrameExtraction');
    const statusObjectDetection = document.getElementById('statusObjectDetection');
    const statusDamageAnalysis = document.getElementById('statusDamageAnalysis');
    const statusReportGeneration = document.getElementById('statusReportGeneration');
    
    // Handle date selection change
    if (dateInput) {
        dateInput.addEventListener('change', function() {
            const selectedDate = this.value;
            
            if (!selectedDate) return;
            
            // Make an AJAX request to get videos for the selected date
            fetch(`/api/videos/${selectedDate}`)
                .then(response => response.json())
                .then(data => {
                    // Clear video select options
                    videoSelect.innerHTML = '<option value="" selected disabled>Choose a video...</option>';
                    
                    // Add new options
                    if (data.videos && data.videos.length > 0) {
                        data.videos.forEach(video => {
                            const option = document.createElement('option');
                            option.value = video;
                            option.textContent = video;
                            videoSelect.appendChild(option);
                        });
                        
                        videoSelect.disabled = false;
                        processBtn.disabled = false;
                    } else {
                        videoSelect.innerHTML = '<option value="" selected disabled>No videos available</option>';
                        videoSelect.disabled = true;
                        processBtn.disabled = true;
                    }
                })
                .catch(error => {
                    console.error('Error fetching videos:', error);
                    videoSelect.innerHTML = '<option value="" selected disabled>Error loading videos</option>';
                    videoSelect.disabled = true;
                    processBtn.disabled = true;
                });
        });
    }
    
    // Handle video selection change
    if (videoSelect) {
        videoSelect.addEventListener('change', function() {
            if (this.value && videoPreviewCard) {
                // Show video preview
                videoPreviewCard.style.display = 'block';
                
                // Get the actual video URL
                const selectedDate = dateInput.value;
                const selectedVideo = this.value;
                
                if (videoSource) {
                    // In a real application, this would be a proper URL to your video
                    // For now, we'll use a placeholder or potentially a generated URL
                    videoSource.src = '';
                    videoPlayer.load();
                    
                    // If you have implemented the video serving endpoint:
                    // videoSource.src = `/videos/${selectedDate}/${selectedVideo}`;
                }
                
                // Update video details
                if (videoDetails) {
                    videoDetails.textContent = `Filename: ${this.value}`;
                }
            } else if (videoPreviewCard) {
                videoPreviewCard.style.display = 'none';
            }
        });
    }
    
    // Handle form submission
    const detectionForm = document.getElementById('detectionForm');
    if (detectionForm) {
        detectionForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            if (!videoSelect.value) {
                alert('Please select a video to process.');
                return;
            }
            
            // Hide video preview and show processing card
            if (videoPreviewCard) videoPreviewCard.style.display = 'none';
            if (processingCard) processingCard.style.display = 'block';
            
            // Mock processing
            let progress = 0;
            
            // Update status: Initializing
            if (statusInitializing) {
                updateStatus(statusInitializing, 'success', 'Completed');
            }
            
            const processingInterval = setInterval(function() {
                progress += 1;
                if (detectionProgressBar) {
                    detectionProgressBar.style.width = progress + '%';
                    detectionProgressBar.textContent = progress + '%';
                    detectionProgressBar.setAttribute('aria-valuenow', progress);
                }
                
                // Update statuses based on progress
                if (progress === 20 && statusFrameExtraction && statusObjectDetection) {
                    updateStatus(statusFrameExtraction, 'success', 'Completed');
                    updateStatus(statusObjectDetection, 'primary', 'In Progress');
                } else if (progress === 50 && statusObjectDetection && statusDamageAnalysis) {
                    updateStatus(statusObjectDetection, 'success', 'Completed');
                    updateStatus(statusDamageAnalysis, 'primary', 'In Progress');
                } else if (progress === 80 && statusDamageAnalysis && statusReportGeneration) {
                    updateStatus(statusDamageAnalysis, 'success', 'Completed');
                    updateStatus(statusReportGeneration, 'primary', 'In Progress');
                } else if (progress >= 100 && statusReportGeneration) {
                    clearInterval(processingInterval);
                    updateStatus(statusReportGeneration, 'success', 'Completed');
                    
                    // Show results after a short delay
                    setTimeout(function() {
                        if (processingCard) processingCard.style.display = 'none';
                        if (resultsCard) resultsCard.style.display = 'block';
                    }, 1000);
                }
            }, 100);
            
            // Cancel processing
            if (cancelProcessingBtn) {
                cancelProcessingBtn.addEventListener('click', function() {
                    clearInterval(processingInterval);
                    if (processingCard) processingCard.style.display = 'none';
                    if (videoPreviewCard) videoPreviewCard.style.display = 'block';
                });
            }
        });
    }
    
    // New detection button
    if (newDetectionBtn) {
        newDetectionBtn.addEventListener('click', function() {
            // Reset UI state
            if (resultsCard) resultsCard.style.display = 'none';
            if (videoPreviewCard) videoPreviewCard.style.display = 'none';
            
            // Reset progress bar and statuses
            if (detectionProgressBar) {
                detectionProgressBar.style.width = '0%';
                detectionProgressBar.textContent = '0%';
                detectionProgressBar.setAttribute('aria-valuenow', 0);
            }
            
            if (statusInitializing && statusFrameExtraction && statusObjectDetection && 
                statusDamageAnalysis && statusReportGeneration) {
                updateStatus(statusInitializing, 'primary', 'In Progress');
                updateStatus(statusFrameExtraction, 'secondary', 'Waiting');
                updateStatus(statusObjectDetection, 'secondary', 'Waiting');
                updateStatus(statusDamageAnalysis, 'secondary', 'Waiting');
                updateStatus(statusReportGeneration, 'secondary', 'Waiting');
            }
            
            // Clear form selections - dateInput doesn't have selectedIndex
            if (videoSelect) videoSelect.selectedIndex = 0;
            
            // Reset the form
            if (detectionForm) detectionForm.reset();
        });
    }
    
    // Helper function to update status
    function updateStatus(element, statusClass, statusText) {
        if (!element) return;
        
        // Update icon
        const statusBadge = element.querySelector('.status-badge');
        if (statusBadge) {
            statusBadge.className = `status-badge bg-${statusClass}`;
            
            if (statusClass === 'primary') {
                statusBadge.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            } else if (statusClass === 'success') {
                statusBadge.innerHTML = '<i class="fas fa-check"></i>';
            } else {
                statusBadge.innerHTML = '<i class="fas fa-clock"></i>';
            }
        }
        
        // Update status badge
        const statusState = element.querySelector('.status-state .badge');
        if (statusState) {
            statusState.className = `badge bg-${statusClass}`;
            statusState.textContent = statusText;
        }
    }
}); 