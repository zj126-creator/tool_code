/**
 * Content Script — 页面翻译核心逻辑
 * 负责：整页翻译、划词翻译、原文/译文对照显示
 */

// ── 状态管理 ──
let isTranslating = false;
let translatedNodes = new Map(); // 记录已翻译节点：node -> { original, translated, wrapper }

// ── 工具函数 ──

/**
 * 判断节点是否包含可翻译的文本
 */
function hasText(node) {
  return node.nodeType === Node.TEXT_NODE &&
         node.textContent.trim().length > 2 &&
         /[a-zA-Z]/.test(node.textContent);
}

/**
 * 获取页面上所有可翻译的文本节点
 */
function getTextNodes(root) {
  const walker = document.createTreeWalker(
    root || document.body,
    NodeFilter.SHOW_TEXT,
    {
      acceptNode(node) {
        if (!hasText(node)) return NodeFilter.FILTER_REJECT;

        // 排除 script、style、textarea 等标签内
        const parent = node.parentElement;
        if (!parent) return NodeFilter.FILTER_REJECT;
        const tag = parent.tagName.toLowerCase();
        const excludeTags = ["script", "style", "textarea", "input", "noscript", "code", "pre"];
        if (excludeTags.includes(tag)) return NodeFilter.FILTER_REJECT;

        // 排除已经翻译过的
        if (translatedNodes.has(node)) return NodeFilter.FILTER_REJECT;

        return NodeFilter.FILTER_ACCEPT;
      }
    }
  );

  const nodes = [];
  let current;
  while ((current = walker.nextNode())) {
    nodes.push(current);
  }
  return nodes;
}

/**
 * 发送翻译请求（通过 background 中转）
 */
function translateText(text) {
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage(
      { action: "fetchTranslation", text: text, sourceLang: "auto" },
      (response) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
        } else if (response && response.success) {
          resolve(response.data);
        } else {
          reject(new Error(response ? response.error : "翻译失败"));
        }
      }
    );
  });
}

// ── 整页翻译 ──

/**
 * 切换整页翻译状态
 */
async function toggleTranslation() {
  if (isTranslating) {
    restoreOriginal();
    return;
  }

  isTranslating = true;
  showStatus("正在翻译页面…");

  try {
    const textNodes = getTextNodes();
    let translated = 0;
    const batchSize = 20;

    for (let i = 0; i < textNodes.length; i += batchSize) {
      const batch = textNodes.slice(i, i + batchSize);

      await Promise.all(batch.map(async (node) => {
        try {
          const original = node.textContent.trim();
          if (!original) return;

          const result = await translateText(original);
          if (result.translatedText && result.translatedText !== original) {
            applyBilingualDisplay(node, original, result.translatedText);
            translated++;
          }
        } catch (e) {
          // 单个节点翻译失败不影响整体
          console.warn("翻译节点失败:", e.message);
        }
      }));

      // 更新进度
      showStatus(`正在翻译… ${Math.min(i + batchSize, textNodes.length)}/${textNodes.length}`);
    }

    showStatus(`翻译完成，共翻译 ${translated} 处`);
    setTimeout(hideStatus, 3000);
  } catch (err) {
    showStatus("翻译出错: " + err.message);
    setTimeout(hideStatus, 5000);
  }
}

/**
 * 应用双语对照显示
 * 将原文和译文同时显示，原文用灰色小字，译文用正常样式
 */
function applyBilingualDisplay(node, original, translated) {
  const parent = node.parentElement;
  if (!parent) return;

  // 创建译文 span
  const translatedSpan = document.createElement("span");
  translatedSpan.className = "ct-translated";
  translatedSpan.textContent = " " + translated;
  translatedSpan.setAttribute("data-original", original);

  // 保存原始状态
  translatedNodes.set(node, {
    original: original,
    translated: translated,
    parent: parent,
    nextSibling: node.nextSibling
  });

  // 在原文后插入译文
  parent.insertBefore(translatedSpan, node.nextSibling);
}

/**
 * 恢复原文（移除译文）
 */
function restoreOriginal() {
  for (const [node, info] of translatedNodes) {
    // 移除插入的译文 span
    const parent = info.parent;
    if (parent) {
      const spans = parent.querySelectorAll(".ct-translated");
      spans.forEach(s => s.remove());
    }
  }
  translatedNodes.clear();
  isTranslating = false;
  hideStatus();
}

// ── 划词翻译 ──

/**
 * 处理选中文字翻译
 */
async function translateSelection(text) {
  // 移除已有的翻译浮窗
  removeExistingPopup();

  // 创建浮窗
  const popup = document.createElement("div");
  popup.className = "ct-selection-popup";
  popup.innerHTML = `
    <div class="ct-popup-header">
      <span class="ct-popup-title">翻译结果</span>
      <span class="ct-popup-close">✕</span>
    </div>
    <div class="ct-popup-loading">翻译中…</div>
  `;

  document.body.appendChild(popup);
  positionPopup(popup);

  // 关闭按钮
  popup.querySelector(".ct-popup-close").addEventListener("click", () => {
    popup.remove();
  });

  try {
    const result = await translateText(text);
    const langMap = {
      "en": "英语", "ja": "日语", "ko": "韩语", "fr": "法语",
      "de": "德语", "es": "西班牙语", "ru": "俄语",
      "pt": "葡萄牙语", "it": "意大利语", "vi": "越南语",
      "th": "泰语", "ar": "阿拉伯语"
    };
    const langName = langMap[result.detectedLang] || result.detectedLang || "未知";

    popup.innerHTML = `
      <div class="ct-popup-header">
        <span class="ct-popup-title">翻译结果</span>
        <span class="ct-popup-lang">${langName} → 简体中文</span>
        <span class="ct-popup-close">✕</span>
      </div>
      <div class="ct-popup-original">${escapeHtml(text)}</div>
      <div class="ct-popup-translated">${escapeHtml(result.translatedText)}</div>
    `;

    popup.querySelector(".ct-popup-close").addEventListener("click", () => {
      popup.remove();
    });
  } catch (err) {
    popup.querySelector(".ct-popup-loading").textContent = "翻译失败: " + err.message;
  }
}

/**
 * 定位翻译浮窗到选中文字附近
 */
function positionPopup(popup) {
  const selection = window.getSelection();
  if (selection.rangeCount > 0) {
    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    const top = rect.bottom + window.scrollY + 10;
    let left = rect.left + window.scrollX;

    // 防止超出右边界
    const popupWidth = 380;
    if (left + popupWidth > window.innerWidth) {
      left = window.innerWidth - popupWidth - 20;
    }

    popup.style.top = top + "px";
    popup.style.left = left + "px";
  }
}

function removeExistingPopup() {
  const existing = document.querySelector(".ct-selection-popup");
  if (existing) existing.remove();
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

// ── 状态提示条 ──

function showStatus(text) {
  let bar = document.getElementById("ct-status-bar");
  if (!bar) {
    bar = document.createElement("div");
    bar.id = "ct-status-bar";
    bar.className = "ct-status-bar";
    document.body.appendChild(bar);
  }
  bar.textContent = text;
  bar.style.display = "block";
}

function hideStatus() {
  const bar = document.getElementById("ct-status-bar");
  if (bar) bar.style.display = "none";
}

// ── 消息监听 ──

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "toggleTranslation") {
    toggleTranslation();
  } else if (request.action === "translateSelection") {
    translateSelection(request.text);
  } else if (request.action === "getStatus") {
    sendResponse({ isTranslating: isTranslating });
  }
});
