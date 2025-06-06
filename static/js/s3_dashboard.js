document.addEventListener('DOMContentLoaded', function() {
    // Add animation to dashboard cards
    const dashboardCards = document.querySelectorAll('.dashboard-card');
    
    dashboardCards.forEach((card, index) => {
        // Add delayed fade-in animation
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        
        setTimeout(() => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 100 * (index + 1)); // Staggered animation
    });

    // Add active class to current nav link
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        const linkPath = link.getAttribute('href');
        if (linkPath && currentPath.includes(linkPath) && linkPath !== '/') {
            link.classList.add('active');
        }
    });

    // Check system status and show appropriate indicators
    const systemStatusElements = document.querySelectorAll('h3');
    systemStatusElements.forEach(element => {
        if (element.closest('.card-body') && 
            element.previousElementSibling && 
            element.previousElementSibling.textContent.includes('System Status')) {
            
            if (element.textContent.includes('Online')) {
                element.classList.add('text-success');
            } else if (element.textContent.includes('Offline')) {
                element.classList.add('text-danger');
            }
        }
    });

    // Add tooltips to buttons and icons (if Bootstrap is used)
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}); 