/** @type {import('cz-git').UserConfig} */
module.exports = {
    prompt: {
        issuePrefixes: [
            { value: 'fixes', name: 'fixes:   ISSUES that are fixed by these changes' },
        ],
        markBreakingChangeMode: true,
        customIssuePrefixAlign: "bottom",
        useAI: !!process.env.CZ_OPENAI_API_KEY,
        useEmoji: true,
        emojiAlign: 'left',
        customScopesAlign: 'top',
    }
}
