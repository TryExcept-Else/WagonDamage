document.addEventListener('DOMContentLoaded', function() {
    // Form elements
    const retrieveForm = document.getElementById('retrieveForm');
    const retrieveBtn = document.getElementById('retrieveBtn');
    const retrieveDateInput = document.getElementById('retrieveDate');
    const cameraAngleInputs = document.querySelectorAll('input[name="camera_angle"]');
    const videoTypeInputs = document.querySelectorAll('input[name="video_type"]');
    
    // Results display elements
    const folderSelect = document.getElementById('folderSelect');
    const folderSelectContainer = document.getElementById('folderSelectContainer');
    const videoListContainer = document.getElementById('videoListContainer');
    const videoList = document.getElementById('videoList');
    const processBtn = document.getElementById('processBtn');
    const noResultsMessage = document.getElementById('noResultsMessage');
    const loadingSpinner = document.getElementById('loadingSpinner');
    
    // Set default date to today
    if (retrieveDateInput) {
        const today = new Date();
        // Format date as YYYY-MM-DD for the date input
        const formattedDate = today.getFullYear() + '-' + 
            String(today.getMonth() + 1).padStart(2, '0') + '-' + 
            String(today.getDate()).padStart(2, '0');
        retrieveDateInput.value = formattedDate;
    }
    
    // Initialize state
    let retrievedFolders = [];
    let selectedFolder = null;
    
    // Handle retrieve button click
    if (retrieveBtn && retrieveForm) {
        retrieveBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Collect form data
            const formData = new FormData(retrieveForm);
            
            // Show loading spinner
            if (loadingSpinner) loadingSpinner.style.display = 'block';
            if (folderSelectContainer) folderSelectContainer.style.display = 'none';
            if (videoListContainer) videoListContainer.style.display = 'none';
            if (noResultsMessage) noResultsMessage.style.display = 'none';
            
            // Send request to retrieve videos
            fetch('/retrieve_videos', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                // Hide loading spinner
                if (loadingSpinner) loadingSpinner.style.display = 'none';
                
                if (data.success && data.folders && data.folders.length > 0) {
                    retrievedFolders = data.folders;
                    
                    // Populate folder select dropdown
                    if (folderSelect) {
                        // Clear existing options
                        folderSelect.innerHTML = '';
                        
                        // Add default option
                        const defaultOption = document.createElement('option');
                        defaultOption.value = '';
                        defaultOption.textContent = 'Select a folder...';
                        folderSelect.appendChild(defaultOption);
                        
                        // Add options for each folder
                        data.folders.forEach(folder => {
                            const option = document.createElement('option');
                            option.value = folder.id;
                            option.dataset.prefix = folder.s3_prefix;
                            option.textContent = folder.name;
                            folderSelect.appendChild(option);
                        });
                        
                        // Show folder select container
                        if (folderSelectContainer) folderSelectContainer.style.display = 'block';
                    }
                } else {
                    // Show no results message
                    if (noResultsMessage) {
                        noResultsMessage.style.display = 'block';
                        noResultsMessage.textContent = data.error || 'No videos found matching the criteria.';
                    }
                }
            })
            .catch(error => {
                console.error('Error retrieving videos:', error);
                // Hide loading spinner
                if (loadingSpinner) loadingSpinner.style.display = 'none';
                
                // Show error message
                if (noResultsMessage) {
                    noResultsMessage.style.display = 'block';
                    noResultsMessage.textContent = 'Error retrieving videos. Please try again.';
                }
            });
        });
    }
    
    // Handle folder selection
    if (folderSelect) {
        folderSelect.addEventListener('change', function() {
            const selectedId = this.value;
            if (!selectedId) {
                // No folder selected, hide video list
                if (videoListContainer) videoListContainer.style.display = 'none';
                selectedFolder = null;
                return;
            }
            
            // Find the selected folder data
            selectedFolder = retrievedFolders.find(folder => folder.id.toString() === selectedId);
            
            if (selectedFolder && videoList) {
                // Clear existing video list
                videoList.innerHTML = '';
                
                // Populate video list
                if (selectedFolder.videos && selectedFolder.videos.length > 0) {
                    selectedFolder.videos.forEach(video => {
                        const item = document.createElement('div');
                        item.className = 'form-check mb-2';
                        
                        const input = document.createElement('input');
                        input.className = 'form-check-input';
                        input.type = 'checkbox';
                        input.name = 'selected_videos[]';
                        input.value = video;
                        input.id = `video-${video.replace(/\./g, '-')}`;
                        
                        const label = document.createElement('label');
                        label.className = 'form-check-label';
                        label.htmlFor = input.id;
                        label.textContent = video;
                        
                        item.appendChild(input);
                        item.appendChild(label);
                        videoList.appendChild(item);
                    });
                    
                    // Show video list container and process button
                    if (videoListContainer) videoListContainer.style.display = 'block';
                    if (processBtn) processBtn.style.display = 'block';
                } else {
                    // No videos in the selected folder
                    const message = document.createElement('p');
                    message.textContent = 'No videos found in this folder.';
                    videoList.appendChild(message);
                    
                    // Show video list container but hide process button
                    if (videoListContainer) videoListContainer.style.display = 'block';
                    if (processBtn) processBtn.style.display = 'none';
                }
            }
        });
    }
    
    // Handle process button click
    if (processBtn) {
        processBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Get selected videos
            const selectedVideos = Array.from(document.querySelectorAll('input[name="selected_videos[]"]:checked')).map(input => input.value);
            
            if (selectedVideos.length === 0) {
                alert('Please select at least one video to process.');
                return;
            }
            
            if (!selectedFolder) {
                alert('Please select a folder first.');
                return;
            }
            
            // Show loading spinner
            if (loadingSpinner) loadingSpinner.style.display = 'block';
            
            // Create form data for processing
            const formData = new FormData();
            formData.append('folder_id', selectedFolder.id);
            formData.append('folder_name', selectedFolder.name);
            formData.append('s3_prefix', selectedFolder.s3_prefix);
            
            // Append each selected video
            selectedVideos.forEach(video => {
                formData.append('selected_videos[]', video);
            });
            
                        // Get processing status element            const processingStatus = document.getElementById('processingStatus');                        // Send request to process videos            fetch('/process_videos', {                method: 'POST',                body: formData            })            .then(response => response.json())            .then(data => {                // Hide loading spinner                if (loadingSpinner) loadingSpinner.style.display = 'none';                                if (data.success) {                    // Hide form sections and show processing status                    if (folderSelectContainer) folderSelectContainer.style.display = 'none';                    if (videoListContainer) videoListContainer.style.display = 'none';                    if (processingStatus) processingStatus.style.display = 'block';                                        // Log the details for verification                    console.log(`Processing started for ${data.processed_videos.length} videos`);                    data.processed_videos.forEach(video => {                        console.log(`- ${video.name}: ${video.status}`);                    });                } else {                    alert(`Error: ${data.error || 'Failed to process videos.'}`);                }            })            .catch(error => {                console.error('Error processing videos:', error);                                // Hide loading spinner                if (loadingSpinner) loadingSpinner.style.display = 'none';                                alert('Error processing videos. Please try again.');            });
        });
    }
}); 