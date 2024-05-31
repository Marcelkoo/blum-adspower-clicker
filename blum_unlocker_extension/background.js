chrome.runtime.onInstalled.addListener(() => {
    const ruleId = 1;
    const dynamicRules = {
        addRules: [
            {
                id: ruleId,
                priority: 1,
                action: {
                    type: "modifyHeaders",
                    responseHeaders: [
                        { header: "content-security-policy", operation: "remove" },
                        { header: "x-frame-options", operation: "remove" }
                    ]
                },
                condition: {
                    urlFilter: "telegram.blum.codes",
                    resourceTypes: ["main_frame", "sub_frame"]
                }
            }
        ],
        removeRuleIds: [ruleId]
    };

    chrome.declarativeNetRequest.updateDynamicRules(dynamicRules);
});
