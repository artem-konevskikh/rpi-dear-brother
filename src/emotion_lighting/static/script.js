// Emotion Lighting System - Frontend JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Element references
    const emotionFace = document.getElementById('emotion-face');
    const emotionName = document.getElementById('emotion-name');
    const touchCount = document.getElementById('touch-count');
    const touchContainer = document.getElementById('touch-container');
    // Total stats elements
    const totalEmotions = document.getElementById('total-emotions');
    const dominantEmotion = document.getElementById('dominant-emotion');
    const totalTouches = document.getElementById('total-touches');
    const totalAvgDuration = document.getElementById('total-avg-duration');
    const totalTouchDuration = document.getElementById('total-touch-duration');
    const systemTime = document.getElementById('system-time');
    
    // Emotion data with corresponding colors
    const EMOTION_DATA = {
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
    
    // All emotions to display in chart
    const ALL_EMOTIONS = ["happy", "sad", "angry", "neutral", "fear", "surprise"];
    
    // Create emotion chart
    let emotionChart = null;
    
    function initEmotionChart() {
        const ctx = document.getElementById('emotion-chart').getContext('2d');
        emotionChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ALL_EMOTIONS.map(e => e.substring(0, 3).toUpperCase()),
                datasets: [{
                    label: 'Emotion Count',
                    data: ALL_EMOTIONS.map(() => 0),
                    backgroundColor: '#333333',
                    borderColor: '#444444',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: '#222222'
                        },
                        ticks: {
                            color: '#AAAAAA'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#FFFFFF'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
    
    // Initialize the chart
    initEmotionChart();
    
    // Draw emotion face
    function drawEmotionFace(emotion) {
        const emotionData = EMOTION_DATA[emotion] || EMOTION_DATA["neutral"];
        const size = 140;
        const radius = size / 2;
        
        // Create SVG
        const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.setAttribute("width", size);
        svg.setAttribute("height", size);
        svg.setAttribute("viewBox", `0 0 ${size} ${size}`);
        
        // Create face circle
        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        circle.setAttribute("cx", radius);
        circle.setAttribute("cy", radius);
        circle.setAttribute("r", radius - 5);
        circle.setAttribute("fill", emotionData.color);
        svg.appendChild(circle);
        
        // Eye parameters
        const eyeOffsetX = radius * 0.4;
        const eyeOffsetY = radius * 0.3;
        const eyeRadius = radius * 0.12;
        
        // Left eye
        const leftEye = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        leftEye.setAttribute("cx", radius - eyeOffsetX);
        leftEye.setAttribute("cy", radius - eyeOffsetY);
        leftEye.setAttribute("r", eyeRadius);
        leftEye.setAttribute("fill", "#000000");
        svg.appendChild(leftEye);
        
        // Right eye
        const rightEye = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        rightEye.setAttribute("cx", radius + eyeOffsetX);
        rightEye.setAttribute("cy", radius - eyeOffsetY);
        rightEye.setAttribute("r", eyeRadius);
        rightEye.setAttribute("fill", "#000000");
        svg.appendChild(rightEye);
        
        // Mouth
        const mouthY = radius + radius * 0.2;
        const mouthWidth = radius;
        
        if (emotionData.mouthOpen) {
            // Draw surprised open mouth (circle)
            const mouth = document.createElementNS("http://www.w3.org/2000/svg", "circle");
            mouth.setAttribute("cx", radius);
            mouth.setAttribute("cy", mouthY);
            mouth.setAttribute("r", radius * 0.15);
            mouth.setAttribute("fill", "#000000");
            svg.appendChild(mouth);
        } else {
            if (emotionData.mouthCurve === 0) {
                // Straight line for neutral
                const mouth = document.createElementNS("http://www.w3.org/2000/svg", "line");
                mouth.setAttribute("x1", radius - mouthWidth / 2);
                mouth.setAttribute("y1", mouthY);
                mouth.setAttribute("x2", radius + mouthWidth / 2);
                mouth.setAttribute("y2", mouthY);
                mouth.setAttribute("stroke", "#000000");
                mouth.setAttribute("stroke-width", "4");
                svg.appendChild(mouth);
            } else {
                // Curved mouth using path
                const curveHeight = 20 * emotionData.mouthCurve;
                const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
                path.setAttribute("d", `M ${radius - mouthWidth / 2} ${mouthY} Q ${radius} ${mouthY + curveHeight}, ${radius + mouthWidth / 2} ${mouthY}`);
                path.setAttribute("fill", "none");
                path.setAttribute("stroke", "#000000");
                path.setAttribute("stroke-width", "4");
                svg.appendChild(path);
            }
        }
        
        // Replace any existing face
        emotionFace.innerHTML = '';
        emotionFace.appendChild(svg);
    }
    
    // Update the UI with data from the server
    function updateUI(data) {
        // Update emotion face and name
        drawEmotionFace(data.emotion.current);
        emotionName.textContent = data.emotion.current.toUpperCase();
        
        // Update touch count
        touchCount.textContent = data.touch.today_touches;
        
        // Add/remove active class for touch indicator
        if (data.touch.active_touches > 0) {
            touchContainer.classList.add('touch-active');
        } else {
            touchContainer.classList.remove('touch-active');
        }
        
        // Update total statistics
        if (data.total_stats) {
            totalEmotions.textContent = data.total_stats.total_emotions || 0;
            dominantEmotion.textContent = (data.total_stats.dominant_emotion || 'neutral').toUpperCase();
            totalTouches.textContent = data.total_stats.total_touches || 0;
            totalAvgDuration.textContent = (data.total_stats.avg_touch_duration || 0).toFixed(1) + 's';
            totalTouchDuration.textContent = (data.total_stats.total_touch_duration || 0).toFixed(1) + 's';
        }
        
        // Update system time
        systemTime.textContent = `SYS: ${data.time}`;
        
        // Update emotion chart
        if (emotionChart) {
            ALL_EMOTIONS.forEach((emotion, index) => {
                emotionChart.data.datasets[0].data[index] = data.emotion.counts[emotion] || 0;
            });
            emotionChart.update();
        }
    }
    
    // Connect to WebSocket
    function connectWebSocket() {
        // Use the correct WebSocket URL based on current location
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        const socket = new WebSocket(wsUrl);
        
        socket.onopen = function() {
            console.log('WebSocket connection established');
        };
        
        socket.onmessage = function(event) {
            // Parse the data from the server
            const data = JSON.parse(event.data);
            // Update the UI
            updateUI(data);
        };
        
        socket.onclose = function() {
            console.log('WebSocket connection closed. Reconnecting...');
            // Reconnect after a delay
            setTimeout(connectWebSocket, 2000);
        };
        
        socket.onerror = function(error) {
            console.error('WebSocket error:', error);
            socket.close(); // This will trigger the onclose event and reconnect
        };
    }
    
    // Start WebSocket connection
    connectWebSocket();
    
    // Initial UI setup with default values
    drawEmotionFace('neutral');
});