// Language configuration for Emotion Lighting System

// Default language setting
const defaultLanguage = 'ru';

// Available languages
const languages = {
    en: 'English',
    ru: 'Русский'
};

// Text content for all UI elements
const translations = {
    // English translations
    en: {
        // Page title and header
        title: 'DEAR BROTHER, ...',
        systemVersion: 'SYSTEM v1.0',
        
        // Section titles
        currentEmotion: 'CURRENT EMOTION',
        interactionData: 'INTERACTION DATA',
        emotionTracking: 'EMOTION TRACKING',
        systemStatus: 'SYSTEM STATUS',
        
        // Touch data
        touches: 'TOUCHES',
        today: 'TODAY',
        
        // Chart labels
        dailyEmotionProfile: 'DAILY EMOTION PROFILE',
        
        // Statistics labels
        totalStatistics: 'TOTAL STATISTICS',
        emotionsDetected: 'EMOTIONS DETECTED:',
        dominantEmotion: 'DOMINANT EMOTION:',
        totalTouches: 'TOTAL TOUCHES:',
        avgTouchTime: 'AVG TOUCH TIME:',
        allTimeTouch: 'ALL-TIME TOUCH:',
        
        // System time
        systemTime: 'SYS:',
        
        // Language selector
        language: 'LANGUAGE:'
    },
    
    // Russian translations
    ru: {
        // Page title and header
        title: 'ДОРОГОЙ БРАТ, ...',
        systemVersion: 'СИСТЕМА v1.0',
        
        // Section titles
        currentEmotion: 'ТЕКУЩАЯ ЭМОЦИЯ',
        interactionData: 'ДАННЫЕ ВЗАИМОДЕЙСТВИЯ',
        emotionTracking: 'ОТСЛЕЖИВАНИЕ ЭМОЦИЙ',
        systemStatus: 'СТАТУС СИСТЕМЫ',
        
        // Touch data
        touches: 'КАСАНИЯ',
        today: 'СЕГОДНЯ',
        
        // Chart labels
        dailyEmotionProfile: 'ДНЕВНОЙ ПРОФИЛЬ ЭМОЦИЙ',
        
        // Statistics labels
        totalStatistics: 'ОБЩАЯ СТАТИСТИКА',
        emotionsDetected: 'ОБНАРУЖЕНО ЭМОЦИЙ:',
        dominantEmotion: 'ДОМИНИРУЮЩАЯ ЭМОЦИЯ:',
        totalTouches: 'ВСЕГО КАСАНИЙ:',
        avgTouchTime: 'СРЕДНЕЕ ВРЕМЯ КАСАНИЯ:',
        allTimeTouch: 'ОБЩЕЕ ВРЕМЯ КАСАНИЯ:',
        
        // System time
        systemTime: 'СИС:',
        
        // Language selector
        language: 'ЯЗЫК:'
    }
};

// Emotion names in different languages
const emotionNames = {
    en: {
        happy: 'HAPPY',
        sad: 'SAD',
        angry: 'ANGRY',
        neutral: 'NEUTRAL',
        fear: 'FEAR',
        surprise: 'SURPRISE',
        disgust: 'DISGUST',
        no_face: 'NO FACE'
    },
    ru: {
        happy: 'РАДОСТЬ',
        sad: 'ГРУСТЬ',
        angry: 'ЗЛОСТЬ',
        neutral: 'НЕЙТРАЛЬНЫЙ',
        fear: 'СТРАХ',
        surprise: 'УДИВЛЕНИЕ',
        disgust: 'ОТВРАЩЕНИЕ',
        no_face: 'НЕТ ЛИЦА'
    }
};

// Export all language-related variables
export { defaultLanguage, languages, translations, emotionNames };