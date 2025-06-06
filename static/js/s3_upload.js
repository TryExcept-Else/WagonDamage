document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('videoFile');
    const filePreview = document.getElementById('filePreview');
    const uploadPrompt = document.getElementById('uploadPrompt');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const removeFileBtn = document.getElementById('removeFile');
    const uploadBtn = document.getElementById('uploadBtn');
    const uploadForm = document.getElementById('uploadForm');
    const uploadProgress = document.getElementById('uploadProgress');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const videoWarning = document.getElementById('videoWarning');
    const uploadDate = document.getElementById('uploadDate');
    
    // Set default date to today
    if (uploadDate) {
        const today = new Date();
        // Format date as YYYY-MM-DD for the date input
        const formattedDate = today.getFullYear() + '-' + 
            String(today.getMonth() + 1).padStart(2, '0') + '-' + 
            String(today.getDate()).padStart(2, '0');
        uploadDate.value = formattedDate;
    }
    
    // Allowed file types
    const allowedTypes = [
        'video/mp4', 
        'video/x-msvideo', 
        'video/quicktime', 
        'video/x-ms-wmv',
        'video/x-flv', 
        'video/x-matroska', 
        'video/webm', 
        'video/3gpp',
        'video/x-m4v'
    ];
    
    // Format file size
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    // Handle file selection
    function handleFile(file) {
        // Check if file is a video
        if (!allowedTypes.includes(file.type)) {
            alert('Please select a valid video file (MP4, AVI, MOV, WMV, FLV, MKV, WEBM, 3GP, M4V)');
            return;
        }
        
        // Update file preview
        fileName.textContent = file.name;
        fileSize.textContent = formatFileSize(file.size);
        
        // Show file preview and hide upload prompt
        uploadPrompt.classList.add('d-none');
        filePreview.classList.remove('d-none');
        
        // Enable upload button (and show warning if element exists)
        if (videoWarning) {
            videoWarning.classList.remove('d-none');
        }
        uploadBtn.disabled = false;
    }
    
    // File input change event
    fileInput.addEventListener('change', function() {
        if (this.files.length > 0) {
            handleFile(this.files[0]);
        }
    });
    
    // Drag and drop functionality
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, function(e) {
            e.preventDefault();
            e.stopPropagation();
        }, false);
    });
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, function() {
            this.classList.add('dragover');
        }, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, function() {
            this.classList.remove('dragover');
        }, false);
    });
    
    dropZone.addEventListener('drop', function(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            fileInput.files = files;
            handleFile(files[0]);
        }
    });
    
    // Click on drop zone selects file
    dropZone.addEventListener('click', function(e) {
        // Only trigger file input if clicking on the drop zone itself or the upload prompt
        // Don't trigger when clicking on the file preview or its children
        if (!filePreview.contains(e.target) || filePreview.classList.contains('d-none')) {
            fileInput.click();
        }
    });
    
    // Remove file button
    removeFileBtn.addEventListener('click', function(e) {
        e.stopPropagation(); // Prevent the click from bubbling to the dropZone
        fileInput.value = '';
        
        // Hide file preview and show upload prompt
        filePreview.classList.add('d-none');
        uploadPrompt.classList.remove('d-none');
        
        // Hide warning if it exists and disable upload button
        if (videoWarning) {
            videoWarning.classList.add('d-none');
        }
        uploadBtn.disabled = true;
    });
    
    // Form submission - simulated upload
    uploadForm.addEventListener('submit', function(e) {
        if (fileInput.files.length === 0) {
            return; // Don't proceed if no file
        }
        
        // For demonstration purposes only - simulated upload progress
        // In production, this would use XHR or fetch to track real upload progress
        
        // Display progress bar
        uploadProgress.classList.remove('d-none');
        uploadBtn.disabled = true;
        
        // Simulate progress updates
        let progress = 0;
        const interval = setInterval(function() {
            progress += 5;
            progressBar.style.width = progress + '%';
            progressText.textContent = progress + '%';
            
            if (progress >= 100) {
                clearInterval(interval);
                // The real form submission continues
            }
        }, 300);
        
        // Let the form submit normally after simulated progress
        // In production, you would use fetch or XHR for AJAX upload
    });
}); 