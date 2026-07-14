let allJobs = [];

document.addEventListener('DOMContentLoaded', () => {
    fetchJobs();

    const searchInput = document.getElementById('search-input');
    const locationInput = document.getElementById('location-input');
    const resetBtn = document.getElementById('reset-btn');

    searchInput.addEventListener('input', renderJobs);
    locationInput.addEventListener('input', renderJobs);
    
    resetBtn.addEventListener('click', () => {
        searchInput.value = '';
        locationInput.value = '';
        renderJobs();
    });
});

async function fetchJobs() {
    try {
        // Fetch from the API. When running locally via Nginx, /api/jobs will proxy to the backend.
        // For testing without Nginx, we point to localhost:8000
        const apiUrl = '/api/jobs?limit=100';

        const res = await fetch(apiUrl);
        const data = await res.json();
        
        allJobs = data.jobs || [];
        
        document.getElementById('total-stat').textContent = data.total || allJobs.length;
        document.getElementById('tab-count').textContent = data.total || allJobs.length;
        
        renderJobs();
    } catch (err) {
        console.error('Failed to fetch jobs', err);
        document.getElementById('job-list').innerHTML = `<div class="loading" style="color:#ef4444">Помилка завантаження даних. Переконайтеся, що API працює.</div>`;
    }
}

function renderJobs() {
    const list = document.getElementById('job-list');
    const searchQuery = document.getElementById('search-input').value.toLowerCase();
    const locQuery = document.getElementById('location-input').value.toLowerCase();

    const filtered = allJobs.filter(job => {
        const textMatch = (job.title + " " + job.company).toLowerCase().includes(searchQuery);
        const locMatch = (job.location || "").toLowerCase().includes(locQuery);
        return textMatch && locMatch;
    });

    document.getElementById('filtered-count').textContent = filtered.length;

    if (filtered.length === 0) {
        list.innerHTML = `<div class="loading">Вакансій не знайдено 😔</div>`;
        return;
    }

    list.innerHTML = filtered.map(job => {
        const companyInitial = job.company ? job.company.charAt(0).toUpperCase() : 'C';
        // Date formatting
        let dateStr = job.date_posted || '';
        
        return `
            <a href="${job.job_link}" target="_blank" class="job-card">
                <div class="job-avatar">${companyInitial}</div>
                <div class="job-details">
                    <div class="job-title-row">
                        <div class="job-title">${job.title}</div>
                        <div class="job-date">${dateStr}</div>
                    </div>
                    <div class="job-meta">
                        <span>📍 ${job.location || 'Невідомо'}</span>
                        <span>•</span>
                        <span>🏢 ${job.company}</span>
                    </div>
                    <div class="job-desc">${job.description || ''}</div>
                </div>
            </a>
        `;
    }).join('');
}
