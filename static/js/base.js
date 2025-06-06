// Base functionality for all pages
document.addEventListener('DOMContentLoaded', function() {
    // Logout button functionality
    const logoutBtn = document.getElementById('logoutBtn');
    const logoutModal = document.getElementById('logoutModal');
    const modalBackdrop = document.getElementById('modalBackdrop');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const cancelLogoutBtn = document.getElementById('cancelLogoutBtn');
    
    if (logoutBtn && logoutModal && modalBackdrop) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Display modal
            logoutModal.style.display = 'flex';
            modalBackdrop.style.display = 'block';
            
            // Add show classes for animation
            setTimeout(function() {
                modalBackdrop.classList.add('show');
                logoutModal.classList.add('show');
            }, 10);
        });
        
        function closeModal() {
            modalBackdrop.classList.remove('show');
            logoutModal.classList.remove('show');
            
            setTimeout(function() {
                modalBackdrop.style.display = 'none';
                logoutModal.style.display = 'none';
            }, 300);
        }
        
        if (closeModalBtn) {
            closeModalBtn.addEventListener('click', closeModal);
        }
        
        if (cancelLogoutBtn) {
            cancelLogoutBtn.addEventListener('click', closeModal);
        }
        
        // Close modal when clicking outside
        modalBackdrop.addEventListener('click', closeModal);
        
        // Prevent modal close when clicking inside the modal content
        logoutModal.querySelector('.modal-content').addEventListener('click', function(e) {
            e.stopPropagation();
        });
    }
    
    // Auto dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // Enable tooltips everywhere
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Enable popovers everywhere
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Add active class to current nav item
    const currentLocation = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentLocation) {
            link.classList.add('active');
        }
    });
}); 