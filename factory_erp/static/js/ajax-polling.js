/**
 * AJAX Polling - замена WebSocket для PythonAnywhere
 * Обеспечивает периодическое обновление данных через HTTP запросы
 */

class AjaxPoller {
    constructor(url, options = {}) {
        this.url = url;
        this.interval = options.interval || 5000; // 5 секунд по умолчанию
        this.onUpdate = options.onUpdate || (() => {});
        this.onError = options.onError || ((error) => console.error('Polling error:', error));
        this.enabled = true;
        this.timerId = null;
        this.lastData = null;
    }

    start() {
        console.log(`🔄 Starting AJAX polling for ${this.url} (interval: ${this.interval}ms)`);
        this.enabled = true;
        this.poll();
    }

    stop() {
        console.log(`⏹️ Stopping AJAX polling for ${this.url}`);
        this.enabled = false;
        if (this.timerId) {
            clearTimeout(this.timerId);
            this.timerId = null;
        }
    }

    async poll() {
        if (!this.enabled) return;

        try {
            const response = await fetch(this.url, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            if (data.success) {
                this.onUpdate(data);
            } else {
                this.onError(data.error || 'Unknown error');
            }

        } catch (error) {
            this.onError(error);
        }

        // Планируем следующий опрос
        if (this.enabled) {
            this.timerId = setTimeout(() => this.poll(), this.interval);
        }
    }
}

// Глобальный объект для управления всеми pollers
window.AjaxPollers = {
    active: {},
    
    create(name, url, options) {
        if (this.active[name]) {
            this.active[name].stop();
        }
        this.active[name] = new AjaxPoller(url, options);
        return this.active[name];
    },
    
    start(name) {
        if (this.active[name]) {
            this.active[name].start();
        }
    },
    
    stop(name) {
        if (this.active[name]) {
            this.active[name].stop();
        }
    },
    
    stopAll() {
        Object.values(this.active).forEach(poller => poller.stop());
    }
};

// Останавливаем все pollers при выходе со страницы
window.addEventListener('beforeunload', () => {
    window.AjaxPollers.stopAll();
});

console.log('✅ AJAX Polling module loaded');

