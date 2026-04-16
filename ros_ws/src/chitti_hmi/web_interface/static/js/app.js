let sessionId = null;
let recorder = null;
let isRecording = false;
let statusPollTimer = null;
let map = null;
let mapConfig = null;
let mapSelectionMarker = null;
let optionsCache = [];
let routeLayer = null;
let robotMarker = null;
let robotTrailLayer = null;
let driveHoldTimer = null;
let activeDriveButton = null;

document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    sessionId = urlParams.get('session_id') || 'unknown';
    document.getElementById('sessionId').textContent = `Session: ${sessionId.substring(0, 8)}...`;

    setupVoiceButton();
    setupManualControls();
    loadDestinationOptions();
    pollNavigationStatus();
    statusPollTimer = setInterval(pollNavigationStatus, 300);
});

function setupVoiceButton() {
    const recordButton = document.getElementById('recordButton');
    recordButton.addEventListener('pointerup', toggleRecording);
}

function setupManualControls() {
    const controlsRoot = document.getElementById('manualControls');
    if (!controlsRoot) {
        return;
    }

    controlsRoot.querySelectorAll('.drive-btn[data-linear]').forEach((button) => {
        button.addEventListener('pointerdown', (event) => {
            event.preventDefault();
            const linear = Number(button.dataset.linear || '0');
            const angular = Number(button.dataset.angular || '0');
            beginDriveHold(button, linear, angular);
        });
    });

    const stopButton = document.getElementById('stopDriveButton');
    if (stopButton) {
        stopButton.addEventListener('pointerup', async (event) => {
            event.preventDefault();
            endDriveHold();
            await sendStopCommand();
            updateStatus('Drive stop command sent.');
        });
    }

    ['pointerup', 'pointercancel', 'pointerleave'].forEach((eventName) => {
        controlsRoot.addEventListener(eventName, endDriveHold);
    });
}

function beginDriveHold(button, linear, angular) {
    endDriveHold();
    activeDriveButton = button;
    button.classList.add('drive-active');

    sendMotionCommand(linear, angular);
    driveHoldTimer = setInterval(() => {
        sendMotionCommand(linear, angular);
    }, 140);
}

function endDriveHold() {
    if (activeDriveButton) {
        activeDriveButton.classList.remove('drive-active');
        activeDriveButton = null;
    }

    if (driveHoldTimer) {
        clearInterval(driveHoldTimer);
        driveHoldTimer = null;
        sendStopCommand();
    }
}

async function sendMotionCommand(linear, angular) {
    const result = await postJson('/api/motion/command', { linear, angular });
    if (!result.ok) {
        updateStatus(result.message || 'Drive command failed.');
    }
}

async function sendStopCommand() {
    const result = await postJson('/api/motion/stop', {});
    if (!result.ok) {
        updateStatus(result.message || 'Stop command failed.');
    }
}

function setupLeafletMap() {
    if (!window.L) {
        updateStatus('Map library failed to load. Check internet connection.');
        return;
    }
    if (!mapConfig) {
        return;
    }

    const mapElement = document.getElementById('iitgnMap');
    if (!mapElement || map) {
        return;
    }

    map = L.map('iitgnMap', {
        zoomControl: false,
        attributionControl: false,
        minZoom: mapConfig.min_zoom || 15,
        maxZoom: mapConfig.max_zoom || 19,
    }).setView([mapConfig.center_lat, mapConfig.center_lon], 16);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
    }).addTo(map);

    const bounds = L.latLngBounds(
        [mapConfig.lat_min, mapConfig.lon_min],
        [mapConfig.lat_max, mapConfig.lon_max]
    );
    map.fitBounds(bounds, { padding: [8, 8] });
    map.setMaxBounds(bounds.pad(0.15));

    L.rectangle(bounds, {
        color: '#2f9e8f',
        weight: 1,
        fillOpacity: 0.03,
    }).addTo(map);

    map.on('click', async (event) => {
        const lat = Number(event.latlng.lat.toFixed(6));
        const lon = Number(event.latlng.lng.toFixed(6));

        if (mapSelectionMarker) {
            map.removeLayer(mapSelectionMarker);
        }
        mapSelectionMarker = L.circleMarker([lat, lon], {
            radius: 8,
            color: '#c9322a',
            fillColor: '#d7342a',
            fillOpacity: 0.9,
        }).addTo(map);

        updateStatus('Planning route to selected IITGN map point...');
        const result = await postJson('/api/navigation/select-latlon', { lat, lon });
        if (!result.ok) {
            updateStatus(result.message || 'Map selection failed.');
            return;
        }
        updateStatus(result.message || 'Destination selected from IITGN map.');
        pollNavigationStatus();
    });

    optionsCache.forEach((option) => {
        L.circleMarker([option.lat, option.lon], {
            radius: 4,
            color: '#1b6f62',
            fillColor: '#2f9e8f',
            fillOpacity: 0.85,
        }).addTo(map).bindTooltip(option.name, { direction: 'top', offset: [0, -2] });
    });
}

async function loadDestinationOptions() {
    try {
        const response = await fetch('/api/options');
        const data = await response.json();
        const container = document.getElementById('destinationOptions');
        container.innerHTML = '';
        mapConfig = data.map || null;
        optionsCache = data.options || [];

        (optionsCache || []).forEach((option) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'option-btn';
            button.textContent = option.name;
            button.addEventListener('pointerup', async (event) => {
                event.preventDefault();
                updateStatus(`Planning route to ${option.name}...`);
                const result = await postJson('/api/navigation/select-option', { location_id: option.id });
                if (!result.ok) {
                    updateStatus(result.message || 'Destination button failed.');
                    return;
                }
                updateStatus(result.message || `Navigation started to ${option.name}.`);
                pollNavigationStatus();
            });
            container.appendChild(button);
        });
        setupLeafletMap();
    } catch (error) {
        console.error('Failed to load options:', error);
        updateStatus('Unable to load destination options.');
    }
}

async function pollNavigationStatus() {
    try {
        const response = await fetch('/api/navigation/status');
        const data = await response.json();
        if (!response.ok) {
            updateStatus(data.message || 'Navigation status unavailable.');
            return;
        }
        if (!data.navigation) {
            return;
        }

        const nav = data.navigation;
        const selectedName = nav.goal && nav.goal.name ? nav.goal.name : '-';
        document.getElementById('selectedDestination').textContent = selectedName;
        document.getElementById('plannedDistance').textContent = formatDistance(nav.planned_distance_m);
        document.getElementById('remainingDistance').textContent = formatDistance(nav.remaining_distance_m);
        document.getElementById('eta').textContent = formatEta(nav.eta_seconds);

        updateMapNavigationLayers(nav);

        if (nav.navigation_active && nav.path_available) {
            updateStatus('Navigation active. Route ready.');
        } else if (nav.navigation_active && !nav.path_available) {
            updateStatus('Navigation active. Waiting for route generation...');
        }
    } catch (error) {
        console.error('Navigation status error:', error);
        updateStatus('Waiting for ROS bridge and navigation status...');
    }
}

function updateMapNavigationLayers(nav) {
    if (!map) {
        return;
    }

    if (routeLayer) {
        map.removeLayer(routeLayer);
        routeLayer = null;
    }

    if (Array.isArray(nav.path_points) && nav.path_points.length >= 2) {
        const latlngs = nav.path_points.map((p) => [p.lat, p.lon]);
        routeLayer = L.polyline(latlngs, {
            color: '#1b6f62',
            weight: 4,
            opacity: 0.9,
        }).addTo(map);
    }

    if (nav.robot_position && Number.isFinite(nav.robot_position.lat) && Number.isFinite(nav.robot_position.lon)) {
        const latlng = [nav.robot_position.lat, nav.robot_position.lon];
        if (!robotMarker) {
            robotMarker = L.circleMarker(latlng, {
                radius: 7,
                color: '#104f9e',
                fillColor: '#2b7dd4',
                fillOpacity: 0.95,
                weight: 2,
            }).addTo(map);
        } else {
            robotMarker.setLatLng(latlng);
        }
    }

    if (robotTrailLayer) {
        map.removeLayer(robotTrailLayer);
        robotTrailLayer = null;
    }
    if (Array.isArray(nav.robot_history) && nav.robot_history.length >= 2) {
        const trail = nav.robot_history.map((p) => [p.lat, p.lon]);
        robotTrailLayer = L.polyline(trail, {
            color: '#2b7dd4',
            weight: 2,
            opacity: 0.55,
            dashArray: '5,5',
        }).addTo(map);
    }
}

function formatDistance(value) {
    if (value === null || value === undefined) {
        return '-';
    }
    if (value >= 1000) {
        return `${(value / 1000).toFixed(2)} km`;
    }
    return `${value.toFixed(1)} m`;
}

function formatEta(seconds) {
    if (seconds === null || seconds === undefined) {
        return '-';
    }
    if (seconds < 60) {
        return `${Math.max(1, Math.round(seconds))} sec`;
    }
    return `${Math.ceil(seconds / 60)} min`;
}

function startRecording() {
    if (isRecording) {
        return;
    }
    recorder = new AudioRecorder();
    recorder.start();
    isRecording = true;

    const button = document.getElementById('recordButton');
    const micLabel = document.getElementById('micLabel');
    button.classList.add('recording');
    micLabel.textContent = 'Stop Mic';
    updateStatus('Recording started. Tap again to send.');
}

function stopRecording() {
    if (!isRecording || !recorder) {
        return;
    }

    recorder.stop().then((audioBlob) => {
        isRecording = false;
        const button = document.getElementById('recordButton');
        const micLabel = document.getElementById('micLabel');
        button.classList.remove('recording');
        micLabel.textContent = 'Start Mic';
        updateStatus('Processing voice input...');

        const formData = new FormData();
        formData.append('audio', audioBlob, 'audio.webm');
        formData.append('session_id', sessionId);

        fetch('/api/voice', {
            method: 'POST',
            body: formData
        })
            .then((response) => response.json())
            .then((result) => {
                if (result.status === 'success') {
                    document.getElementById('transcription').innerHTML = '<p>Voice clip sent successfully.</p>';
                    updateStatus('Voice sent.');
                } else {
                    updateStatus(result.message || 'Voice upload failed.');
                }
            })
            .catch((error) => {
                console.error('Voice upload error:', error);
                updateStatus('Error sending audio.');
            });
    });
}

function toggleRecording() {
    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
}

async function postJson(url, payload) {
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        return {
            ok: response.ok && data.status !== 'error',
            message: data.message || null,
            data
        };
    } catch (error) {
        console.error(`POST ${url} failed:`, error);
        return { ok: false, message: 'Network error' };
    }
}

function updateStatus(message) {
    document.getElementById('status').textContent = message;
}
