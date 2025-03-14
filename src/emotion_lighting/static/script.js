// Emotion Lighting System - Frontend JavaScript
document.addEventListener('DOMContentLoaded', function () {
    // ----- ELEMENT REFERENCES -----
    const elements = {
        emotionFace: document.getElementById('emotion-face'),
        emotionName: document.getElementById('emotion-name'),
        touchCount: document.getElementById('touch-count'),
        touchContainer: document.getElementById('touch-container'),
        totalEmotions: document.getElementById('total-emotions'),
        dominantEmotion: document.getElementById('dominant-emotion'),
        totalTouches: document.getElementById('total-touches'),
        totalAvgDuration: document.getElementById('total-avg-duration'),
        totalTouchDuration: document.getElementById('total-touch-duration'),
        systemTime: document.getElementById('system-time'),
    };

    // ----- EMOTION CONFIGURATION -----
    const EMOTION_CONFIG = {
        "happy": {
            "color": "#FFFF00", // Yellow
            "mouthCurve": 0.5   // Smile
        },
        "sad": {
            "color": "#0000FF", // Blue
            "mouthCurve": -0.5  // Frown
        },
        "angry": {
            "color": "#FF0000", // Red
            "mouthCurve": -0.2  // Slight frown with bent
        },
        "neutral": {
            "color": "#FFFFFF", // White
            "mouthCurve": 0.0   // Straight line
        },
        "fear": {
            "color": "#800080", // Purple
            "mouthCurve": -0.3  // Slight wary frown
        },
        "surprise": {
            "color": "#00FFFF", // Cyan
            "mouthCurve": 0.0,  // Straight line
            "mouthOpen": true   // Open mouth
        },
        "disgust": {
            "color": "#008000", // Green
            "mouthCurve": -0.3  // Frown with bent
        }
    };

    // All emotions to display in chart - ensure these match backend
    const CHART_EMOTIONS = ["happy", "sad", "angry", "neutral", "fear", "surprise"];

    // Chart reference
    let emotionChart = null;

    // ----- CHART INITIALIZATION -----
    function initEmotionChart() {
        const ctx = document.getElementById('emotion-chart').getContext('2d');
        const chartConfig = {
            type: 'bar',
            data: {
                labels: CHART_EMOTIONS.map(e => e.substring(0, 3).toUpperCase()),
                datasets: [{
                    label: 'Emotion Count',
                    data: CHART_EMOTIONS.map(() => 0),
                    backgroundColor: '#333333',
                    borderColor: '#444444',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: '#222222' },
                        ticks: { color: '#AAAAAA' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#FFFFFF' }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        };

        emotionChart = new Chart(ctx, chartConfig);
    }

    // ----- SVG FACE DRAWING -----
    function drawEmotionFace(emotion) {
        const emotionData = EMOTION_CONFIG[emotion] || EMOTION_CONFIG["neutral"];
        const size = 140;
        const radius = size / 2;

        // Create SVG element
        const svg = createSvgElement("svg", {
            width: size,
            height: size,
            viewBox: `0 0 ${size} ${size}`
        });

        // Create face circle
        const circle = createSvgElement("circle", {
            cx: radius,
            cy: radius,
            r: radius - 5,
            fill: emotionData.color
        });
        svg.appendChild(circle);

        // Eye parameters
        const eyeOffsetX = radius * 0.4;
        const eyeOffsetY = radius * 0.3;
        const eyeRadius = radius * 0.12;

        // Add eyes
        svg.appendChild(createEye(radius - eyeOffsetX, radius - eyeOffsetY, eyeRadius));
        svg.appendChild(createEye(radius + eyeOffsetX, radius - eyeOffsetY, eyeRadius));

        // Add mouth based on emotion
        svg.appendChild(createMouth(emotionData, radius, radius + radius * 0.2));

        // Replace any existing face
        elements.emotionFace.innerHTML = '';
        elements.emotionFace.appendChild(svg);
    }

    // Helper function to create SVG elements
    function createSvgElement(name, attributes) {
        const element = document.createElementNS("http://www.w3.org/2000/svg", name);
        for (const [key, value] of Object.entries(attributes)) {
            element.setAttribute(key, value);
        }
        return element;
    }

    // Create an eye SVG element
    function createEye(cx, cy, radius) {
        return createSvgElement("circle", {
            cx: cx,
            cy: cy,
            r: radius,
            fill: "#000000"
        });
    }

    // Create mouth based on emotion data
    function createMouth(emotionData, centerX, mouthY) {
        const mouthWidth = centerX;

        if (emotionData.mouthOpen) {
            return createSvgElement("circle", {
                cx: centerX,
                cy: mouthY,
                r: centerX * 0.15,
                fill: "#000000"
            });
        } else if (emotionData.mouthCurve === 0) {
            return createSvgElement("line", {
                x1: centerX - mouthWidth / 2,
                y1: mouthY,
                x2: centerX + mouthWidth / 2,
                y2: mouthY,
                stroke: "#000000",
                "stroke-width": "4"
            });
        } else {
            const curveHeight = 20 * emotionData.mouthCurve;
            return createSvgElement("path", {
                d: `M ${centerX - mouthWidth / 2} ${mouthY} Q ${centerX} ${mouthY + curveHeight}, ${centerX + mouthWidth / 2} ${mouthY}`,
                fill: "none",
                stroke: "#000000",
                "stroke-width": "4"
            });
        }
    }

    // ----- UI UPDATES -----
    function updateUI(data) {
        // Update emotion face and name
        drawEmotionFace(data.emotion.current);
        elements.emotionName.textContent = data.emotion.current.toUpperCase();

        // Update touch data
        updateTouchInfo(data.touch);

        // Update statistics
        updateStatistics(data.total_stats);

        // Update system time
        elements.systemTime.textContent = `SYS: ${data.time}`;

        // Update emotion chart
        updateEmotionChart(data.emotion.counts);
    }

    function updateTouchInfo(touchData) {
        elements.touchCount.textContent = touchData.today_touches;

        if (touchData.active_touches > 0) {
            elements.touchContainer.classList.add('touch-active');
        } else {
            elements.touchContainer.classList.remove('touch-active');
        }
    }

    function updateStatistics(stats) {
        if (!stats) return;

        elements.totalEmotions.textContent = stats.total_emotions || 0;
        elements.dominantEmotion.textContent = (stats.dominant_emotion || 'neutral').toUpperCase();
        elements.totalTouches.textContent = stats.total_touches || 0;
        elements.totalAvgDuration.textContent = (stats.avg_touch_duration || 0).toFixed(1) + 's';
        elements.totalTouchDuration.textContent = (stats.total_touch_duration || 0).toFixed(1) + 's';
    }

    function updateEmotionChart(emotionCounts) {
        if (!emotionChart) return;

        CHART_EMOTIONS.forEach((emotion, index) => {
            emotionChart.data.datasets[0].data[index] = emotionCounts[emotion] || 0;
        });
        emotionChart.update();
    }

    // ----- WEBSOCKET CONNECTION -----
    function connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        const socket = new WebSocket(wsUrl);

        socket.onopen = () => {
            console.log('WebSocket connection established');
        };

        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                updateUI(data);
            } catch (error) {
                console.error('Error parsing WebSocket data:', error);
            }
        };

        socket.onclose = () => {
            console.log('WebSocket connection closed. Reconnecting...');
            setTimeout(connectWebSocket, 2000);
        };

        socket.onerror = (error) => {
            console.error('WebSocket error:', error);
            socket.close();
        };
    }

    // ----- INITIALIZATION -----
    function initialize() {
        // Initialize chart
        initEmotionChart();

        // Start WebSocket connection
        connectWebSocket();

        // Set initial face
        drawEmotionFace('neutral');
    }

    // Start the application
    initialize();
});