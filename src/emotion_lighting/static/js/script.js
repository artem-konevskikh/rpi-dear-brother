// Emotion Lighting System - Frontend JavaScript
import { defaultLanguage, languages, translations, emotionNames } from './lang.js';

document.addEventListener('DOMContentLoaded', function () {
    // ----- UTILITY FUNCTIONS -----
    // Format large numbers with K/M suffix
    function formatLargeNumber(num) {
        if (!num && num !== 0) return '0';
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num;
    }
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
        // Text elements that need translation
        pageTitle: document.querySelector('title'),
        headerTitle: document.querySelector('h1'),
        systemVersion: document.getElementById('system-version'),
        sectionTitles: [
            document.getElementById('current-emotion-title'),
            document.getElementById('interaction-data-title'),
            document.getElementById('emotion-tracking-title'),
            document.getElementById('system-status-title')
        ],
        touchesLabel: document.getElementById('touches-label'),
        todayLabel: document.getElementById('today-label'),
        chartTitle: document.getElementById('daily-emotion-profile'),
        statsTitle: document.getElementById('total-statistics'),
        statsLabels: [
            document.getElementById('emotions-detected-label'),
            document.getElementById('dominant-emotion-label'),
            document.getElementById('total-touches-label'),
            document.getElementById('avg-touch-time-label'),
            document.getElementById('all-time-touch-label')
        ]
    };
    
    // ----- LANGUAGE MANAGEMENT -----
    // Current language - prioritize defaultLanguage over localStorage
    let currentLanguage = defaultLanguage;
    // Only use localStorage if it exists and user explicitly changed it
    const storedLanguage = localStorage.getItem('language');
    if (storedLanguage && storedLanguage !== defaultLanguage) {
        currentLanguage = storedLanguage;
    }
    
    // Language selector has been removed as per requirements
    // Language is now configured via script only
    
    // Set language and update UI
    function setLanguage(lang) {
        if (!translations[lang]) return;
        
        currentLanguage = lang;
        localStorage.setItem('language', lang);
        updateLanguage();
    }
    
    // Update all text elements with the current language
    function updateLanguage() {
        const t = translations[currentLanguage];
        
        // Update page title and header
        elements.pageTitle.textContent = t.title;
        elements.headerTitle.textContent = t.title;
        elements.systemVersion.textContent = t.systemVersion;
        
        // Update section titles
        const sectionTitlesText = [t.currentEmotion, t.interactionData, t.emotionTracking, t.systemStatus];
        elements.sectionTitles.forEach((el, i) => {
            if (sectionTitlesText[i]) el.textContent = sectionTitlesText[i];
        });
        
        // Update touch data labels
        elements.touchesLabel.textContent = t.touches;
        elements.todayLabel.textContent = t.today;
        
        // Update chart title
        elements.chartTitle.textContent = t.dailyEmotionProfile;
        
        // Update stats title and labels
        elements.statsTitle.textContent = t.totalStatistics;
        
        const statsLabelsText = [
            t.emotionsDetected,
            t.dominantEmotion,
            t.totalTouches,
            t.avgTouchTime,
            t.allTimeTouch
        ];
        
        elements.statsLabels.forEach((el, i) => {
            if (statsLabelsText[i]) el.textContent = statsLabelsText[i];
        });
        
        // Update current emotion name if present
        if (elements.emotionName.textContent) {
            const emotion = elements.emotionName.textContent.toLowerCase();
            if (emotionNames[currentLanguage][emotion]) {
                elements.emotionName.textContent = emotionNames[currentLanguage][emotion];
            }
        }
        
        // Update dominant emotion if present
        if (elements.dominantEmotion.textContent) {
            const emotion = elements.dominantEmotion.textContent.toLowerCase();
            if (emotionNames[currentLanguage][emotion]) {
                elements.dominantEmotion.textContent = emotionNames[currentLanguage][emotion];
            }
        }
        
        // Language selector has been removed
    }

    // ----- EMOTION CONFIGURATION -----
    const EMOTION_CONFIG = {
        "happy": {
            "color": "#FFFF00", // Yellow
            "emoji": "(◠‿◠)"    // Smile
        },
        "sad": {
            "color": "#0000FF", // Blue
            "emoji": "(︶︹︶)"   // Frown
        },
        "angry": {
            "color": "#FF0000", // Red
            "emoji": "(ಠ益ಠ)"   // Angry face
        },
        "neutral": {
            "color": "#FFFFFF", // White
            "emoji": "( ･_･)"   // Neutral face
        },
        "fear": {
            "color": "#800080", // Purple
            "emoji": "(ㆆ﹏ㆆ)"   // Fearful face
        },
        "surprise": {
            "color": "#00FFFF", // Cyan
            "emoji": "(⊙□⊙)",   // Surprised face
            "mouthOpen": true   // Open mouth
        },
        "disgust": {
            "color": "#008000", // Green
            "emoji": "(≧︿≦)"   // Disgusted face
        },
        "no_face": {
            "color": "#808080", // Gray
            "emoji": "(⋅⋅⋅)"   // Empty face
        }
    };

    // All emotions to display in chart - ensure these match backend
    const CHART_EMOTIONS = ["happy", "sad", "angry", "neutral", "fear", "surprise", "disgust"];

    // Chart reference
    let emotionChart = null;

    // ----- CHART INITIALIZATION -----
    function initEmotionChart() {
        try {
            const chartElement = document.getElementById('emotion-chart');
            if (!chartElement) {
                console.error('Chart element not found');
                return;
            }
            
            const ctx = chartElement.getContext('2d');
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
                        ticks: { 
                            color: '#FFFFFF',
                            font: {
                                size: 8 // Smaller font size for x-axis labels
                            }
                        }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        };

            emotionChart = new Chart(ctx, chartConfig);
        } catch (error) {
            console.error('Failed to initialize chart:', error);
        }
    }

    // ----- ASCII EMOJI FACE DRAWING -----
    function drawEmotionFace(emotion) {
        // Use default emotion if invalid emotion is provided
        const safeEmotion = EMOTION_CONFIG[emotion] ? emotion : "neutral";
        const emotionData = EMOTION_CONFIG[safeEmotion];
        
        // Check if we already have a container to reuse
        let emojiContainer = elements.emotionFace.querySelector('.ascii-emoji');
        
        if (!emojiContainer) {
            // Create a new container if none exists
            emojiContainer = document.createElement('div');
            emojiContainer.className = 'ascii-emoji';
            elements.emotionFace.innerHTML = '';
            elements.emotionFace.appendChild(emojiContainer);
        }
        
        // Update the container properties
        emojiContainer.style.color = emotionData.color;
        emojiContainer.textContent = emotionData.emoji;
        
        // Also update the emotion name color to match
        elements.emotionName.style.color = emotionData.color;
    }

    // ----- UI UPDATES -----
    function updateUI(data) {
        // Update emotion face and name
        drawEmotionFace(data.emotion.current);
        elements.emotionName.textContent = emotionNames[currentLanguage][data.emotion.current] || data.emotion.current.toUpperCase();

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
        // Format large numbers for better display
        const touchCount = touchData.today_touches || 0;
        elements.touchCount.textContent = formatLargeNumber(touchCount);

        // Apply appropriate class based on number of digits
        elements.touchCount.classList.remove('digits-4', 'digits-5', 'digits-6', 'digits-7', 'digits-many');

        const digitCount = touchCount.toString().length;
        if (digitCount >= 8) {
            elements.touchCount.classList.add('digits-many');
        } else if (digitCount >= 6) {
            elements.touchCount.classList.add('digits-6');
        } else if (digitCount === 5) {
            elements.touchCount.classList.add('digits-5');
        } else if (digitCount === 4) {
            elements.touchCount.classList.add('digits-4');
        }

        if (touchData.active_touches > 0) {
            elements.touchContainer.classList.add('touch-active');
        } else {
            elements.touchContainer.classList.remove('touch-active');
        }
    }

    function updateStatistics(stats) {
        if (!stats) return;

        elements.totalEmotions.textContent = formatLargeNumber(stats.total_emotions || 0);
        const dominantEmotion = stats.dominant_emotion || 'neutral';
        elements.dominantEmotion.textContent = emotionNames[currentLanguage][dominantEmotion] || dominantEmotion.toUpperCase();
        elements.totalTouches.textContent = formatLargeNumber(stats.total_touches || 0);
        elements.totalAvgDuration.textContent = (stats.avg_touch_duration || 0).toFixed(1) + 's';
        elements.totalTouchDuration.textContent = (stats.total_touch_duration || 0).toFixed(1) + 's';
    }

    function updateEmotionChart(emotionCounts) {
        if (!emotionChart || !emotionCounts) return;

        // Check if data has actually changed before updating
        let hasChanged = false;
        
        CHART_EMOTIONS.forEach((emotion, index) => {
            const newValue = emotionCounts[emotion] || 0;
            if (emotionChart.data.datasets[0].data[index] !== newValue) {
                emotionChart.data.datasets[0].data[index] = newValue;
                hasChanged = true;
            }
        });
        
        // Only update the chart if data has changed
        if (hasChanged) {
            emotionChart.update();
        }
    }

    // ----- WEBSOCKET CONNECTION -----
    function connectWebSocket(retryCount = 0) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        // Exponential backoff for reconnection
        const maxRetryDelay = 30000; // 30 seconds max
        const baseDelay = 1000; // Start with 1 second
        const retryDelay = Math.min(maxRetryDelay, baseDelay * Math.pow(1.5, retryCount));

        const socket = new WebSocket(wsUrl);

        socket.onopen = () => {
            console.log('WebSocket connection established');
            // Reset retry count on successful connection
            connectWebSocket.retryCount = 0;
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
            const nextRetryCount = retryCount + 1;
            console.log(`WebSocket connection closed. Reconnecting in ${retryDelay}ms... (Attempt ${nextRetryCount})`);
            setTimeout(() => connectWebSocket(nextRetryCount), retryDelay);
        };

        socket.onerror = (error) => {
            console.error('WebSocket error:', error);
            // Let onclose handle the reconnection
        };
    }

    // ----- INITIALIZATION -----
    function initialize() {
        try {
            // Initialize chart
            initEmotionChart();

            // Set initial face
            drawEmotionFace('no_face');
            
            // Apply current language
            updateLanguage();

            // Start WebSocket connection last (after UI is ready)
            connectWebSocket();
            
            console.log('Emotion Lighting System initialized successfully');
        } catch (error) {
            console.error('Failed to initialize application:', error);
        }
    }

    // Start the application
    initialize();
});