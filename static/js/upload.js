document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('fileInput');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const uploadInitial = document.getElementById('uploadInitial');
    const uploadPreview = document.getElementById('uploadPreview');
    const uploadProgress = document.getElementById('uploadProgress');
    const uploadSuccess = document.getElementById('uploadSuccess');
    const removeFileBtn = document.getElementById('removeFileBtn');
    const uploadBtn = document.getElementById('uploadBtn');
    const progressBar = document.getElementById('progressBar');
    const uploadedSize = document.getElementById('uploadedSize');
    const uploadSpeed = document.getElementById('uploadSpeed');
    const timeRemaining = document.getElementById('timeRemaining');
    const cancelUploadBtn = document.getElementById('cancelUploadBtn');
    const uploadContainer = document.getElementById('uploadContainer');
    const uploadForm = document.getElementById('uploadForm');
    
    // Format bytes to human-readable size
    function formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }
    
    // Handle file selection
    fileInput.addEventListener('change', function() {
        if (this.files.length > 0) {
            const file = this.files[0];
            fileName.textContent = file.name;
            fileSize.textContent = formatBytes(file.size);
            
            uploadInitial.style.display = 'none';
            uploadPreview.style.display = 'block';
        }
    });
    
    // Remove selected file
    if (removeFileBtn) {
        removeFileBtn.addEventListener('click', function() {
            uploadForm.reset();
            uploadPreview.style.display = 'none';
            uploadInitial.style.display = 'block';
        });
    }
    
    // Handle upload button click
    if (uploadBtn) {
        uploadBtn.addEventListener('click', function() {
            uploadPreview.style.display = 'none';
            uploadProgress.style.display = 'block';
            
            // Simulate upload progress (for demo purposes)
            let progress = 0;
            const interval = setInterval(function() {
                progress += Math.random() * 10;
                if (progress > 100) progress = 100;
                
                progressBar.style.width = progress + '%';
                progressBar.textContent = Math.round(progress) + '%';
                progressBar.setAttribute('aria-valuenow', Math.round(progress));
                
                // Update stats (simulated)
                const totalSize = fileInput.files[0] ? fileInput.files[0].size : 100 * 1024 * 1024;
                const uploadedBytes = totalSize * (progress / 100);
                uploadedSize.textContent = formatBytes(uploadedBytes) + ' / ' + formatBytes(totalSize);
                uploadSpeed.textContent = formatBytes(uploadedBytes / 10) + '/s';
                
                const remainingSeconds = (100 - progress) / 10;
                if (remainingSeconds > 60) {
                    timeRemaining.textContent = Math.round(remainingSeconds / 60) + ' min remaining';
                } else {
                    timeRemaining.textContent = Math.round(remainingSeconds) + ' sec remaining';
                }
                
                if (progress >= 100) {
                    clearInterval(interval);
                    
                    // Show success after a small delay
                    setTimeout(function() {
                        uploadProgress.style.display = 'none';
                        uploadSuccess.style.display = 'block';
                    }, 500);
                }
            }, 1000);
            
            // Handle cancel upload
            cancelUploadBtn.addEventListener('click', function() {
                clearInterval(interval);
                uploadProgress.style.display = 'none';
                uploadPreview.style.display = 'block';
            });
        });
    }
    
    // Drag and drop functionality
    if (uploadInitial) {
        uploadInitial.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.classList.add('drag-highlight');
        });
        
        uploadInitial.addEventListener('dragleave', function(e) {
            e.preventDefault();
            this.classList.remove('drag-highlight');
        });
        
        uploadInitial.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('drag-highlight');
            
            if (e.dataTransfer.files.length > 0) {
                fileInput.files = e.dataTransfer.files;
                
                // Trigger change event
                const event = new Event('change');
                fileInput.dispatchEvent(event);
            }
        });
    }
}); 