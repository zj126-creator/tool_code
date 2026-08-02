/**
 * Background Service Worker
 * 处理右键菜单、快捷键、翻译请求中转
 */

// ── 右键菜单初始化 ──
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "translate-page",
    title: "翻译此页面为简体中文",
    contexts: ["page"]
  });

  chrome.contextMenus.create({
    id: "translate-selection",
    title: "翻译选中的文字为简体中文",
    contexts: ["selection"]
  });
});

// ── 右键菜单点击 ──
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "translate-page") {
    chrome.tabs.sendMessage(tab.id, { action: "toggleTranslation" });
  } else if (info.menuItemId === "translate-selection") {
    chrome.tabs.sendMessage(tab.id, {
      action: "translateSelection",
      text: info.selectionText
    });
  }
});

// ── 快捷键 ──
chrome.commands.onCommand.addListener((command) => {
  if (command === "toggle-translation") {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0]) {
        chrome.tabs.sendMessage(tabs[0].id, { action: "toggleTranslation" });
      }
    });
  }
});

// ── 翻译 API 中转（避免 content script 跨域问题）──
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "fetchTranslation") {
    fetchTranslation(request.text, request.sourceLang || "auto")
      .then(result => sendResponse({ success: true, data: result }))
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true; // 保持消息通道开启
  }
});

/**
 * 调用 Google 翻译 API（免费接口）
 * @param {string} text - 待翻译文本
 * @param {string} sourceLang - 源语言（auto=自动检测）
 * @returns {Promise<string>} 翻译结果
 */
async function fetchTranslation(text, sourceLang = "auto") {
  const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=${sourceLang}&tl=zh-CN&dt=t&q=${encodeURIComponent(text)}`;

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`翻译请求失败: ${response.status}`);
  }

  const data = await response.json();
  // Google 返回嵌套数组，拼接所有翻译片段
  let result = "";
  if (data && data[0]) {
    for (const segment of data[0]) {
      if (segment[0]) {
        result += segment[0];
      }
    }
  }

  // 检测的源语言
  const detectedLang = data && data[2] ? data[2] : "unknown";

  return { translatedText: result, detectedLang };
}
