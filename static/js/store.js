/**
 * store.js — Data persistence for Lab Program Designer v3.
 * Manages projects across 4 phases: Audiences & Objectives, Design & Configure,
 * Organize & Finalize, Architect & Build.
 *
 * Uses localStorage with key 'labdesigner_v3'.
 * Migrates from v2 data automatically on first load.
 */

const Store = (() => {
    const STORAGE_KEY = 'labdesigner_v3';
    const LEGACY_KEY = 'labdesigner_v2';

    // ── Utilities ──────────────────────────────────────────────

    function generateId() {
        try {
            return crypto.randomUUID();
        } catch {
            // Fallback for older browsers or non-secure contexts
            return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
                const r = (Math.random() * 16) | 0;
                const v = c === 'x' ? r : (r & 0x3) | 0x8;
                return v.toString(16);
            });
        }
    }

    function now() {
        return new Date().toISOString();
    }

    // ── Default project structure ──────────────────────────────

    function emptyProject(name) {
        return {
            id: generateId(),
            name: name || 'Untitled Program',
            createdAt: now(),
            updatedAt: now(),

            // Phase 1: Audiences & Objectives
            uploads: [],              // { id, name, type, content, addedAt }
            urls: [],                 // { id, url, title, content, addedAt }
            audiences: [],            // { id, role, responsibilities, prerequisites }
            businessObjectives: [],   // strings
            learningObjectives: [],   // strings
            competencies: [],         // { id, name, description, source }
            successCriteria: [],      // strings — what "done" looks like
            technologyPlatform: '',   // e.g. "Azure", "Commvault", "Dragos"
            documentationRefs: [],    // { id, url, title, notes }
            scenarioSeeds: [],        // { id, title, description } — real-world scenario ideas
            phase1Chat: [],           // { role, content, timestamp }

            // Phase 2: Design & Organize
            programStructure: null,   // { labSeries: [{ id, title, description, labs: [{ id, title, description, activities: [{ id, title, description }] }] }] }
            framework: null,          // framework ID
            frameworkData: null,      // framework mapping details
            seatTime: { min: 45, max: 90 },
            instructionStyle: null,   // 'challenge' | 'step-by-step' | 'mixed'
            phase2Chat: [],

            // Phase 3: Draft & Finalize
            labBlueprints: [],        // { id, labSeriesId, title, shortDescription, activities[], approved: { title, description, outline } }
            draftInstructions: {},    // { labId: { activityId: markdownContent } }
            phase3Chat: [],

            // Phase 4: Package & Export
            environmentTemplates: [], // { id, name, platform, vms[], cloudResources[], credentials[], dummyData[], licenses[] }
            billOfMaterials: [],      // { id, category, item, details, required }
            lifecycleScripts: {},     // { templateId: { platform, buildScript, teardownScript } }
            scoringMethods: [],       // { id, labId, type: 'ai'|'script', scriptLanguage, script, description }
            exportHistory: [],        // { id, exportedAt, format, labCount }
            phase4Chat: [],
        };
    }

    // ── Migration from v2 ──────────────────────────────────────

    function migrateV2Project(old) {
        const p = emptyProject(old.name);
        p.id = old.id;
        p.createdAt = old.createdAt || p.createdAt;
        p.updatedAt = old.updatedAt || p.updatedAt;

        // Uploads — normalise shape
        if (Array.isArray(old.uploads)) {
            p.uploads = old.uploads.map(u => ({
                id: u.id || generateId(),
                name: u.name || 'Unknown',
                type: u.type || 'unknown',
                content: u.content || '',
                addedAt: u.addedAt || old.createdAt || now(),
            }));
        }

        // Goals → split into businessObjectives & learningObjectives
        // (v2 stored a flat array of goal strings — carry them as learning objectives)
        if (Array.isArray(old.goals)) {
            p.learningObjectives = old.goals.slice();
        }

        // Curriculum, framework, frameworkData carry over directly
        if (old.curriculum) p.curriculum = old.curriculum;
        if (old.framework) p.framework = old.framework;
        if (old.frameworkData) p.frameworkData = old.frameworkData;

        // Lab blueprints — normalise to v3 shape
        if (Array.isArray(old.labBlueprints)) {
            p.labBlueprints = old.labBlueprints.map(lb => ({
                id: lb.id || generateId(),
                title: lb.title || '',
                shortDescription: lb.description || '',
                activities: Array.isArray(lb.activities) ? lb.activities : [],
                approved: null,
            }));
        }

        // Environment templates carry over if they existed (v2 had the field on some projects)
        if (Array.isArray(old.environmentTemplates)) {
            p.environmentTemplates = old.environmentTemplates;
        }

        // Chat history — v2 used defineChat, organizeChat, labsChat
        // Map: defineChat → phase1Chat, organizeChat → phase2Chat, labsChat → phase3Chat
        if (Array.isArray(old.defineChat)) p.phase1Chat = old.defineChat;
        if (Array.isArray(old.organizeChat)) p.phase2Chat = old.organizeChat;
        if (Array.isArray(old.labsChat)) p.phase3Chat = old.labsChat;

        // Also accept already-named phase*Chat keys from partially-migrated data
        if (Array.isArray(old.phase1Chat) && old.phase1Chat.length) p.phase1Chat = old.phase1Chat;
        if (Array.isArray(old.phase2Chat) && old.phase2Chat.length) p.phase2Chat = old.phase2Chat;
        if (Array.isArray(old.phase3Chat) && old.phase3Chat.length) p.phase3Chat = old.phase3Chat;

        return p;
    }

    function migrateFromV2IfNeeded() {
        // Only migrate if v3 store does not exist yet and v2 does
        if (localStorage.getItem(STORAGE_KEY)) return;
        const raw = localStorage.getItem(LEGACY_KEY);
        if (!raw) return;

        try {
            const v2 = JSON.parse(raw);
            const v3 = { projects: [], activeProjectId: v2.activeProjectId || null };

            if (Array.isArray(v2.projects)) {
                v3.projects = v2.projects.map(migrateV2Project);
                // Ensure activeProjectId still points at a valid project
                if (v3.activeProjectId && !v3.projects.some(p => p.id === v3.activeProjectId)) {
                    v3.activeProjectId = v3.projects.length ? v3.projects[0].id : null;
                }
            }

            localStorage.setItem(STORAGE_KEY, JSON.stringify(v3));
            console.log('[Store] Migrated', v3.projects.length, 'project(s) from v2 → v3');
        } catch (err) {
            console.warn('[Store] v2 migration failed:', err);
        }
    }

    // Run migration on load
    migrateFromV2IfNeeded();

    // ── Storage helpers ────────────────────────────────────────

    function loadAll() {
        try {
            const raw = localStorage.getItem(STORAGE_KEY);
            return raw ? JSON.parse(raw) : { projects: [], activeProjectId: null };
        } catch {
            return { projects: [], activeProjectId: null };
        }
    }

    function saveAll(data) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    }

    /** Internal helper: load a project by id, apply a mutator, save, and return the project. */
    function mutateProject(projectId, mutator) {
        const data = loadAll();
        const project = data.projects.find(p => p.id === projectId);
        if (!project) return null;
        mutator(project);
        project.updatedAt = now();
        saveAll(data);
        return project;
    }

    // ── Project CRUD ───────────────────────────────────────────

    function listProjects() {
        return loadAll().projects;
    }

    function getProject(id) {
        return loadAll().projects.find(p => p.id === id) || null;
    }

    function getActiveProject() {
        const data = loadAll();
        if (!data.activeProjectId || data.projects.length === 0) return null;
        return data.projects.find(p => p.id === data.activeProjectId) || null;
    }

    function setActiveProject(id) {
        const data = loadAll();
        data.activeProjectId = id;
        saveAll(data);
    }

    function createProject(name) {
        const data = loadAll();
        const project = emptyProject(name);
        data.projects.push(project);
        data.activeProjectId = project.id;
        saveAll(data);
        return project;
    }

    function updateProject(project) {
        const data = loadAll();
        const idx = data.projects.findIndex(p => p.id === project.id);
        if (idx >= 0) {
            project.updatedAt = now();
            data.projects[idx] = project;
            saveAll(data);
        }
        return project;
    }

    function deleteProject(id) {
        const data = loadAll();
        data.projects = data.projects.filter(p => p.id !== id);
        if (data.activeProjectId === id) {
            data.activeProjectId = data.projects.length ? data.projects[0].id : null;
        }
        saveAll(data);
    }

    // ── Chat helpers ───────────────────────────────────────────

    const PHASE_CHAT_KEYS = {
        phase1: 'phase1Chat',
        phase2: 'phase2Chat',
        phase3: 'phase3Chat',
        phase4: 'phase4Chat',
    };

    function addChatMessage(projectId, phase, role, content) {
        const chatKey = PHASE_CHAT_KEYS[phase] || (phase + 'Chat');
        return mutateProject(projectId, project => {
            if (!Array.isArray(project[chatKey])) project[chatKey] = [];
            project[chatKey].push({ role, content, timestamp: now() });
        });
    }

    function getChatHistory(projectId, phase) {
        const chatKey = PHASE_CHAT_KEYS[phase] || (phase + 'Chat');
        const project = getProject(projectId);
        if (!project) return [];
        return project[chatKey] || [];
    }

    // ── Phase 1: Audiences & Objectives helpers ────────────────

    function addUpload(projectId, { name, type, content }) {
        return mutateProject(projectId, project => {
            project.uploads.push({
                id: generateId(),
                name,
                type,
                content,
                addedAt: now(),
            });
        });
    }

    function addUrl(projectId, { url, title, content }) {
        return mutateProject(projectId, project => {
            project.urls.push({
                id: generateId(),
                url,
                title: title || url,
                content: content || '',
                addedAt: now(),
            });
        });
    }

    function addAudience(projectId, { role, responsibilities, prerequisites }) {
        return mutateProject(projectId, project => {
            project.audiences.push({
                id: generateId(),
                role,
                responsibilities: responsibilities || '',
                prerequisites: prerequisites || '',
            });
        });
    }

    function addCompetency(projectId, { name, description, source }) {
        return mutateProject(projectId, project => {
            project.competencies.push({
                id: generateId(),
                name,
                description: description || '',
                source: source || '',
            });
        });
    }

    // ── Phase 1: Additional helpers ─────────────────────────────

    function addDocumentationRef(projectId, { url, title, notes }) {
        return mutateProject(projectId, project => {
            if (!Array.isArray(project.documentationRefs)) project.documentationRefs = [];
            project.documentationRefs.push({
                id: generateId(),
                url,
                title: title || url,
                notes: notes || '',
            });
        });
    }

    function addScenarioSeed(projectId, { title, description }) {
        return mutateProject(projectId, project => {
            if (!Array.isArray(project.scenarioSeeds)) project.scenarioSeeds = [];
            project.scenarioSeeds.push({
                id: generateId(),
                title,
                description: description || '',
            });
        });
    }

    // ── Phase 2: Design & Organize helpers ────────────────────

    function updateProgramStructure(projectId, programStructure) {
        return mutateProject(projectId, project => {
            project.programStructure = programStructure;
        });
    }

    function setInstructionStyle(projectId, style) {
        return mutateProject(projectId, project => {
            project.instructionStyle = style;
        });
    }

    // ── Phase 3: Organize & Finalize helpers ───────────────────

    /**
     * Approve a specific field on a lab blueprint.
     * @param {string} projectId
     * @param {string} labId       — the blueprint id
     * @param {string} field       — 'title', 'description', or 'outline'
     * @param {*}      value       — the approved value
     */
    function approveLabField(projectId, labId, field, value) {
        return mutateProject(projectId, project => {
            const bp = project.labBlueprints.find(b => b.id === labId);
            if (!bp) return;
            if (!bp.approved) bp.approved = { title: null, description: null, outline: null };
            bp.approved[field] = value;
        });
    }

    function setDraftInstructions(projectId, labId, markdownContent) {
        return mutateProject(projectId, project => {
            if (!project.draftInstructions) project.draftInstructions = {};
            project.draftInstructions[labId] = markdownContent;
        });
    }

    // ── Phase 4: Architect & Build helpers ─────────────────────

    function addEnvironmentTemplate(projectId, template) {
        return mutateProject(projectId, project => {
            const entry = {
                id: template.id || generateId(),
                name: template.name || '',
                platform: template.platform || '',
                vms: template.vms || [],
                cloudResources: template.cloudResources || [],
                credentials: template.credentials || [],
                dummyData: template.dummyData || [],
                licenses: template.licenses || [],
            };
            project.environmentTemplates.push(entry);
        });
    }

    function setBOM(projectId, billOfMaterials) {
        return mutateProject(projectId, project => {
            project.billOfMaterials = billOfMaterials;
        });
    }

    function setLifecycleScript(projectId, templateId, { platform, buildScript, teardownScript }) {
        return mutateProject(projectId, project => {
            if (!project.lifecycleScripts) project.lifecycleScripts = {};
            project.lifecycleScripts[templateId] = {
                platform: platform || '',
                buildScript: buildScript || '',
                teardownScript: teardownScript || '',
            };
        });
    }

    function addScoringMethod(projectId, { labId, type, scriptLanguage, script, description }) {
        return mutateProject(projectId, project => {
            if (!Array.isArray(project.scoringMethods)) project.scoringMethods = [];
            project.scoringMethods.push({
                id: generateId(),
                labId: labId || '',
                type: type || 'script',           // 'ai' or 'script'
                scriptLanguage: scriptLanguage || 'powershell',
                script: script || '',
                description: description || '',
            });
        });
    }

    function setScoringMethods(projectId, scoringMethods) {
        return mutateProject(projectId, project => {
            project.scoringMethods = scoringMethods;
        });
    }

    function addExportRecord(projectId, { format, labCount }) {
        return mutateProject(projectId, project => {
            if (!Array.isArray(project.exportHistory)) project.exportHistory = [];
            project.exportHistory.push({
                id: generateId(),
                exportedAt: now(),
                format: format || 'json',
                labCount: labCount || 0,
            });
        });
    }

    // ── Import / Export ────────────────────────────────────────

    function exportProject(projectId) {
        const project = getProject(projectId);
        return project ? JSON.stringify(project, null, 2) : null;
    }

    function importProject(json) {
        const data = loadAll();
        const project = typeof json === 'string' ? JSON.parse(json) : json;
        project.id = generateId(); // new ID to avoid collision
        project.importedAt = now();
        // Ensure all v3 fields exist on imported data
        const defaults = emptyProject();
        for (const key of Object.keys(defaults)) {
            if (!(key in project)) {
                project[key] = defaults[key];
            }
        }
        data.projects.push(project);
        data.activeProjectId = project.id;
        saveAll(data);
        return project;
    }

    // ── Public API ─────────────────────────────────────────────

    return {
        // Utilities
        generateId,

        // Project CRUD
        listProjects,
        getProject,
        getActiveProject,
        setActiveProject,
        createProject,
        updateProject,
        deleteProject,

        // Chat
        addChatMessage,
        getChatHistory,

        // Phase 1
        addUpload,
        addUrl,
        addAudience,
        addCompetency,
        addDocumentationRef,
        addScenarioSeed,

        // Phase 2
        updateProgramStructure,
        setInstructionStyle,

        // Phase 3
        approveLabField,
        setDraftInstructions,

        // Phase 4
        addEnvironmentTemplate,
        setBOM,
        setLifecycleScript,
        addScoringMethod,
        setScoringMethods,
        addExportRecord,

        // Import/Export
        exportProject,
        importProject,
    };
})();
