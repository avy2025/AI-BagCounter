document.addEventListener('DOMContentLoaded', () => {
    const grid = document.getElementById('scenarios-grid');
    const streamArea = document.getElementById('streaming-area');
    const videoStream = document.getElementById('videoStream');
    const scenarioTitle = document.getElementById('current-scenario-title');
    let countInterval = null;

    async function init() {
        try {
            const resp = await fetch('/api/scenarios');
            const scenarios = await resp.json();
            renderScenarios(scenarios);
        } catch (err) {
            grid.innerHTML = `<p class="error">Failed to load scenarios. Ensure backend is running.</p>`;
        }
    }

    function renderScenarios(scenarios) {
        grid.innerHTML = '';
        scenarios.forEach(s => {
            const card = document.createElement('div');
            card.className = 'scenario-card';
            card.innerHTML = `
                <h3>${s.title}</h3>
                <p>${s.video}</p>
                <button class="btn-process" onclick="startScenario('${s.id}', '${s.title}')">Start Analysis</button>
            `;
            grid.appendChild(card);
        });
    }

    window.startScenario = (id, title) => {
        // Toggle UI
        grid.classList.add('hidden');
        streamArea.classList.remove('hidden');
        scenarioTitle.innerText = `Analyzing: ${title}`;

        // Start Video Stream with cache-buster
        videoStream.src = `/video_feed/${id}?t=${Date.now()}`;

        // Start polling counts
        startCountingPolling();
    };

    window.stopStream = () => {
        // Stop stream by clearing src
        videoStream.src = '';

        // Toggle UI back
        streamArea.classList.add('hidden');
        grid.classList.remove('hidden');

        // Stop polling
        if (countInterval) clearInterval(countInterval);
    };

    function startCountingPolling() {
        if (countInterval) clearInterval(countInterval);

        countInterval = setInterval(async () => {
            try {
                const resp = await fetch('/api/counts');
                const counts = await resp.json();

                document.getElementById('count-in').innerText = counts.in;
                document.getElementById('count-out').innerText = counts.out;
                document.getElementById('count-total').innerText = counts.total;
            } catch (err) {
                console.error("Failed to poll counts");
            }
        }, 1000);
    }

    init();
});
