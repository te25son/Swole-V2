module.exports = {
    autodiscover: true,
    onboardingConfig: {
        extends: ["config:base"],
    },
    onboarding: true,
    platform: "github",
    gitAuthor: "RenovateBot <renovatebot@rossum.ai>",
    enabledManagers: ["poetry"],
    lockFileMaintenance: {
        enabled: true
    }
}
