/**
 * chat.js — Chat engine for Lab Program Designer v3.
 * Handles AI conversations across 4 phases with phase-specific system prompts,
 * context injection from prior phases, and structured output parsing.
 *
 * Data model: Lab Series → Labs → Activities (not Courses/Modules/Lessons/Topics).
 *
 * Depends on: Store, Settings, Catalog, Frameworks (all global IIFEs).
 */

const Chat = (() => {

    // ── Phase key mapping ───────────────────────────────────────

    const PHASE_KEYS = {
        1: 'phase1',
        2: 'phase2',
        3: 'phase3',
        4: 'phase4',
    };

    function getPhaseKey(phase) {
        return PHASE_KEYS[phase] || `phase${phase}`;
    }

    // ── Structured output markers ───────────────────────────────

    const MARKERS = {
        1: { start: '===PHASE1_DATA===',          end: '===END_PHASE1_DATA===' },
        2: { start: '===PROGRAM_STRUCTURE===',     end: '===END_PROGRAM_STRUCTURE===' },
        3: [
            { start: '===LAB_BLUEPRINTS===',       end: '===END_LAB_BLUEPRINTS===' },
            { start: '===DRAFT_INSTRUCTIONS===',    end: '===END_DRAFT_INSTRUCTIONS===' },
        ],
        4: { start: '===ENVIRONMENT===',           end: '===END_ENVIRONMENT===' },
    };

    // ── System prompt builders ──────────────────────────────────

    function buildSystemPrompt(phase, context) {
        const seatTime = context.seatTime || Settings.get('defaultSeatTime') || '45-75';
        let prompt = '';

        switch (phase) {
            case 1:
                prompt = _phase1Prompt(context);
                break;
            case 2:
                prompt = _phase2Prompt(seatTime, context);
                break;
            case 3:
                prompt = _phase3Prompt(seatTime, context);
                break;
            case 4:
                prompt = _phase4Prompt(context);
                break;
            default:
                throw new Error(`Unknown phase: ${phase}`);
        }

        return prompt;
    }

    function _phase1Prompt(context) {
        return `You are an expert instructional designer helping create a hands-on lab training program. Your role in this phase is to answer three fundamental questions:

- **WHY** — What business problem does this training solve? What outcomes matter?
- **WHAT** — What technology, platform, or product are we teaching? What skills and competencies?
- **WHO** — Who is the target audience? What do they already know? What roles do they serve?

CORE DESIGN PRINCIPLE:
Every lab should be designed to work for BOTH instructor-led training (ILT/vILT) AND self-paced learning. This dual-use approach maximizes ROI for the customer. Instructions must be clear enough for self-paced learners to succeed independently, while also supporting instructor-led delivery where an instructor can add context and guidance. Do not ask the user about delivery mode — assume dual-use always.

CONVERSATION FLOW:
1. If this is a new conversation, ask what technology/platform/product the training is for and who the target audience is.
2. Gather: target audiences (roles, responsibilities, prerequisites), business objectives, learning objectives, success criteria, and the technology/platform being taught.
3. Ask for documentation links — this is critical for specialized software (Commvault, Dragos, Hyland, OneStream, etc.) that you may not have deep knowledge of.
4. Explore real-world scenario ideas that could become authentic lab exercises.
5. Based on what you learn about the audience's experience level, the complexity of the technology, and the learning objectives, recommend a difficulty level for the labs (Beginner, Intermediate, Advanced, or Expert). Explain your reasoning — e.g., "Given that your audience already has networking fundamentals and you're teaching advanced routing concepts, I'd recommend these labs be built at the Advanced level."
6. When you feel you have enough information, ask probing questions like "Is there anything else I should know about your learners or the technology?" and "Are there common mistakes or misconceptions learners face?"
7. Let the person know they can always come back and add more details later.

CONVERSATION STYLE:
- Be opinionated. Make recommendations, don't present "Option A vs Option B" choices. If you have a recommendation, lead with it and explain why. The designer can always push back.
- Keep responses concise and conversational. Avoid walls of text.
- When summarizing what you've learned, use short bullet points.

DO NOT ASK ABOUT:
- Lab environments, infrastructure, VMs, cloud subscriptions, or technical setup — that is handled in Phase 4.
- Instruction style (challenge-based vs step-by-step) — that is configured in Phase 3.
- Number of labs, length of labs, or lab duration — the AI generates the right number of labs in Phase 2 based on content scope, and lab duration is driven by the Targeted Seat Time setting in Preferences.
- Delivery mode (ILT vs self-paced) — every lab is dual-use by default.
- Stay focused on WHAT they want to teach and WHO they're teaching, not HOW the labs will be built or deployed.

PROGRAM NAMING:
- If the user hasn't named their program yet, suggest a clear, descriptive name based on what they've described.
- Include the program name in your structured output when you have one.

DIFFICULTY RECOMMENDATION:
- Always recommend a difficulty level based on audience prerequisites, technology complexity, and learning objectives.
- Valid levels: "beginner", "intermediate", "advanced", "expert"
- Include your recommendation in the structured output as "recommendedDifficulty".

COMPETENCY FRAMEWORK RECOMMENDATION:
- Once you understand the technology and audience, recommend a competency framework that should be used to align skills and labs.
- Examples: "CompTIA Security+", "AWS Solutions Architect", "Commvault Certification", "CISSP CBK", "Kubernetes CKAD", vendor-specific certification tracks, etc.
- Explain why you're recommending it and suggest 1-2 alternatives the designer could choose instead.
- The designer can accept, choose a different one, or ignore frameworks entirely.
- Include in structured output as "recommendedFramework": { "name": "...", "reason": "...", "alternatives": ["...", "..."] }
- Skills/competencies you extract should be tagged with this framework as their source once accepted.

IMPORTANT — OUTPUT STRUCTURED DATA EARLY AND OFTEN:
After EVERY response where you learn something new, output a structured data block with whatever you have so far. Do NOT wait until you have everything — output partial data immediately so the Lab Blueprint panel updates in real time. The data blocks are merged automatically, so it's safe to send partial updates. This gives the program designer a live preview they can react to.

\`\`\`
===PHASE1_DATA===
{ "programName": "...", "audiences": [{ "role": "...", "responsibilities": "...", "prerequisites": "..." }], "businessObjectives": ["..."], "learningObjectives": ["..."], "competencies": [{ "name": "...", "description": "...", "source": "Framework Name" }], "successCriteria": ["..."], "technologyPlatform": "...", "recommendedDifficulty": "intermediate", "recommendedFramework": { "name": "...", "reason": "...", "alternatives": ["...", "..."] }, "documentationRefs": [{ "url": "...", "title": "...", "notes": "..." }], "scenarioSeeds": [{ "title": "...", "description": "..." }] }
===END_PHASE1_DATA===
\`\`\`

Only include fields you have data for — omit empty arrays or unknown fields. Each block is merged with previous data, so partial updates are expected and encouraged.`;
    }

    function _phase2Prompt(seatTime, context) {
        const namingFormula = Settings.get('labNamingFormula') || '{Verb} {Specific Action} {Product Name}';

        let prompt = `You are an expert curriculum architect designing a hands-on lab training program. Based on the objectives and competencies from Phase 1, design a program structure using this hierarchy:

HIERARCHY: Lab Series → Labs → Activities
- A Lab Series is a collection of related labs (like a course)
- A Lab is a single hands-on session targeting ${seatTime} minutes of seat time
- An Activity is a discrete task within a lab (3-6 per lab)

LAB NAMING:
Lab naming is critical. Use this formula: ${namingFormula}
- Always start lab names with an action verb (Configure, Deploy, Implement, Analyze, Troubleshoot, etc.)
- Names should be specific and descriptive — avoid vague titles
- Example good names: "Configure Virtual Network Peering in Azure", "Deploy a Containerized Application with Kubernetes", "Troubleshoot Active Directory Replication Issues"
- Example bad names: "Azure Networking Lab", "Container Lab 1", "AD Lab"

Be opinionated — propose strong names. The program owner can refine them.`;

        if (context.frameworkId) {
            prompt += `\n\nWhen a skill framework is selected, map labs and activities to framework competencies where appropriate.`;
        }

        prompt += `\n\nDo NOT ask about instruction style (challenge-based vs step-by-step) — that is configured in Phase 3.

Output the program structure as:
\`\`\`
===PROGRAM_STRUCTURE===
{ "labSeries": [{ "id": "ls-1", "title": "...", "description": "...", "labs": [{ "id": "lab-1", "title": "...", "description": "...", "estimatedDuration": "${seatTime}", "activities": [{ "id": "act-1", "title": "...", "description": "..." }] }] }], "instructionStyle": "step-by-step" }
===END_PROGRAM_STRUCTURE===
\`\`\`

Be helpful when the designer wants to rename, reorganize, add, or remove items. Inline editing handles quick fixes — use chat for structural changes.`;

        return prompt;
    }

    function _phase3Prompt(seatTime, context) {
        const styleGuide = Settings.get('instructionStyleGuide') || 'microsoft';
        const customStyleUrl = Settings.get('customStyleGuideUrl') || '';
        const instructionStyle = context.instructionStyle || 'step-by-step';

        let styleRef = '';
        switch (styleGuide) {
            case 'microsoft':
                styleRef = 'Follow the Microsoft Style Guide for technical documentation.';
                break;
            case 'google':
                styleRef = 'Follow the Google Developer Documentation Style Guide.';
                break;
            case 'apple':
                styleRef = 'Follow the Apple Style Guide for technical writing.';
                break;
            case 'redhat':
                styleRef = 'Follow the Red Hat Documentation Guide for technical content.';
                break;
            case 'custom':
                styleRef = customStyleUrl
                    ? `Follow the custom style guide at: ${customStyleUrl}`
                    : 'Follow standard technical documentation best practices.';
                break;
            default:
                styleRef = 'Follow the Microsoft Style Guide for technical documentation.';
        }

        let prompt = `You are an expert lab content writer for Skillable. Draft detailed per-activity instructions for each lab. ${styleRef}

CORE DESIGN PRINCIPLE:
Every lab is designed for BOTH instructor-led (ILT/vILT) AND self-paced delivery. Instructions must be clear and complete enough for self-paced learners to succeed independently, while also supporting instructor-led sessions. Do not reference a specific delivery mode — write instructions that work for both.

INSTRUCTION STYLE: ${instructionStyle}
${instructionStyle === 'challenge' ? '- Give learners a goal/scenario and hints, but let them figure out the steps' : ''}
${instructionStyle === 'step-by-step' ? '- Provide detailed numbered steps with expected outcomes after each step' : ''}
${instructionStyle === 'mixed' ? '- Use challenge-based for intermediate/advanced activities, step-by-step for beginner activities' : ''}

FOR EACH ACTIVITY, INCLUDE:
- Clear heading with the activity title
- Introduction explaining what the learner will accomplish
- Numbered steps with specific actions (click this, type that, navigate here)
- Expected outcomes or verification steps after key actions
- Notes, tips, or warnings where appropriate
- A brief summary at the end

Default lab duration is ${seatTime} minutes. Each activity's instructions should be proportional to its estimated duration.

When generating lab blueprints, output:
\`\`\`
===LAB_BLUEPRINTS===
[{ "id": "...", "title": "...", "shortDescription": "...", "estimatedDuration": 0, "activities": [{ "title": "...", "tasks": [...], "duration": 0 }] }]
===END_LAB_BLUEPRINTS===
\`\`\`

When generating draft instructions for a specific activity, output:
\`\`\`
===DRAFT_INSTRUCTIONS===
{ "labId": "...", "activityId": "...", "markdown": "..." }
===END_DRAFT_INSTRUCTIONS===
\`\`\``;

        // Inject branding context for instruction generation
        const branding = _getBrandingContext();
        if (branding) {
            prompt += `\n\nBranding guidelines for generated instructions:\n${branding}`;
        }

        return prompt;
    }

    function _phase4Prompt(context) {
        return `You are an expert cloud/lab environment architect for Skillable. In this phase, help with:

1. ENVIRONMENT TEMPLATES: Design reusable environment configurations. For each template specify:
   - VMs needed (OS, RAM, CPU, disk, installed software)
   - Cloud resources (subscriptions, resource groups, storage, networking)
   - Credentials and access accounts
   - Dummy/practice data files to pre-populate
   - Required licenses or permissions

2. SCORING METHODS: Define how lab completion is validated. Two types supported:
   - **AI-based scoring**: Define rubrics and criteria for AI to evaluate learner work
   - **Script-based scoring**: Write PowerShell or Bash scripts that use product APIs to verify task completion
   NOTE: Do NOT suggest manual scoring — only AI-based or script-based.

3. LIFECYCLE SCRIPTS: Write build and teardown scripts for provisioning/cleaning environments.

4. BILL OF MATERIALS: Itemize everything needed to run the labs at scale.

Focus on environment reusability — multiple labs should share the same template whenever possible.

Output structured data as:
\`\`\`
===ENVIRONMENT===
{ "templates": [...], "billOfMaterials": [...], "lifecycleScripts": { "templateId": { "platform": "...", "buildScript": "...", "teardownScript": "..." } }, "scoringMethods": [{ "labId": "...", "type": "ai|script", "scriptLanguage": "powershell|bash", "script": "...", "description": "..." }] }
===END_ENVIRONMENT===
\`\`\``;
    }

    // ── Context helpers ─────────────────────────────────────────

    function _getBrandingContext() {
        const parts = [];
        const logoUrl = Settings.get('logoUrl');
        const colors = Settings.get('brandColors');
        const fonts = Settings.get('brandFonts');

        if (logoUrl) parts.push(`Logo URL: ${logoUrl}`);
        if (colors) {
            const entries = Object.entries(colors).filter(([, v]) => v);
            if (entries.length) {
                parts.push('Brand colors: ' + entries.map(([k, v]) => `${k}: ${v}`).join(', '));
            }
        }
        if (fonts) {
            const entries = Object.entries(fonts).filter(([, v]) => v);
            if (entries.length) {
                parts.push('Brand fonts: ' + entries.map(([k, v]) => `${k}: ${v}`).join(', '));
            }
        }

        return parts.length ? parts.join('\n') : null;
    }

    function _getPhase1Context(project) {
        const parts = [];

        if (project.technologyPlatform) {
            parts.push('Technology/Platform: ' + project.technologyPlatform);
        }
        if (project.audiences && project.audiences.length) {
            parts.push('Target audiences: ' + project.audiences.map(a => a.role).join(', '));
        }
        if (project.businessObjectives && project.businessObjectives.length) {
            parts.push('Business objectives: ' + project.businessObjectives.join('; '));
        }
        if (project.learningObjectives && project.learningObjectives.length) {
            parts.push('Learning objectives: ' + project.learningObjectives.join('; '));
        }
        if (project.competencies && project.competencies.length) {
            parts.push('Competencies: ' + project.competencies.map(c => c.name).join(', '));
        }
        if (project.successCriteria && project.successCriteria.length) {
            parts.push('Success criteria: ' + project.successCriteria.join('; '));
        }
        if (project.documentationRefs && project.documentationRefs.length) {
            parts.push('Documentation references: ' + project.documentationRefs.map(d => d.title || d.url).join(', '));
        }
        if (project.scenarioSeeds && project.scenarioSeeds.length) {
            parts.push('Scenario ideas: ' + project.scenarioSeeds.map(s => s.title).join(', '));
        }

        return parts.length ? parts.join('\n') : null;
    }

    function _getFrameworkContext(project) {
        if (!project.framework) return null;

        try {
            const fw = Frameworks.getById(project.framework);
            if (!fw) return null;
            const lines = [`Skill framework: ${fw.name}`];
            if (fw.domains && fw.domains.length) {
                lines.push('Domains: ' + fw.domains.map(d => d.name).join(', '));
            }
            if (project.frameworkData) {
                lines.push('Framework mapping data: ' + JSON.stringify(project.frameworkData));
            }
            return lines.join('\n');
        } catch {
            return null;
        }
    }

    function _getCatalogContext() {
        try {
            if (typeof Catalog !== 'undefined' && typeof Catalog.toPromptContext === 'function') {
                return Catalog.toPromptContext();
            }
            if (typeof Catalog !== 'undefined' && typeof Catalog.getDomains === 'function') {
                const domains = Catalog.getDomains();
                if (domains && domains.length) {
                    const summary = domains.map(d => {
                        const skills = d.skills ? d.skills.map(s => s.name).join(', ') : '';
                        return `${d.name}: ${skills}`;
                    }).join('\n');
                    return `Available skill domains and lab templates:\n${summary}`;
                }
            }
        } catch {
            // Catalog not available
        }
        return null;
    }

    // ── Message assembly ────────────────────────────────────────

    function buildMessages(phase, projectId) {
        const project = Store.getProject(projectId);
        if (!project) throw new Error(`Project not found: ${projectId}`);

        const context = {
            seatTime: project.seatTime
                ? `${project.seatTime.min}-${project.seatTime.max}`
                : Settings.get('defaultSeatTime') || '45-75',
            frameworkId: project.framework,
            instructionStyle: project.instructionStyle || 'step-by-step',
        };

        const messages = [];

        // System prompt
        messages.push({ role: 'system', content: buildSystemPrompt(phase, context) });

        // Context from prior phases
        _injectPhaseContext(messages, phase, project);

        // Chat history
        const phaseKey = getPhaseKey(phase);
        const history = Store.getChatHistory(projectId, phaseKey);
        for (const msg of history) {
            messages.push({ role: msg.role, content: msg.content });
        }

        return messages;
    }

    function _injectPhaseContext(messages, phase, project) {
        // Phase 1 uploads context
        if (phase === 1 && project.uploads && project.uploads.length) {
            const uploadContent = project.uploads
                .filter(u => u.content)
                .map(u => `--- ${u.name} ---\n${u.content}`)
                .join('\n\n');
            if (uploadContent) {
                messages.push({
                    role: 'system',
                    content: `The user has uploaded these documents:\n\n${uploadContent}`,
                });
            }
        }

        // Phase 2+ gets Phase 1 context
        if (phase >= 2) {
            const p1Context = _getPhase1Context(project);
            if (p1Context) {
                messages.push({
                    role: 'system',
                    content: `Context from Phase 1 (Audiences & Objectives):\n${p1Context}`,
                });
            }
        }

        // Framework context for phases 2+
        if (phase >= 2) {
            const fw = _getFrameworkContext(project);
            if (fw) {
                messages.push({ role: 'system', content: fw });
            }
        }

        // Catalog knowledge base for phases 2 and 4
        if (phase === 2 || phase === 4) {
            const catalog = _getCatalogContext();
            if (catalog) {
                messages.push({ role: 'system', content: catalog });
            }
        }

        // Phase 3+ gets Phase 2 program structure
        if (phase >= 3 && project.programStructure) {
            messages.push({
                role: 'system',
                content: `Program structure from Phase 2 (Design & Organize):\n${JSON.stringify(project.programStructure, null, 2)}`,
            });
        }

        // Phase 4 gets Phase 3 blueprints
        if (phase >= 4 && project.labBlueprints && project.labBlueprints.length) {
            messages.push({
                role: 'system',
                content: `Lab blueprints from Phase 3 (Draft & Finalize):\n${JSON.stringify(project.labBlueprints, null, 2)}`,
            });
        }
    }

    // ── Send message ────────────────────────────────────────────

    async function sendMessage(phase, projectId, userMessage) {
        const messages = buildMessages(phase, projectId);

        // Append the new user message
        messages.push({ role: 'user', content: userMessage });

        // Persist the user message
        const phaseKey = getPhaseKey(phase);
        Store.addChatMessage(projectId, phaseKey, 'user', userMessage);

        // Call the AI
        const response = await Settings.callAI(messages, { maxTokens: 4096 });

        // Persist the assistant response
        Store.addChatMessage(projectId, phaseKey, 'assistant', response);

        // Parse structured data if present
        const structured = parseStructuredData(response, phase);

        return {
            raw: response,
            display: cleanResponse(response),
            structured,
        };
    }

    // ── Structured data parsing ─────────────────────────────────

    function parseStructuredData(text, phase) {
        switch (phase) {
            case 1:
                return _extractBlock(text, MARKERS[1].start, MARKERS[1].end);
            case 2:
                return _extractBlock(text, MARKERS[2].start, MARKERS[2].end);
            case 3: {
                const blueprints = _extractBlock(text, MARKERS[3][0].start, MARKERS[3][0].end);
                const draft = _extractBlock(text, MARKERS[3][1].start, MARKERS[3][1].end);
                if (!blueprints && !draft) return null;
                return { blueprints, draftInstructions: draft };
            }
            case 4:
                return _extractBlock(text, MARKERS[4].start, MARKERS[4].end);
            default:
                return null;
        }
    }

    function _extractBlock(text, startMarker, endMarker) {
        const pattern = new RegExp(
            _escapeRegex(startMarker) + '([\\s\\S]*?)' + _escapeRegex(endMarker)
        );
        const match = text.match(pattern);
        if (!match) return null;

        try {
            return JSON.parse(match[1].trim());
        } catch {
            console.warn('[Chat] Failed to parse structured block between', startMarker, 'and', endMarker);
            return null;
        }
    }

    function _escapeRegex(str) {
        return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    // ── Clean response for display ──────────────────────────────

    function cleanResponse(text) {
        let cleaned = text;

        // Remove all known marker blocks
        const allMarkers = [
            MARKERS[1],
            MARKERS[2],
            ...MARKERS[3],
            MARKERS[4],
        ];

        for (const m of allMarkers) {
            const pattern = new RegExp(
                _escapeRegex(m.start) + '[\\s\\S]*?' + _escapeRegex(m.end),
                'g'
            );
            cleaned = cleaned.replace(pattern, '');
        }

        return cleaned.trim();
    }

    // ── Public API ──────────────────────────────────────────────

    return {
        buildSystemPrompt,
        buildMessages,
        sendMessage,
        parseStructuredData,
        cleanResponse,
        getPhaseKey,
    };
})();
