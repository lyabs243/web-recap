function webRecapApp() {
  return {
    language: "en",
    locale: {},
    topic: "",
    isSubmitting: false,
    events: [],
    currentEvent: null,
    references: [],
    articleTitle: "",
    articleHtml: "",
    statusLabel: "Idle",
    socket: null,

    async init() {
      await this.loadLocale();
    },

    async setLanguage(language) {
      this.language = language;
      await this.loadLocale();
    },

    async loadLocale() {
      const response = await fetch(`/frontend/locales/${this.language}.json`);
      this.locale = await response.json();
      this.statusLabel = this.t("idleStatus");
    },

    t(key, params = {}) {
      let text = this.locale[key] || key;
      Object.keys(params).forEach((p) => {
        text = text.replace(`{${p}}`, params[p]);
      });
      return text;
    },

    formatTime(value) {
      if (!value) return "";
      return new Date(value).toLocaleTimeString();
    },

    getEventIcon(stage) {
      const icons = {
        submit: '<svg class="w-10 h-10 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>',
        query: '<svg class="w-10 h-10 animate-bounce" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>',
        search: '<svg class="w-10 h-10 animate-spin-slow" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>',
        scrape: '<svg class="w-10 h-10 animate-bounce" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10"></path></svg>',
        clean: '<svg class="w-10 h-10 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-7.714 2.143L11 21l-2.143-7.714L1 12l7.714-2.143L11 3z"></path></svg>',
        "source-plan": '<svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"></path></svg>',
        outline: '<svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 6h16M4 10h16M4 14h16M4 18h16"></path></svg>',
        write: '<svg class="w-10 h-10 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg>',
        done: '<svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>',
        failed: '<svg class="w-10 h-10 content-shake" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>',
      };
      return icons[stage] || icons.submit;
    },

    getProgressPercentage() {
      const stages = ["submit", "query", "search", "scrape", "clean", "source-plan", "outline", "write", "done"];
      const index = stages.indexOf(this.currentEvent?.stage || "submit");
      return ((index + 1) / stages.length) * 100;
    },

    async submit() {
      if (this.topic.trim().length < 3 || this.isSubmitting) {
        return;
      }

      this.isSubmitting = true;
      this.events = [];
      this.currentEvent = {
        stage: "submit",
        message: "submitting",
        timestamp: new Date().toISOString(),
      };
      this.references = [];
      this.articleTitle = "";
      this.articleHtml = "";
      this.statusLabel = this.t("submitting");

      try {
        const response = await fetch(window.WEB_RECAP_CONFIG.apiBase, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ topic: this.topic, language: this.language }),
        });
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.detail || this.t("genericError"));
        }
        this.openStream(payload.job_id);
      } catch (error) {
        this.currentEvent = {
          type: "failed",
          stage: "failed",
          message: error.message,
          timestamp: new Date().toISOString(),
        };
        this.events.push(this.currentEvent);
        this.statusLabel = this.t("failedStatus");
        setTimeout(() => {
          this.isSubmitting = false;
        }, 3000);
      }
    },

    openStream(jobId) {
      if (this.socket) {
        this.socket.close();
      }

      const protocol = window.location.protocol === "https:" ? "wss" : "ws";
      const url = `${protocol}://${window.location.host}${window.WEB_RECAP_CONFIG.websocketPath}/${jobId}/stream`;
      this.socket = new WebSocket(url);
      this.socket.onmessage = (event) => {
        const payload = JSON.parse(event.data);
        this.events.unshift(payload);
        this.currentEvent = payload;

        if (payload.type === "progress") {
          this.statusLabel = payload.stage;
          return;
        }
        if (payload.type === "completed") {
          const result = payload.payload.result;
          this.articleTitle = result.title;
          this.articleHtml = window.marked.parse(result.markdown);
          this.references = result.references;
          this.statusLabel = this.t("doneStatus");
          setTimeout(() => {
            this.isSubmitting = false;
          }, 1000);
        }
        if (payload.type === "failed") {
          this.statusLabel = this.t("failedStatus");
          setTimeout(() => {
            this.isSubmitting = false;
          }, 3000);
        }
      };
      this.socket.onclose = () => {
        this.socket = null;
      };
    },
  };
}

window.webRecapApp = webRecapApp;