document.addEventListener('DOMContentLoaded', function() {
    // Toggle filter section
    const toggleFiltersBtn = document.getElementById('toggleFiltersBtn');
    const filtersBody = document.getElementById('filtersBody');
    
    if (toggleFiltersBtn && filtersBody) {
        toggleFiltersBtn.addEventListener('click', function() {
            if (filtersBody.style.display === 'none') {
                filtersBody.style.display = 'block';
                toggleFiltersBtn.querySelector('i').classList.remove('fa-angle-down');
                toggleFiltersBtn.querySelector('i').classList.add('fa-angle-up');
            } else {
                filtersBody.style.display = 'none';
                toggleFiltersBtn.querySelector('i').classList.remove('fa-angle-up');
                toggleFiltersBtn.querySelector('i').classList.add('fa-angle-down');
            }
        });
    }
    
    // Chart.js global defaults for better responsiveness
    Chart.defaults.responsive = true;
    Chart.defaults.maintainAspectRatio = false;
    
    // Add message to empty charts
    Chart.defaults.plugins.title.display = true;
    Chart.defaults.plugins.title.font = {
        size: 14
    };
    
    // Check if we have real data before creating charts
    // Initialize damage distribution chart
    const damageCtx = document.getElementById('damageChart');
    if (damageCtx) {
        // Show "No data available" message
        const damageChart = new Chart(damageCtx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'No damage data available yet',
                        position: 'center'
                    },
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
    
    // Initialize damage types pie chart
    const damageTypesCtx = document.getElementById('damageTypesChart');
    if (damageTypesCtx) {
        // Show "No data available" message
        const damageTypesChart = new Chart(damageTypesCtx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'No damage type data available yet',
                        position: 'center'
                    },
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
    
    // Initialize severity chart if exists
    const severityCtx = document.getElementById('severityChart');
    if (severityCtx) {
        // Show "No data available" message
        const severityChart = new Chart(severityCtx, {
            type: 'pie',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'No severity data available yet',
                        position: 'center'
                    },
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
    
    // Initialize location chart if exists
    const locationCtx = document.getElementById('locationChart');
    if (locationCtx) {
        // Show "No data available" message
        const locationChart = new Chart(locationCtx, {
            type: 'pie',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'No location data available yet',
                        position: 'center'
                    },
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
    
    // Handle window resize to redraw charts
    window.addEventListener('resize', function() {
        // Trigger chart resize after window resizes
        setTimeout(function() {
            if (damageChart) damageChart.resize();
            if (damageTypesChart) damageTypesChart.resize();
            if (typeof severityChart !== 'undefined' && severityChart) severityChart.resize();
            if (typeof locationChart !== 'undefined' && locationChart) locationChart.resize();
        }, 100);
    });
}); 