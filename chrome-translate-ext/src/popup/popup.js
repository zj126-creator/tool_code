/**
 * Popup 脚本 — 弹窗交互逻辑
 */

document.addEventListener("DOMContentLoaded", () => {
  const btnTranslatePage = document.getElementById("btnTranslatePage");
  const btnRestorePage = document.getElementById("btnRestorePage");
  const btnTranslateText = document.getElementById("btnTranslateText");
  const manualInput = document.getElementById("manualInput");
  const manualResult = document.getElementById("manualResult");

  // ── 翻译当前页面 ──
  btnTranslatePage.addEventListener("click", async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab) {
      chrome.tabs.sendMessage(tab.id, { action: "toggleTranslation" }, () => {
        window.close();
      });
    }
  });

  // ── 恢复原页面 ──
  btnRestorePage.addEventListener("click", async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab) {
      chrome.tabs.sendMessage(tab.id, { action: "toggleTranslation" }, () => {
        window.close();
      });
    }
  });

  // ── 手动翻译 ──
  btnTranslateText.addEventListener("click", () => {
    const text = manualInput.value.trim();
    if (!text) return;

    manualResult.textContent = "翻译中…";
    manualResult.classList.add("show");

    chrome.runtime.sendMessage(
      { action: "fetchTranslation", text: text, sourceLang: "auto" },
      (response) => {
        if (response && response.success) {
          manualResult.textContent = response.data.translatedText;
        } else {
          manualResult.textContent = "翻译失败: " + (response ? response.error : "未知错误");
        }
      }
    );
  });

  // 回车键翻译
  manualInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      btnTranslateText.click();
    }
  });
});
