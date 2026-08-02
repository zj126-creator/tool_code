# Chrome Translate Extension — 简体中文翻译助手

一个 Chrome 浏览器扩展，将外文网页翻译为简体中文，支持整页翻译、划词翻译、右键菜单翻译，原文/译文对照显示。

![Chrome Extension](https://img.shields.io/badge/Chrome-Extension-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Manifest](https://img.shields.io/badge/Manifest-V3-orange)

## ✨ 功能特性

- 🌐 **整页翻译** — 一键将当前页面所有外文翻译为简体中文，译文以蓝色显示在原文旁边
- ✋ **划词翻译** — 选中任意文字，浮窗显示翻译结果和检测到的源语言
- 📋 **右键菜单** — 右键页面或选中文字，直接翻译
- 📝 **手动翻译** — 在弹窗中手动输入文字翻译
- ⌨️ **快捷键** — `Alt+T` 快速开关整页翻译
- 🔍 **原文/译文对照** — 译文以蓝色标注显示在原文后，可随时恢复原文
- 💯 **免费翻译引擎** — 使用 Google 翻译免费接口，无需 API Key

## 🚀 安装方式

### 开发者模式加载（当前方式）

1. 打开 Chrome 浏览器，地址栏输入 `chrome://extensions/`
2. 右上角开启「开发者模式」
3. 点击「加载已解压的扩展程序」
4. 选择 `src/` 文件夹
5. 扩展出现在工具栏，即可使用

### 打包安装（.crx 文件）

```bash
# 在 Chrome 扩展页面点击「打包扩展程序」
# 根目录选 src/，私钥可选
```

## 📖 使用说明

### 整页翻译

| 操作 | 方式 |
|------|------|
| 快捷键 | `Alt+T` 开关翻译 |
| 右键菜单 | 右键页面 → 翻译此页面为简体中文 |
| 工具栏 | 点击图标 → 翻译当前页面 |

翻译后译文以蓝色显示在原文旁边，再次操作恢复原文。

### 划词翻译

1. 在网页中选中一段文字
2. 右键 → 翻译选中的文字为简体中文
3. 浮窗显示原文和译文，自动检测源语言

### 手动翻译

1. 点击工具栏图标
2. 在弹窗中输入文字
3. 点击翻译或按回车

## 🏗️ 项目结构

```
chrome-translate-ext/
├── src/
│   ├── manifest.json              # 扩展配置（Manifest V3）
│   ├── icons/
│   │   ├── icon16.png             # 图标 16x16
│   │   ├── icon48.png             # 图标 48x48
│   │   └── icon128.png            # 图标 128x128
│   ├── background/
│   │   └── background.js          # 后台 Service Worker
│   ├── content/
│   │   ├── content.js             # 内容脚本（页面翻译逻辑）
│   │   └── content.css            # 内容样式
│   └── popup/
│       ├── popup.html             # 弹窗界面
│       ├── popup.css              # 弹窗样式
│       └── popup.js               # 弹窗逻辑
└── README.md
```

## 🔧 技术栈

| 模块 | 技术 |
|------|------|
| 扩展规范 | Chrome Manifest V3 |
| 翻译引擎 | Google 翻译免费接口 (translate.googleapis.com) |
| 后台 | Service Worker |
| 内容交互 | Content Script + TreeWalker 遍历文本节点 |
| UI | HTML + CSS + 原生 JS |

## 💡 使用提示

1. 整页翻译会跳过 `<script>`、`<style>`、`<code>` 等标签内文字
2. 翻译采用批量请求，避免大量请求导致被限流
3. 译文以蓝色背景标注，方便区分
4. 再次按 `Alt+T` 可恢复原页面
5. 划词翻译浮窗可点击 ✕ 关闭

## 🔒 隐私说明

- 不收集任何用户数据
- 翻译请求仅发送到 Google 翻译 API
- 不存储翻译内容
- 无需登录，无需 API Key

## 📄 许可证

[MIT License](../LICENSE) — 自由使用、修改和分发。
