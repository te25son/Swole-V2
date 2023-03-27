module.exports = {
    autodiscover: false,
    onboardingConfig: {
        extends: ["config:base"],
    },
    onboarding: true,
    platform: "github",
    gitAuthor: "RenovateBot <renovatebot@swole.com>",
    enabledManagers: ["poetry"],
    lockFileMaintenance: {
        enabled: true
    },
    repositories: ["te25son/Swole-V2"]
}
