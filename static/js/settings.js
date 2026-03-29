/**
 * settings.js — Settings management and AI provider integration for Lab Program Designer v3.
 *
 * Manages user preferences, branding, default references, and AI API routing.
 * All settings are persisted in localStorage under 'labdesigner_settings'.
 */

const Settings = (() => {
    const STORAGE_KEY = 'labdesigner_settings';

    const DEFAULT_MODELS = {
        claude: 'claude-sonnet-4-20250514',
        openai: 'gpt-4o',
        custom: 'default',
    };

    const DEFAULTS = {
        // AI Provider
        aiProvider: 'claude',
        apiKey: '',
        model: DEFAULT_MODELS.claude,
        customEndpoint: '',

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

    function getDefaultModel(provider) {
        return DEFAULT_MODELS[provider] || DEFAULT_MODELS.claude;
    }

    function isConfigured() {
        if (!_settings) load();
        return !!_settings.apiKey;
    }

    // ── AI API Calls ──

    async function callAI(messages, options = {}) {
        if (!_settings) load();
        if (!_settings.apiKey) {
            throw new Error('No API key configured. Go to Settings to add one.');
        }

        const provider = _settings.aiProvider || 'claude';

        switch (provider) {
            case 'claude':  return _callClaude(messages, options);
            case 'openai':  return _callOpenAI(messages, options);
            case 'custom':  return _callCustom(messages, options);
            default:        throw new Error(`Unknown AI provider: ${provider}`);
        }
    }

    async function _callClaude(messages, options) {
        const systemMsg = messages.find(m => m.role === 'system');
        const chatMessages = messages.filter(m => m.role !== 'system');

        const body = {
            model: _settings.model || DEFAULT_MODELS.claude,
            max_tokens: options.maxTokens || 4096,
            messages: chatMessages.map(m => ({ role: m.role, content: m.content })),
        };

        if (systemMsg) {
            body.system = systemMsg.content;
        }

        const res = await fetch('https://api.anthropic.com/v1/messages', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': _settings.apiKey,
                'anthropic-version': '2023-06-01',
                'anthropic-dangerous-direct-browser-access': 'true',
            },
            body: JSON.stringify(body),
        });

        if (!res.ok) {
            const err = await res.text();
            throw new Error(`Claude API error (${res.status}): ${err}`);
        }

        const data = await res.json();
        return data.content?.[0]?.text || '';
    }

    async function _callOpenAI(messages, options) {
        const body = {
            model: _settings.model || DEFAULT_MODELS.openai,
            max_tokens: options.maxTokens || 4096,
            messages: messages.map(m => ({ role: m.role, content: m.content })),
        };

        const res = await fetch('https://api.openai.com/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${_settings.apiKey}`,
            },
            body: JSON.stringify(body),
        });

        if (!res.ok) {
            const err = await res.text();
            throw new Error(`OpenAI API error (${res.status}): ${err}`);
        }

        const data = await res.json();
        return data.choices?.[0]?.message?.content || '';
    }

    async function _callCustom(messages, options) {
        const endpoint = _settings.customEndpoint;
        if (!endpoint) {
            throw new Error('Custom endpoint URL is not configured. Go to Settings to add one.');
        }

        const body = {
            model: _settings.model || DEFAULT_MODELS.custom,
            max_tokens: options.maxTokens || 4096,
            messages: messages.map(m => ({ role: m.role, content: m.content })),
        };

        const res = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${_settings.apiKey}`,
            },
            body: JSON.stringify(body),
        });

        if (!res.ok) {
            const err = await res.text();
            throw new Error(`Custom API error (${res.status}): ${err}`);
        }

        const data = await res.json();
        // Support both Claude-style and OpenAI-style response formats
        return data.content?.[0]?.text
            || data.choices?.[0]?.message?.content
            || JSON.stringify(data);
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
        getDefaultModel,
        isConfigured,
    };
})();
