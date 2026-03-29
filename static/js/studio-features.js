/**
 * studio-features.js — Skillable Studio Feature Nudge Catalog
 *
 * Contextual suggestions the AI surfaces during Phase 3 to remind
 * program designers about advanced Studio capabilities their lab
 * authors should consider during final authoring.
 *
 * Each feature has:
 *   - id:          unique key
 *   - name:        display name
 *   - category:    grouping for UI
 *   - description: what it does (1-2 sentences)
 *   - keywords:    words in draft instructions that trigger this nudge
 *   - nudge:       the suggestion shown to the user
 *   - docsUrl:     link to Skillable docs
 */

const StudioFeatures = (() => {

    const catalog = [

        // ── Scoring & Assessment ──────────────────────────────────

        {
            id: 'aba',
            name: 'Activity-Based Assessments (ABAs)',
            category: 'Scoring & Assessment',
            description: 'Automated scripts that validate whether learners completed tasks correctly, providing real-time pass/fail feedback.',
            keywords: ['create', 'configure', 'deploy', 'install', 'set up', 'build', 'provision', 'enable', 'modify', 'change setting'],
            nudge: 'This activity asks learners to complete a verifiable task. Consider adding an **Activity-Based Assessment** in Studio to automatically check their work and give immediate feedback.',
            docsUrl: 'https://docs.skillable.com/docs/activities',
        },
        {
            id: 'pbt',
            name: 'Performance-Based Testing (PBT)',
            category: 'Scoring & Assessment',
            description: 'Exam-mode scoring where learners complete all tasks first and submit for grading at the end, without per-item feedback.',
            keywords: ['exam', 'certification', 'assessment', 'test', 'validate', 'evaluate', 'high-stakes'],
            nudge: 'This lab looks assessment-oriented. Consider using **Performance-Based Testing** mode in Studio — learners complete all tasks before submitting for a final score, ideal for certification exams.',
            docsUrl: 'https://docs.skillable.com/docs/pbt-overview',
        },
        {
            id: 'scoring-bot',
            name: 'Scoring Bot',
            category: 'Scoring & Assessment',
            description: 'A hidden VM that runs assessment scripts against the learner\'s environment invisibly, keeping the scoring mechanism tamper-proof.',
            keywords: ['verify', 'validate', 'check', 'assess', 'score', 'grade'],
            nudge: 'For tamper-proof scoring, consider using a **Scoring Bot** in Studio — a hidden VM that runs assessment scripts against the learner\'s environment without them seeing the scoring mechanism.',
            docsUrl: 'https://docs.skillable.com/docs/scoring',
        },
        {
            id: 'script-library',
            name: 'Script Library',
            category: 'Scoring & Assessment',
            description: 'Centralized hub of reusable scoring and automation script templates with AI Copilot for assisted script generation.',
            keywords: ['script', 'powershell', 'bash', 'automate'],
            nudge: 'Before writing scoring scripts from scratch, check the **Script Library** in Studio for reusable templates. The Scripting Co-Pilot can also generate draft scripts from natural language descriptions.',
            docsUrl: 'https://docs.skillable.com/docs/using-the-script-library-1',
        },

        // ── Automation & Variables ─────────────────────────────────

        {
            id: 'lca',
            name: 'Life Cycle Actions (LCAs)',
            category: 'Automation & Variables',
            description: 'Scripts, notifications, or API calls that run automatically at specific lab events like build, first display, or tear down.',
            keywords: ['pre-configure', 'setup', 'initialize', 'prepare', 'before the learner', 'when the lab starts', 'tear down', 'clean up'],
            nudge: 'This lab needs environment setup before the learner begins. Consider using **Life Cycle Actions** in Studio to run setup scripts automatically on lab build or first display.',
            docsUrl: 'https://docs.skillable.com/docs/life-cycle-actions-5',
        },
        {
            id: 'replacement-tokens',
            name: 'Replacement Tokens',
            category: 'Automation & Variables',
            description: 'Dynamic placeholders (@lab. syntax) replaced at runtime with per-instance values like usernames, passwords, IPs, and resource names.',
            keywords: ['username', 'password', 'credential', 'login', 'sign in', 'IP address', 'URL', 'endpoint', 'connection string'],
            nudge: 'This step references credentials or dynamic values. In Studio, use **Replacement Tokens** (`@lab.` syntax) so each learner gets unique, auto-populated values instead of hardcoded ones.',
            docsUrl: 'https://docs.skillable.com/docs/replacement-tokens',
        },
        {
            id: 'variables',
            name: 'Variables & Variable Store',
            category: 'Automation & Variables',
            description: 'Named values scoped to a lab instance — set via learner input, scripts, or predefined values, and recalled anywhere in instructions.',
            keywords: ['enter a name', 'choose a value', 'type your', 'remember this', 'use this later', 'refer back', 'same value'],
            nudge: 'This step asks learners to enter or choose a value used later. In Studio, capture it with `@lab.TextBox()` and recall it with `@lab.Variable()` to keep instructions consistent throughout the lab.',
            docsUrl: 'https://docs.skillable.com/docs/variables',
        },
        {
            id: 'conditional-display',
            name: 'Conditional Instruction Display',
            category: 'Automation & Variables',
            description: 'Show or hide instruction sections dynamically based on variable values, enabling multi-audience or adaptive content paths.',
            keywords: ['if you are', 'depending on', 'for advanced users', 'for beginners', 'optional', 'choose your path', 'multiple scenarios'],
            nudge: 'This lab serves multiple skill levels or scenarios. In Studio, use **conditional display** to show or hide sections based on variables — one lab profile, multiple tailored experiences.',
            docsUrl: 'https://docs.skillable.com/docs/variably-display-instructions',
        },

        // ── Cloud & Infrastructure ────────────────────────────────

        {
            id: 'cloud-slice',
            name: 'Cloud Slice',
            category: 'Cloud & Infrastructure',
            description: 'Provisions isolated, temporary Azure subscriptions or AWS accounts per learner with access control policies.',
            keywords: ['azure', 'aws', 'cloud', 'subscription', 'portal', 'console', 'resource group', 'cloud environment'],
            nudge: 'This lab involves cloud platform tasks. Consider using **Cloud Slice** in Studio to automatically provision an isolated Azure/AWS environment per learner with access control policies.',
            docsUrl: 'https://docs.skillable.com/docs/cloud-slice-guide-microsoft-azure-setup',
        },
        {
            id: 'container-labs',
            name: 'Container Labs',
            category: 'Cloud & Infrastructure',
            description: 'Lightweight Docker containers instead of full VMs — supports web display for browser-based access and shared volumes.',
            keywords: ['docker', 'container', 'microservice', 'lightweight', 'programming', 'development environment', 'code editor'],
            nudge: 'For this development exercise, consider **Container Labs** in Studio instead of full VMs — lighter, faster, and supports browser-based IDEs via Container Web Display.',
            docsUrl: 'https://docs.skillable.com/docs/container-images',
        },
        {
            id: 'ide',
            name: 'Embedded IDEs',
            category: 'Cloud & Infrastructure',
            description: 'Browser-based VS Code, Jupyter, or other IDEs embedded directly in the lab via Container Web Display.',
            keywords: ['write code', 'coding', 'programming', 'script', 'python', 'javascript', 'notebook', 'IDE', 'VS Code', 'Jupyter'],
            nudge: 'This lab involves coding. Consider embedding a browser-based **IDE** (VS Code, Jupyter) in Studio via Container Web Display so learners can code directly in the lab.',
            docsUrl: 'https://docs.skillable.com/docs/container-web-display',
        },
        {
            id: 'custom-endpoints',
            name: 'Custom VM Endpoints',
            category: 'Cloud & Infrastructure',
            description: 'Expose SSH, RDP, HTTP, or VNC from VMs as dedicated tabs in the lab interface for direct access.',
            keywords: ['web application', 'web app', 'SSH', 'terminal', 'browser', 'access the service', 'open the portal'],
            nudge: 'Instead of having learners open a browser inside the VM, consider adding a **Custom VM Endpoint** in Studio to expose this web app as a dedicated tab in the lab interface.',
            docsUrl: 'https://docs.skillable.com/docs/custom-vm-endpoints',
        },
        {
            id: 'byoc',
            name: 'Bring Your Own Cloud (BYOC)',
            category: 'Cloud & Infrastructure',
            description: 'Enables labs targeting cloud platforms beyond Azure/AWS, or any web-based SaaS application.',
            keywords: ['GCP', 'Google Cloud', 'SaaS', 'third-party', 'external platform', 'Salesforce', 'ServiceNow'],
            nudge: 'This lab targets a platform outside Azure/AWS. Consider **Bring Your Own Cloud** in Studio to integrate external cloud platforms or SaaS applications into the lab experience.',
            docsUrl: 'https://docs.skillable.com/docs/introduction-to-custom-cloud-labs',
        },

        // ── Instructions & Content ────────────────────────────────

        {
            id: 'markdown-hints',
            name: 'Hint Blocks',
            category: 'Instructions & Content',
            description: 'Collapsible hint blocks that learners can optionally reveal when stuck.',
            keywords: ['hint', 'stuck', 'help', 'try this', 'if you need'],
            nudge: 'Use **Hint blocks** (`> [!hint]`) in Studio to wrap this guidance so learners can optionally reveal it only when they need help.',
            docsUrl: 'https://docs.skillable.com/docs/creating-instructions-with-markdown-syntax',
        },
        {
            id: 'markdown-knowledge',
            name: 'Knowledge Blocks',
            category: 'Instructions & Content',
            description: 'Collapsible blocks for supplementary information and deeper context that doesn\'t interrupt the main flow.',
            keywords: ['background', 'context', 'more information', 'deep dive', 'explanation', 'why this matters', 'how it works'],
            nudge: 'Wrap this background information in a **Knowledge block** (`> [!knowledge]`) in Studio so it\'s collapsible and doesn\'t clutter the main instructions.',
            docsUrl: 'https://docs.skillable.com/docs/creating-instructions-with-markdown-syntax',
        },
        {
            id: 'markdown-alert',
            name: 'Alert Blocks',
            category: 'Instructions & Content',
            description: 'Prominent warning blocks for critical information the learner must not skip.',
            keywords: ['warning', 'caution', 'important', 'do not', 'be careful', 'critical', 'must'],
            nudge: 'This is critical information. Use an **Alert block** (`> [!alert]`) in Studio to make sure learners don\'t miss it.',
            docsUrl: 'https://docs.skillable.com/docs/creating-instructions-with-markdown-syntax',
        },
        {
            id: 'type-text',
            name: 'Type Text & Copy to Clipboard',
            category: 'Instructions & Content',
            description: 'One-click text entry into VMs (+++text+++) or clipboard copy (++text++) to reduce typos.',
            keywords: ['type the command', 'enter the following', 'run this command', 'paste', 'copy', 'command line', 'CLI', 'terminal'],
            nudge: 'This step has commands for learners to type. In Studio, wrap them with `+++` (Type Text for VMs) or `++` (Copy to Clipboard for browsers) so learners can enter them with one click.',
            docsUrl: 'https://docs.skillable.com/docs/creating-instructions-with-markdown-syntax',
        },
        {
            id: 'instruction-sets',
            name: 'Instruction Sets',
            category: 'Instructions & Content',
            description: 'Multiple instruction variants for a single lab — different languages, skill levels, or audiences sharing the same environment.',
            keywords: ['multiple languages', 'localization', 'different audiences', 'beginner', 'advanced', 'variant'],
            nudge: 'If this lab serves multiple languages or skill levels, use **Instruction Sets** in Studio — one lab environment, multiple tailored instruction variants.',
            docsUrl: 'https://docs.skillable.com/docs/instruction-sets',
        },
        {
            id: 'external-instructions',
            name: 'Git-Based Instructions',
            category: 'Instructions & Content',
            description: 'Source lab instructions from GitHub/Azure DevOps/GitLab for version control, offline editing, and content reuse via !include syntax.',
            keywords: ['version control', 'git', 'reuse', 'shared content', 'template'],
            nudge: 'For version-controlled content management, consider storing instructions in a **Git repository** and using `!include` to share common modules across labs in Studio.',
            docsUrl: 'https://docs.skillable.com/docs/github-repository',
        },

        // ── AI & Advanced ─────────────────────────────────────────

        {
            id: 'ai-chat',
            name: 'AI Chat in Labs',
            category: 'AI & Advanced',
            description: 'Embeds a scoped AI chat directly in lab instructions so learners can ask questions without leaving the lab.',
            keywords: ['explain', 'understand', 'concept', 'theory', 'learn more', 'what is', 'how does'],
            nudge: 'Consider adding `ai-chat[topic]` in Studio here so learners can ask the AI questions about this concept without leaving the lab.',
            docsUrl: 'https://docs.skillable.com/docs/ai-menu-in-lab-instructions',
        },
        {
            id: 'ai-quiz',
            name: 'AI-Generated Quizzes',
            category: 'AI & Advanced',
            description: 'Auto-generates quiz questions on a topic for quick knowledge checks within the lab.',
            keywords: ['quiz', 'check understanding', 'knowledge check', 'review', 'test yourself'],
            nudge: 'Want a quick knowledge check here? Use `ai-quiz[topic]` in Studio to auto-generate quiz questions on the fly.',
            docsUrl: 'https://docs.skillable.com/docs/ai-menu-in-lab-instructions',
        },

        // ── Lab Management ────────────────────────────────────────

        {
            id: 'theming',
            name: 'Custom Theming (v2)',
            category: 'Lab Management',
            description: 'Custom CSS/JS for branded lab client appearance — colors, fonts, logos with theme inheritance.',
            keywords: ['brand', 'logo', 'customer-facing', 'white label', 'appearance', 'theme'],
            nudge: 'If this lab will be delivered under your organization\'s brand, consider applying a **custom theme** in Studio to match your colors, fonts, and logo.',
            docsUrl: 'https://docs.skillable.com/docs/theming-v2-lab-client',
        },
        {
            id: 'shared-labs',
            name: 'Shared Labs',
            category: 'Lab Management',
            description: 'Multi-user lab environments where participants share networks and interact with each other\'s VMs for collaborative scenarios.',
            keywords: ['team', 'collaborate', 'group exercise', 'role-play', 'multi-user', 'cyber range', 'red team', 'blue team'],
            nudge: 'This scenario involves multiple roles or teamwork. Consider configuring a **Shared Lab** in Studio so participants\' VMs can communicate for collaborative exercises.',
            docsUrl: 'https://docs.skillable.com/docs/shared-labs',
        },
        {
            id: 'diff-disks',
            name: 'Differencing Disks',
            category: 'Lab Management',
            description: 'Incremental VM snapshots for versioning environment changes without altering the base disk.',
            keywords: ['pre-install', 'pre-configure', 'snapshot', 'save state', 'base image'],
            nudge: 'After configuring VMs with required software, use **differencing disks** in Studio to capture and version the changes. Keep the disk chain short for performance.',
            docsUrl: 'https://docs.skillable.com/docs/virtual-machine-modifications-and-differencing-disks',
        },
        {
            id: 'api-webhooks',
            name: 'API & Webhook Integration',
            category: 'Lab Management',
            description: 'REST API for programmatic lab launches and webhooks for real-time event notifications to LMS platforms.',
            keywords: ['LMS', 'integration', 'API', 'webhook', 'LTI', 'SCORM', 'learning platform', 'completion data'],
            nudge: 'If this lab integrates with an LMS, consider setting up **LTI 1.3 or webhooks** in Studio to sync completion data and scores back to your learning platform automatically.',
            docsUrl: 'https://docs.skillable.com/docs/webhook-workflows',
        },
    ];

    // ── Public API ────────────────────────────────────────────────

    /**
     * Returns the full catalog.
     */
    function getAll() {
        return catalog;
    }

    /**
     * Returns features grouped by category.
     */
    function getByCategory() {
        const groups = {};
        for (const f of catalog) {
            if (!groups[f.category]) groups[f.category] = [];
            groups[f.category].push(f);
        }
        return groups;
    }

    /**
     * Given draft instruction text, returns relevant feature nudges
     * by scanning for keyword matches.
     */
    function suggestForText(text) {
        if (!text) return [];
        const lower = text.toLowerCase();
        const matches = [];
        for (const f of catalog) {
            const score = f.keywords.reduce((count, kw) => {
                return count + (lower.includes(kw.toLowerCase()) ? 1 : 0);
            }, 0);
            if (score > 0) {
                matches.push({ feature: f, score });
            }
        }
        // Sort by relevance (most keyword matches first), deduplicate
        matches.sort((a, b) => b.score - a.score);
        return matches.map(m => m.feature);
    }

    /**
     * Returns the top N most relevant nudges for a given draft text.
     */
    function topNudges(text, n = 3) {
        return suggestForText(text).slice(0, n);
    }

    return {
        getAll,
        getByCategory,
        suggestForText,
        topNudges,
    };

})();
