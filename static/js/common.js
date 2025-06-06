// Common JavaScript functionality shared across multiple pages
document.addEventListener('DOMContentLoaded', function() {
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Form validation for all forms
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
    
    // Handle mobile navigation
    const navbarToggler = document.querySelector('.navbar-toggler');
    
    if (navbarToggler) {
        navbarToggler.addEventListener('click', function() {
            document.body.classList.toggle('navbar-open');
        });
    }
    
    // Handle collapsible sections
    const collapsibleTogglers = document.querySelectorAll('[data-toggle="collapse"]');
    
    collapsibleTogglers.forEach(toggler => {
        toggler.addEventListener('click', function() {
            const target = document.querySelector(this.getAttribute('data-target'));
            if (target) {
                target.classList.toggle('show');
                
                // Toggle icon for common patterns
                const icon = this.querySelector('i.fa-angle-down, i.fa-angle-up');
                if (icon) {
                    icon.classList.toggle('fa-angle-down');
                    icon.classList.toggle('fa-angle-up');
                }
            }
        });
    });
}); 