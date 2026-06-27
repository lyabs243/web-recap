function webRecapApp() {
  return {
    language: "en",
    locale: {},
    topic: "",
    isSubmitting: false,
    events: [],
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

    t(key) {
      return this.locale[key] || key;
    },

    formatTime(value) {
      return new Date(value).toLocaleTimeString();
    },

    async submit() {
      if (this.topic.trim().length < 3 || this.isSubmitting) {
        return;
      }

      this.isSubmitting = true;
      this.events = [];
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
        this.events.push({
          type: "failed",
          stage: "submit",
          message: error.message,
          timestamp: new Date().toISOString(),
        });
        this.statusLabel = this.t("failedStatus");
        this.isSubmitting = false;
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
          this.isSubmitting = false;
        }
        if (payload.type === "failed") {
          this.statusLabel = this.t("failedStatus");
          this.isSubmitting = false;
        }
      };
      this.socket.onclose = () => {
        this.socket = null;
      };
    },
  };
}

window.webRecapApp = webRecapApp;