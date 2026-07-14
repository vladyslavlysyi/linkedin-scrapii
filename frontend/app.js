let currentTab = 'people';
let allData = {
    people: [],
    jobs: []
};
let totals = {
    people: 0,
    jobs: 0
};

document.addEventListener('DOMContentLoaded', () => {
    // Initial fetch
    fetchData('people');
    fetchData('jobs');

    // UI Elements
    const searchInput = document.getElementById('search-input');
    const locationInput = document.getElementById('location-input');
    const resetBtn = document.getElementById('reset-btn');
    const tabs = document.querySelectorAll('.nav-tab');

    // Event Listeners
    searchInput.addEventListener('input', renderList);
    locationInput.addEventListener('input', renderList);
    
    resetBtn.addEventListener('click', () => {
        searchInput.value = '';
        locationInput.value = '';
        renderList();
    });

    tabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            tabs.forEach(t => t.classList.remove('active'));
            e.currentTarget.classList.add('active');
            
            currentTab = e.currentTarget.getAttribute('data-tab');
            
            const titleEl = document.getElementById('section-title');
            titleEl.textContent = currentTab === 'people' ? 'Список Кандидатів' : 'Список Вакансій';
            
            updateTotalStat();
            renderList();
        });
    });
});

async function fetchData(type) {
    try {
        const apiUrl = `/api/${type}?limit=100`;
        const res = await fetch(apiUrl);
        const data = await res.json();
        
        allData[type] = data[type] || [];
        totals[type] = data.total || allData[type].length;
        
        if (currentTab === type) {
            updateTotalStat();
            renderList();
        }
    } catch (err) {
        console.error(`Failed to fetch ${type}`, err);
        if (currentTab === type) {
            document.getElementById('list-container').innerHTML = `
                <div class="loading-state" style="color:#ef4444">
                    Помилка завантаження. API недоступне.
                </div>`;
        }
    }
}

function updateTotalStat() {
    const totalEl = document.getElementById('total-stat');
    
    // Create an animation effect for the number
    let currentVal = parseInt(totalEl.textContent) || 0;
    const targetVal = totals[currentTab] || 0;
    
    if (currentVal === targetVal) {
        totalEl.textContent = targetVal;
        return;
    }
    
    const duration = 500;
    const frames = 20;
    const step = (targetVal - currentVal) / frames;
    let frame = 0;
    
    const timer = setInterval(() => {
        frame++;
        currentVal += step;
        totalEl.textContent = Math.round(currentVal);
        
        if (frame >= frames) {
            clearInterval(timer);
            totalEl.textContent = targetVal;
        }
    }, duration / frames);
}

function renderList() {
    const list = document.getElementById('list-container');
    const searchQuery = document.getElementById('search-input').value.toLowerCase();
    const locQuery = document.getElementById('location-input').value.toLowerCase();
    
    const currentList = allData[currentTab];

    const filtered = currentList.filter(item => {
        let textMatch = false;
        let locMatch = false;
        
        if (currentTab === 'people') {
            textMatch = (item.name + " " + (item.headline || "") + " " + (item.snippet || "")).toLowerCase().includes(searchQuery);
            locMatch = (item.location || "").toLowerCase().includes(locQuery);
        } else {
            textMatch = (item.title + " " + item.company).toLowerCase().includes(searchQuery);
            locMatch = (item.location || "").toLowerCase().includes(locQuery);
        }
        
        return textMatch && locMatch;
    });

    document.getElementById('filtered-count').textContent = filtered.length;

    if (filtered.length === 0) {
        list.innerHTML = `
            <div class="loading-state">
                <p>Нічого не знайдено за вашим запитом 😔</p>
            </div>`;
        return;
    }

    list.innerHTML = filtered.map(item => {
        if (currentTab === 'people') {
            const initial = item.name ? item.name.charAt(0).toUpperCase() : '👤';
            return `
                <a href="${item.profile_link}" target="_blank" class="result-card">
                    <div class="card-avatar">${initial}</div>
                    <div class="card-details">
                        <div class="card-title-row">
                            <div class="card-title">${item.name}</div>
                        </div>
                        <div class="card-meta">
                            <span>📍 ${item.location || 'Не вказано'}</span>
                            <span>•</span>
                            <span>💼 ${item.headline || ''}</span>
                        </div>
                        <div class="card-desc">${item.snippet || ''}</div>
                    </div>
                </a>
            `;
        } else {
            const initial = item.company ? item.company.charAt(0).toUpperCase() : 'C';
            return `
                <a href="${item.job_link}" target="_blank" class="result-card">
                    <div class="card-avatar job-avatar">${initial}</div>
                    <div class="card-details">
                        <div class="card-title-row">
                            <div class="card-title">${item.title}</div>
                            <div class="card-date">${item.date_posted || ''}</div>
                        </div>
                        <div class="card-meta">
                            <span>📍 ${item.location || 'Невідомо'}</span>
                            <span>•</span>
                            <span>🏢 ${item.company}</span>
                        </div>
                        <div class="card-desc">${item.description || ''}</div>
                    </div>
                </a>
            `;
        }
    }).join('');
}
