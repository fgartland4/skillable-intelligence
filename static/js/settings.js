/**
 * settings.js — Settings management for Lab Program Designer v3.
 *
 * Manages user preferences, branding, and default references.
 * AI API calls route through the Skillable Intelligence backend — no API key required in browser.
 * All settings are persisted in localStorage under 'labdesigner_settings'.
 */

const Settings = (() => {
    const STORAGE_KEY = 'labdesigner_settings';

    const DEFAULTS = {
        // Lab Defaults
        defaultSeatTime: 45,
        activitiesPerLab: 5,
        defaultDifficulty: 'intermediate',

        // Lab Naming Formula
        labNamingFormula: '{Verb} {Specific Action} {Product Name}',

        // Instruction Style Guide
        instructionStyleGuide: 'microsoft',  // 'microsoft' | 'google' | 'apple' | 'redhat' | 'custom'
        customStyleGuideUrl: '',

        // Branding
        logoUrl: '',
        brandingSourceUrl: '',
        brandColors: {
            primary: '',
            secondary: '',
            accent: '',
            text: '',
            background: '',
        },
        brandFonts: {
            heading: '',
            body: '',
        },

        // Default Reference Materials
        defaultReferences: [],
    };

    let _settings = null;

    // ── Persistence ──

    function load() {
        try {
            const raw = localStorage.getItem(STORAGE_KEY);
            const stored = raw ? JSON.parse(raw) : {};
            _settings = deepMerge(structuredClone(DEFAULTS), stored);
        } catch {
            _settings = structuredClone(DEFAULTS);
        }
        return _settings;
    }

    function save() {
        if (!_settings) load();
        localStorage.setItem(STORAGE_KEY, JSON.stringify(_settings));
    }

    // ── Accessors ──

    function get(key) {
        if (!_settings) load();
        return key in _settings ? _settings[key] : undefined;
    }

    function set(key, value) {
        if (!_settings) load();
        _settings[key] = value;
        save();
        return value;
    }

    function getAll() {
        if (!_settings) load();
        return structuredClone(_settings);
    }

    // ── Default References ──

    function addDefaultReference(ref) {
        if (!_settings) load();
        if (!ref || !ref.id) {
            throw new Error('Reference must include an id');
        }
        const exists = _settings.defaultReferences.some(r => r.id === ref.id);
        if (exists) {
            _settings.defaultReferences = _settings.defaultReferences.map(r =>
                r.id === ref.id ? ref : r
            );
        } else {
            _settings.defaultReferences.push(ref);
        }
        save();
    }

    function removeDefaultReference(id) {
        if (!_settings) load();
        _settings.defaultReferences = _settings.defaultReferences.filter(r => r.id !== id);
        save();
    }

    // ── AI Provider Helpers ──

    function isConfigured() {
        return true;  // API key lives server-side in .env — always configured
    }

    // ── AI API Calls ──

    async function callAI(messages, options = {}) {
        const res = await fetch('/designer/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ messages, max_tokens: options.maxTokens || 4096 }),
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({ error: res.statusText }));
            throw new Error(err.error || `Server error (${res.status})`);
        }
        const data = await res.json();
        return data.text || '';
    }

    async function testConnection() {
        try {
            const result = await callAI([
                { role: 'system', content: 'Reply with exactly: Connection successful' },
                { role: 'user', content: 'Test' },
            ], { maxTokens: 50 });
            return { ok: true, message: result.slice(0, 100) };
        } catch (e) {
            return { ok: false, message: e.message };
        }
    }

    // ── Utilities ──

    function deepMerge(target, source) {
        for (const key of Object.keys(source)) {
            if (
                source[key] !== null &&
                typeof source[key] === 'object' &&
                !Array.isArray(source[key]) &&
                typeof target[key] === 'object' &&
                target[key] !== null &&
                !Array.isArray(target[key])
            ) {
                deepMerge(target[key], source[key]);
            } else {
                target[key] = source[key];
            }
        }
        return target;
    }

    // Initialize on load
    load();

    return {
        get,
        set,
        getAll,
        save,
        load,
        addDefaultReference,
        removeDefaultReference,
        callAI,
        testConnection,
        isConfigured,
    };
})();
