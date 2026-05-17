// charts.js - Logic for data visualization components

document.addEventListener('DOMContentLoaded', () => {
    
    // 1. Initialize Bar Chart
    const barChartContainer = document.getElementById('bar-chart-bars');
    if (barChartContainer) {
        const barData = [
            { label: 'Mon', value: 45 },
            { label: 'Tue', value: 75 },
            { label: 'Wed', value: 50 },
            { label: 'Thu', value: 90 },
            { label: 'Fri', value: 65 },
            { label: 'Sat', value: 100 },
            { label: 'Sun', value: 30 }
        ];

        barData.forEach((data, index) => {
            const wrapper = document.createElement('div');
            wrapper.className = 'bar-wrapper';

            const bar = document.createElement('div');
            bar.className = 'bar';
            // Start at 0 for animation
            bar.style.height = '0%';
            
            // Set final height after a short delay for animation
            setTimeout(() => {
                bar.style.height = `${data.value}%`;
            }, 100 + (index * 50));

            const tooltip = document.createElement('div');
            tooltip.className = 'bar-tooltip';
            tooltip.innerText = `${data.value} users`;

            const label = document.createElement('div');
            label.className = 'bar-label';
            label.innerText = data.label;

            bar.appendChild(tooltip);
            wrapper.appendChild(bar);
            wrapper.appendChild(label);
            barChartContainer.appendChild(wrapper);
        });
    }

    // 2. Initialize Heatmap Activity Tracker
    const heatmapContainer = document.getElementById('heatmap-grid');
    if (heatmapContainer) {
        // Generate 36 random cells for the last month
        for(let i = 0; i < 36; i++) {
            const cell = document.createElement('div');
            cell.className = 'heatmap-cell';
            
            // Random level 0-4
            const level = Math.random() > 0.3 ? Math.floor(Math.random() * 5) : 0;
            if (level > 0) {
                cell.setAttribute('data-level', level);
            }
            
            // Tooltip for cell
            cell.title = `Activity level: ${level}`;
            heatmapContainer.appendChild(cell);
        }
    }

    // 3. SVG Line Chart Points Interactions
    const points = document.querySelectorAll('.svg-point');
    points.forEach(point => {
        point.addEventListener('mouseenter', (e) => {
            // Optional: Create a custom tooltip element floating near the mouse
            const val = e.target.getAttribute('data-value');
            // For simplicity, we just rely on the built-in title if added, or we could create a custom div.
        });
    });
});

// Helper for copy code buttons
function toggleCode(id) {
    const el = document.getElementById(id);
    if(el) el.classList.toggle('show');
}

function copyCode(previewId, btnElement) {
    const preview = document.getElementById(previewId);
    if (!preview) return;

    const htmlToCopy = preview.innerHTML.trim();
    
    navigator.clipboard.writeText(htmlToCopy).then(() => {
        const originalText = btnElement.innerHTML;
        btnElement.innerHTML = '<i class="fa-solid fa-check"></i> Copied!';
        btnElement.style.color = '#10b981';
        setTimeout(() => {
            btnElement.innerHTML = originalText;
            btnElement.style.color = '';
        }, 2000);
    });
}
