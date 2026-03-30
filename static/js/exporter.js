/**
 * exporter.js — Converts Lab Program Designer v3 data to Skillable Studio export format.
 * Generates ZIP packages containing data.json for Skillable Studio import.
 * Also provides BOM CSV export and clean JSON export.
 *
 * Depends on: Store (global IIFE), JSZip (loaded globally).
 */

const Exporter = (() => {

    let _idCounter = 100000;
    function nextId() { return _idCounter++; }

    // ── Platform mappings ───────────────────────────────────────

    const cloudPlatformMap = {
        'azure': 10,
        'aws': 20,
        'gcp': 30,
        'multi': 10,
        '': 0,
    };

    const platformUrlMap = {
        'azure': 'https://portal.azure.com',
        'aws': 'https://console.aws.amazon.com',
        'gcp': 'https://console.cloud.google.com',
        'multi': 'https://portal.azure.com',
    };

    // OS to Skillable VM profile mapping
    const osMap = {
        'windows-server': { os: 'Windows Server 2022', platformId: 2 },
        'windows-11': { os: 'Windows 11', platformId: 2 },
        'windows-10': { os: 'Windows 10', platformId: 2 },
        'ubuntu': { os: 'Ubuntu 22.04 LTS', platformId: 10 },
        'centos': { os: 'CentOS 8', platformId: 10 },
        'rhel': { os: 'Red Hat Enterprise Linux 8', platformId: 10 },
        'debian': { os: 'Debian 11', platformId: 10 },
        'custom': { os: 'Custom Image', platformId: 2 },
    };

    // Difficulty to Skillable Studio level mapping
    const levelMap = {
        'beginner': 100,
        'intermediate': 200,
        'advanced': 300,
        'expert': 400,
    };

    // Development status
    const statusMap = {
        'draft': 1,
        'review': 5,
        'published': 10,
    };

    // ── Skillable structure builders ─────────────────────────────

    /**
     * Build a Skillable-format network object.
     */
    function buildNetwork(name, type, id) {
        return {
            Id: id,
            Name: name,
            Description: null,
            PhysicalNetworkAdapterName: null,
            IsStudentVisible: false,
            DevelopmentOnly: false,
            Type: type, // 10 = Internet/NAT, 0 = Internal, 20 = Public IP
            VLanId: null,
            GatewayAddress: type === 10 ? '192.168.1.1' : null,
            SubnetMask: type === 10 ? '255.255.255.0' : null,
            EnableDhcp: type === 10,
            DhcpStart: type === 10 ? '192.168.1.100' : null,
            DhcpEnd: type === 10 ? '192.168.1.200' : null,
            SubnetId: null,
            EnableNat: false,
            CustomNetworkId: null,
            AccessControlListId: null,
            EnableEndpoints: false,
            EndpointGatewayIpAddress: null,
            EndpointGatewaySubnetMask: null,
        };
    }

    /**
     * Build a Skillable-format VM machine entry.
     */
    function buildMachine(vm, sortOrder, networkId, vmProfileId) {
        const machineId = nextId();
        const adapterId = nextId();
        const connectionId = nextId();
        return {
            Id: machineId,
            MachineProfileId: vmProfileId,
            DisplayName: vm.name || 'LabVM',
            IsStudentVisible: true,
            AutoStart: true,
            InitialSystemTime: null,
            IsHostTimeSyncEnabled: true,
            StartupDelaySeconds: null,
            SortOrder: sortOrder,
            FloppyMediaId: null,
            DvdMediaId: null,
            NetworkConnections: [
                {
                    Id: connectionId,
                    NetworkProfileId: networkId,
                    AdapterId: adapterId,
                    IsStudentVisible: false,
                },
            ],
            StartStateDisks: [],
            Endpoints: [],
            WaitForHeartbeat: true,
            ResumeOrder: sortOrder,
            ResumeDelaySeconds: null,
            ReplacementTokenAlias: vm.name || 'LabVM',
            AllowDesktopConnections: true,
            AllowSshConnections: _isLinuxOs(vm.os),
            TrackLabInstanceData: false,
        };
    }

    /**
     * Build a Skillable-format VM profile.
     */
    function buildVMProfile(vm, seriesId) {
        const osInfo = osMap[vm.os] || osMap['windows-11'];
        const profileId = nextId();
        const adapterId = nextId();
        const scsiId = nextId();
        const diskId = nextId();
        const dvdId = nextId();
        const ramMb = vm.ram || 8192;

        return {
            id: profileId,
            profile: {
                Id: profileId,
                SeriesId: seriesId,
                Name: vm.name || 'LabVM',
                Description: `${osInfo.os} virtual machine for lab environment.`,
                PlatformId: osInfo.platformId,
                OperatingSystem: osInfo.os,
                Ram: ramMb,
                HostIntegrationEnabled: true,
                Username: 'LabUser',
                Password: 'Pa$$w0rd',
                ScreenWidth: 1024,
                ScreenHeight: 768,
                Cmos: null,
                BootOrder: '1,2,3,0',
                EnableDynamicScreenResizing: true,
                OperatingSystemValue: osInfo.platformId === 2 ? 'windows9_64Guest' : 'ubuntu64Guest',
                EnableNestedVirtualization: false,
                HideVirtualizationFromGuestOs: false,
                NumProcessors: 4,
                NumCoresPerProcessor: 1,
                VideoRam: 32,
                Enable3DVideo: false,
                EnableHostCompatibility: true,
                RdpFileText: null,
                HardDisks: [
                    {
                        Id: diskId,
                        FilePath: `Placeholder\\${vm.name || 'LabVM'}\\disk.vhdx`,
                        ScsiAdapterId: scsiId,
                        AttachmentIndex: 0,
                        SortOrder: 0,
                        DifferencingDiskId: null,
                        IsOsDisk: true,
                    },
                ],
                NetworkAdapters: [
                    {
                        Id: adapterId,
                        Name: 'NIC0',
                        EthernetAddress: '00155D018000',
                        HardwareId: null,
                        IsLegacy: false,
                        AllowMacSpoofing: false,
                        VLanId: null,
                        SortOrder: 0,
                        TypeId: 0,
                        MonitoringMode: 0,
                    },
                ],
                ScsiAdapters: [
                    {
                        Id: scsiId,
                        ScsiId: 7,
                        IsBusShared: false,
                        TypeId: 0,
                        SortOrder: 0,
                    },
                ],
                DvdRomDrives: [
                    {
                        Id: dvdId,
                        AttachmentIndex: 1,
                        ScsiAdapterId: scsiId,
                    },
                ],
                TargetResourceGroup: null,
                CloudOperatingSystemType: 0,
                DiskType: 0,
                UseCloudHybridBenefit: false,
                Enabled: true,
                AllowDiskUpdatesInLabConsole: true,
                Generation: 2,
                HardwareVersion: 14,
                UseEnhancedSessionMode: true,
                ColorDepth: 0,
                RedirectSmartCards: false,
                RedirectPrinters: false,
                RedirectDrives: false,
                RedirectDevices: false,
                CaptureAudioInput: false,
                RedirectAudioOutput: false,
                RedirectClipboard: true,
                AttemptAutoLogon: false,
                AllowDesktopWallpaper: false,
                EnableFontSmoothing: true,
                MachineType: 'A0',
                ExternalMachineImage: null,
                ExternalMachineImageRegion: null,
                ExternalMachineImageAccount: null,
                UseAzureMarketplaceImage: false,
                AzureMarketplaceImagePlanId: null,
                AzureMarketplaceImageProductId: null,
                AzureMarketplaceImagePublisherId: null,
                BiosGuid: null,
                EnableTrustedPlatformModule: true,
                EnableSecureBoot: true,
                UseEfi: false,
            },
        };
    }

    /**
     * Build instructions markdown from v3 blueprint activities and draft instructions.
     * Uses === page separators between activities (Skillable markdown format).
     */
    function buildInstructionsMarkdown(blueprint, draftMarkdown) {
        // If there is a draft instruction, use it directly
        if (draftMarkdown) {
            return draftMarkdown;
        }

        // Otherwise generate from activities
        const activities = blueprint.activities || [];
        if (activities.length === 0) return '';

        const sections = activities.map((activity, idx) => {
            let md = `# Exercise ${idx + 1}: ${activity.title || 'Untitled Exercise'}\n\n`;
            if (activity.description) {
                md += activity.description + '\n\n';
            }
            if (Array.isArray(activity.tasks)) {
                activity.tasks.forEach((task, tIdx) => {
                    md += `## Task ${tIdx + 1}: ${typeof task === 'string' ? task : (task.title || task)}\n\n`;
                    if (task.instructions) {
                        md += task.instructions + '\n\n';
                    }
                });
            }
            return md;
        });

        return sections.join('\n===\n\n');
    }

    /**
     * Build cloud resource groups from environment template.
     */
    function buildCloudResourceGroups(template, labProfileId) {
        const resources = template.cloudResources || [];
        if (resources.length === 0 && template.platform) {
            return [{
                Id: nextId(),
                DisplayName: 'ResourceGroup1',
                ReplacementTokenAlias: 'ResourceGroup1',
                LabProfileId: labProfileId,
                CloudTemplateResourceGroups: [],
                CloudResourceParameterValues: [],
                AccessControlPolicyResourceGroups: [],
                CloudQuotaResourceGroups: [],
            }];
        }
        return resources.map((res, idx) => ({
            Id: nextId(),
            DisplayName: res.name || `Resource${idx + 1}`,
            ReplacementTokenAlias: (res.name || `Resource${idx + 1}`).replace(/[^a-zA-Z0-9]/g, ''),
            LabProfileId: labProfileId,
            CloudTemplateResourceGroups: [],
            CloudResourceParameterValues: [],
            AccessControlPolicyResourceGroups: [],
            CloudQuotaResourceGroups: [],
        }));
    }

    /**
     * Build credential profiles JSON for cloud platform.
     */
    function buildCredentialProfilesJson(platform) {
        if (!platform) return null;
        return JSON.stringify([{
            LocalId: 1,
            ResourceGroupPermissionMappings: [{
                Id: 1,
                ResourceGroupName: 'ResourceGroup1',
                PermissionId: 'b24988ac-6180-42a0-ab88-20f7382dd24c',
            }],
            SubscriptionPermissionMappings: [{
                Id: 1,
                PermissionId: 'b24988ac-6180-42a0-ab88-20f7382dd24c',
            }],
            AccountNamePrefix: 'User1-',
            ReplacementTokenAlias: 'User1',
        }]);
    }

    /**
     * Build LifeCycleActions from Phase 4 lifecycle scripts.
     */
    function buildLifeCycleActions(lifecycleScripts, templateId, vmProfiles) {
        const actions = [];

        const scriptData = (lifecycleScripts || {})[templateId];
        if (!scriptData) return actions;

        const targetId = vmProfiles.length > 0 ? vmProfiles[0].id : null;
        const isPS = (scriptData.platform || 'powershell') !== 'bash';
        const scriptLanguage = isPS ? 0 : 1; // 0 = PowerShell, 1 = Bash

        // Build script (Event 10 = Running / lab start)
        if (scriptData.buildScript && scriptData.buildScript.trim()) {
            actions.push({
                Id: nextId(),
                Name: 'Environment Build Script',
                Event: 10,
                ActionType: 40,
                Url: null,
                HttpVerb: 0,
                Synchronous: true,
                ErrorAction: 0,
                Timeout: 1200,
                SortOrder: 0,
                AppendLabData: false,
                CustomErrorNotification: null,
                HttpHeaders: null,
                HttpContent: null,
                Notification: null,
                Subject: null,
                ScriptTargetId: targetId,
                ScriptLanguage: scriptLanguage,
                Script: scriptData.buildScript,
                ScriptDescription: 'Provisions the environment for this lab.',
                ScriptGuidance: null,
                ScriptSource: 0,
                Delay: 0,
                Enabled: true,
                NotificationName: null,
                ScriptEngineImageId: 5,
                ScriptEnginePackagesJson: null,
                RepeatScriptUntilTrue: false,
                RepeatScriptIntervalSeconds: 60,
                RepeatScriptTimeoutMinutes: 20,
                MaxRetries: 1,
                CopilotPromptJson: null,
                RunWithElevatedPermissions: true,
            });
        }

        // Teardown script (Event 20 = Tearing Down)
        if (scriptData.teardownScript && scriptData.teardownScript.trim()) {
            actions.push({
                Id: nextId(),
                Name: 'Environment Teardown Script',
                Event: 20,
                ActionType: 40,
                Url: null,
                HttpVerb: 0,
                Synchronous: true,
                ErrorAction: 0,
                Timeout: 600,
                SortOrder: 1,
                AppendLabData: false,
                CustomErrorNotification: null,
                HttpHeaders: null,
                HttpContent: null,
                Notification: null,
                Subject: null,
                ScriptTargetId: targetId,
                ScriptLanguage: scriptLanguage,
                Script: scriptData.teardownScript,
                ScriptDescription: 'Cleans up the environment after lab completion.',
                ScriptGuidance: null,
                ScriptSource: 0,
                Delay: 0,
                Enabled: true,
                NotificationName: null,
                ScriptEngineImageId: 5,
                ScriptEnginePackagesJson: null,
                RepeatScriptUntilTrue: false,
                RepeatScriptIntervalSeconds: 60,
                RepeatScriptTimeoutMinutes: 10,
                MaxRetries: 1,
                CopilotPromptJson: null,
                RunWithElevatedPermissions: true,
            });
        }

        return actions;
    }

    // ── Helpers ──────────────────────────────────────────────────

    function _isLinuxOs(os) {
        if (!os) return false;
        const lower = os.toLowerCase();
        return ['ubuntu', 'centos', 'rhel', 'debian', 'linux', 'suse'].some(k => lower.includes(k));
    }

    /**
     * Find the best matching environment template for a given blueprint.
     * Heuristic: first template (shared environment), or match by name similarity.
     */
    function _findTemplateForBlueprint(blueprint, templates) {
        if (!templates || templates.length === 0) return null;
        // Simple: return first template (shared environment approach)
        return templates[0];
    }

    /**
     * Determine platform from environment templates.
     */
    function _getPlatformFromTemplates(templates) {
        if (!templates || templates.length === 0) return '';
        const platforms = [...new Set(templates.map(t => t.platform).filter(Boolean))];
        if (platforms.length === 0) return '';
        if (platforms.length === 1) return platforms[0];
        return 'multi';
    }

    // ── Main export: project to Skillable Studio ────────────────────

    /**
     * Convert a v3 project to Skillable Studio export format.
     * Creates a Lab Series with Lab Profiles for each blueprint.
     */
    function projectToSkillable(project, options) {
        _idCounter = Math.floor(Math.random() * 100000) + 200000;

        const seriesId = nextId();
        const templates = project.environmentTemplates || [];
        const blueprints = project.labBlueprints || [];
        const draftInstructions = project.draftInstructions || {};
        const lifecycleScripts = project.lifecycleScripts || {};
        const selectedIds = (options && options.labIds) || blueprints.map(bp => bp.id);

        const selectedBlueprints = blueprints.filter(bp => selectedIds.includes(bp.id));
        const platform = _getPlatformFromTemplates(templates);
        const cloudPlatform = cloudPlatformMap[platform] || 0;

        // Lab Series
        const labSeries = {
            Id: seriesId,
            Name: project.name || 'Lab Series',
            Description: `Lab series generated from Lab Program Designer project: ${project.name || 'Untitled'}`,
        };

        // Build all VM profiles across all templates
        const allVMProfiles = [];
        const templateVMMap = {}; // templateId -> [{ id, profile }]
        for (const tpl of templates) {
            const vms = tpl.vms || [];
            templateVMMap[tpl.id] = [];
            for (const vm of vms) {
                const vpResult = buildVMProfile(vm, seriesId);
                allVMProfiles.push(vpResult);
                templateVMMap[tpl.id].push(vpResult);
            }
        }

        // Build Lab Profiles
        const labProfiles = selectedBlueprints.map((bp, seriesIndex) => {
            const labProfileId = nextId();
            const template = _findTemplateForBlueprint(bp, templates);
            const tplId = template ? template.id : null;
            const tplPlatform = template ? template.platform : platform;
            const tplCloudPlatform = cloudPlatformMap[tplPlatform] || cloudPlatform;

            // VMs from matched template
            const vmProfiles = tplId ? (templateVMMap[tplId] || []) : [];
            const vms = template ? (template.vms || []) : [];

            // Networks
            const internetNetworkId = nextId();
            const networks = [buildNetwork('Internet', 10, internetNetworkId)];

            // Machines
            const machines = vms.map((vm, idx) => {
                const vpResult = vmProfiles[idx];
                return vpResult ? buildMachine(vm, idx, internetNetworkId, vpResult.id) : null;
            }).filter(Boolean);

            // Instructions
            const draftMd = draftInstructions[bp.id] || '';
            const instructionsMarkdown = buildInstructionsMarkdown(bp, draftMd);

            // Instructions Sets
            const instructionsSets = [];
            if (instructionsMarkdown) {
                instructionsSets.push({
                    Id: nextId(),
                    Name: 'Base Instructions Set',
                    Enabled: true,
                    Instructions: instructionsMarkdown,
                    DisplayId: 'Base-01',
                    LabTitle: bp.title || 'Untitled Lab',
                    DurationMinutes: bp.estimatedDuration || 60,
                    LanguageId: 1,
                    AiTranslationStatus: 0,
                    PassingScore: 1,
                    RawCutoffScore: 1,
                    ScoringResultsDisplayType: 10,
                    EndOfLabScoreType: 0,
                    ScoringMode: 0,
                    EnableTaskProgressTracking: true,
                    EnableTaskAutoChecking: false,
                    RequireTasksCompletedInOrder: false,
                    VariablesJson: null,
                    ReplacementsJson: null,
                    OrganizationId: 4997,
                    Editable: true,
                });
            }

            // Cloud resource groups
            const cloudResourceGroups = (tplPlatform && template)
                ? buildCloudResourceGroups(template, labProfileId)
                : [];

            // Products
            const products = [];
            if (tplPlatform === 'azure' || tplPlatform === 'multi') {
                products.push({ LabProfileId: labProfileId, ProductId: 20, Name: 'Azure' });
            }
            if (tplPlatform === 'aws' || tplPlatform === 'multi') {
                products.push({ LabProfileId: labProfileId, ProductId: 30, Name: 'AWS' });
            }
            if (tplPlatform === 'gcp' || tplPlatform === 'multi') {
                products.push({ LabProfileId: labProfileId, ProductId: 40, Name: 'GCP' });
            }

            // Lifecycle actions
            const lifeCycleActions = tplId
                ? buildLifeCycleActions(lifecycleScripts, tplId, vmProfiles)
                : [];

            const duration = bp.estimatedDuration || 60;

            return {
                ContentVersion: 2,
                HasContent: true,
                Id: labProfileId,
                SourceUrl: null,
                SeriesId: seriesId,
                SeriesIndex: seriesIndex + 1,
                Name: bp.title || 'Untitled Lab',
                Sku: null,
                Number: bp.id ? `LAB-${bp.id.toUpperCase().slice(0, 8)}` : null,
                PlatformId: vms.length > 0 ? 2 : (tplCloudPlatform > 0 ? 3 : 2),
                DevelopmentStatusId: statusMap['draft'],
                Level: levelMap['intermediate'],
                DurationMinutes: duration,
                Description: bp.shortDescription || null,
                Enabled: false,
                ShowNavigationPane: true,
                AllowCancel: true,
                AllowSave: false,
                EnableAutoSave: false,
                LastConsoleSyncTimeoutMinutes: Math.max(duration, 15),
                LastActivityTimeoutMinutes: Math.max(duration, 120),
                EnableExpirationNotificationEmail: false,
                ExpirationNotificationEmailMinutes: 0,
                EnableScheduledDisablement: false,
                ScheduledDisableDateTime: null,
                MinimumAutoSaveTimeInvestment: 5,
                MaxSnapshots: 0,
                HasVirtualMachinePool: false,
                InheritLifeCycleActions: false,
                Networks: networks,
                Machines: machines,
                RemovableMediaIds: [],
                MachinePool: [],
                MachinePoolMembers: [],
                Resources: [],
                ContainerImages: [],
                ContainerNetworks: [],
                ContainerVolumeIds: [],
                CloudPortalCredentialProfilesJson: tplPlatform ? buildCredentialProfilesJson(tplPlatform) : null,
                LifeCycleActions: lifeCycleActions,
                CodeLanguages: null,
                CodeTests: null,
                EnableCodeLabFabric: false,
                CloudSubscriptionInstancePolicies: [],
                CloudScriptContextPolicies: [],
                CloudSubscriptionInstanceQuotas: [],
                CloudResourceGroups: cloudResourceGroups,
                CloudCredentialPoolAssignments: [],
                Activities: [],
                ActivityGroups: [],
                InstructionsSets: instructionsSets,
                LabProfileMappedProductMetadata: null,
                Products: products,
                MinInstanceStorageGb: 20,
                AllowTimeExtensions: true,
                Ram: vms.length > 0 ? vms.reduce((sum, vm) => sum + (vm.ram || 8192), 0) : 0,
                NavigationBarWidth: 400,
                PreinstanceBatchSize: 1,
                PreinstanceStockLevel: 0,
                SavePreinstances: true,
                PreinstanceSaveDelaySeconds: 0,
                ShowContentTab: true,
                ShowMachinesTab: vms.length > 0,
                ShowSupportTab: true,
                EndUrl: null,
                OwnerName: null,
                OwnerEmail: null,
                CustomContentTabLabel: null,
                CustomMachinesTabLabel: null,
                CustomSupportTabLabel: null,
                CloudPlatform: tplCloudPlatform,
                IntroductionContentUrl: null,
                IntroductionContentMinimumDisplaySeconds: null,
                AnonymousLaunchExpires: null,
                AnonymousSaveMaxDays: 7,
                AnonymousSaveMaxSessions: 5,
                ShowTimer: true,
                StorageLoadingPriority: 20,
                InheritStorageAvailability: true,
                CloudSubscriptionPoolId: null,
                EnableNavigationWarning: true,
                ShowVirtualMachinePowerOptions: true,
                StartStateDirectoryPath: null,
                EnableInstanceLinkSharing: false,
                EnableCopyPaste: true,
                LtiOutcomeScoringPolicy: 0,
                LtiOutcomeScoringFormat: 0,
                LtiOutcomePassingScoreMinutes: 15,
                LtiOutcomePassingScoreTaskCompletePercentage: 70,
                DefaultVirtualMachineProfileId: vmProfiles.length > 0 ? vmProfiles[0].id : null,
                DefaultVirtualMachineLabPoolProfileId: null,
                DefaultResourceId: null,
                NumVirtualMachines: vms.length,
                NumPublicIpAddresses: 0,
                RequiresNestedVirtualization: false,
                PremiumPrice: null,
                CustomPremiumPrice: null,
                ExpectedCloudCost: null,
                OverrideScriptContext: false,
                RunScriptAsAdmin: false,
                CloudPortalUrl: platformUrlMap[tplPlatform] || null,
                OverrideCloudPortalUrl: false,
                EnableAutomaticPortalLogin: false,
                DeployDefaultResources: false,
                AppendLabDataToCloudPortalUrl: false,
                TerminateOnFailedDeployment: true,
                SendNotificationOnFailedDeployment: false,
                TimeExtensionMinutes: 15,
                TimeExtensionShowNotificationMinutes: 10,
                EnableBugReporting: false,
                BugReportEmailAddress: null,
                DisplayDelaySeconds: null,
                DisplayDelayMessage: null,
                MaxActiveLabInstances: null,
                ThemeId: null,
                Tags: [],
                LabHostTags: [],
                NumVcpus: vms.length > 0 ? vms.length * 4 : 0,
                LabFabricBuildSequence: 0,
                AllowDisconnect: false,
                CloudDatacenterAvailability: [],
                RecordRdpSession: false,
                MaxAllowedBuildMinutes: 60,
                MaxAllowedBuildTimeAction: 10,
                DefaultLanguageId: 1,
                DefaultInstructionsDisplayId: 'Base-01',
                ShowInstructionsWhileBuilding: false,
                MaxAiTokensPerLabInstance: 100000,
                MaxAiTokensPerLabInstanceCustomMessage: null,
                ExamScoringItems: [],
                Exercises: [],
                AllowMultipleActiveInstancesPerUser: false,
                AllowLabInstanceNaming: false,
                NumExposedContainerPorts: 0,
                ExamShowResult: false,
                ExamShowResultDetails: false,
                IsExam: false,
                ExamPassingScore: 0,
                Instructions: null,
                EnableTaskProgressTracking: true,
                RequireTasksCompletedInOrder: false,
                EnableTaskAutoChecking: false,
                VariablesJson: null,
                InstructionsReplacementsJson: null,
                LanguageId: 0,
            };
        });

        return {
            SourceId: 'lab-designer-v3',
            LabSeries: [labSeries],
            LabProfiles: labProfiles,
            VirtualMachineProfiles: allVMProfiles.map(vp => vp.profile),
            RemovableMedia: [],
            CloudTemplates: [],
            AccessControlPolicies: [],
            CloudQuotas: [],
            AccessControlLists: [],
            ContainerImages: [],
            ContainerVolumes: [],
        };
    }

    // ── Export as Skillable ZIP ──────────────────────────────────

    /**
     * Export project to Skillable Studio format as a downloadable ZIP.
     * @param {object} project — full v3 project object
     * @param {object} options — { labIds: string[] } which labs to include
     */
    async function exportToSkillable(project, options) {
        if (!project) throw new Error('No project provided.');

        if (typeof JSZip === 'undefined') {
            throw new Error('JSZip library not loaded. Cannot create ZIP files.');
        }

        const exported = projectToSkillable(project, options);
        const json = JSON.stringify(exported, null, 2);

        const zip = new JSZip();
        zip.file('data.json', json);

        // Add content folder placeholders for each lab profile
        for (const lp of exported.LabProfiles) {
            zip.folder(`content/${lp.Id}`);
        }

        const blob = await zip.generateAsync({
            type: 'blob',
            compression: 'DEFLATE',
            compressionOptions: { level: 6 },
        });

        const filename = _sanitizeFilename(project.name || 'lab-export') + '-skillable.zip';
        _downloadBlob(filename, blob);

        return { filename, labCount: exported.LabProfiles.length };
    }

    // ── Export BOM as CSV ────────────────────────────────────────

    /**
     * Generate a CSV string from a bill of materials array.
     * @param {Array} billOfMaterials — array of { category, item, details, required }
     * @returns {string} CSV content
     */
    function exportBOMAsCSV(billOfMaterials) {
        const headers = ['Category', 'Item', 'Details', 'Required'];
        const rows = (billOfMaterials || []).map(item => [
            _csvEscape(item.category || ''),
            _csvEscape(item.item || ''),
            _csvEscape(item.details || ''),
            item.required ? 'Yes' : 'No',
        ].join(','));

        return [headers.join(','), ...rows].join('\n');
    }

    // ── Export Labs as JSON ──────────────────────────────────────

    /**
     * Export all labs in a clean JSON format with instructions.
     * @param {object} project — full v3 project object
     * @returns {string} JSON string
     */
    function exportLabsAsJSON(project) {
        const blueprints = project.labBlueprints || [];
        const draftInstructions = project.draftInstructions || {};

        const labs = blueprints.map((bp, idx) => ({
            index: idx + 1,
            id: bp.id,
            title: bp.title || 'Untitled Lab',
            shortDescription: bp.shortDescription || '',
            estimatedDuration: bp.estimatedDuration || null,
            activities: (bp.activities || []).map(a => ({
                title: a.title,
                tasks: a.tasks || [],
                duration: a.duration || null,
            })),
            approved: bp.approved || null,
            draftInstructions: draftInstructions[bp.id] || null,
        }));

        return JSON.stringify({
            projectName: project.name,
            exportedAt: new Date().toISOString(),
            labCount: labs.length,
            labs,
        }, null, 2);
    }

    // ── Utility functions ───────────────────────────────────────

    function _sanitizeFilename(name) {
        return name
            .replace(/[^a-zA-Z0-9\s\-_]/g, '')
            .replace(/\s+/g, '-')
            .trim()
            .slice(0, 80);
    }

    function _downloadBlob(filename, blob) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    function _csvEscape(value) {
        const str = String(value);
        if (str.includes(',') || str.includes('"') || str.includes('\n')) {
            return '"' + str.replace(/"/g, '""') + '"';
        }
        return str;
    }

    // ── Public API ──────────────────────────────────────────────

    return {
        projectToSkillable,
        exportToSkillable,
        exportBOMAsCSV,
        exportLabsAsJSON,
    };
})();
