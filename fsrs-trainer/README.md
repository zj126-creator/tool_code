# FSRS 间隔重复学习系统

基于 FSRS-5.0（Free Spaced Repetition Scheduler）算法的间隔重复学习工具，支持单选、多选、判断三种题型，支持多题库管理和学习进度持久化。

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Algorithm](https://img.shields.io/badge/FSRS-5.0-orange)

## ✨ 功能特性

- 🧠 **FSRS-5.0 算法** — 先进的间隔重复调度算法，科学安排复习时间
- 📝 **三种题型** — 单选题、多选题、判断题
- 📚 **多题库管理** — 同时加载多个题库，切换学习
- 📥 **多种导入格式** — CSV / Excel(.xlsx) / JSON / 磨题帮格式
- 💾 **进度持久化** — 学习记录保存到 `~/.fsrs_trainer/progress.json`
- 📊 **学习统计** — 每日学习量、正确率统计
- ↩️ **撤销操作** — 误评可撤销
- 🖥️ **GUI 界面** — tkinter 图形界面，操作直观

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行

```bash
python -m fsrs_trainer.src.app
```

或直接运行：

```bash
python src/app.py
```

## 📖 使用说明

### 导入题库

支持以下格式：

| 格式 | 扩展名 | 说明 |
|------|--------|------|
| CSV | .csv | 逗号分隔，UTF-8 编码 |
| Excel | .xlsx / .xls | 含 openpyxl 读取 |
| JSON | .json | 标准 JSON 数组格式 |
| 磨题帮 | .xlsx | 磨题帮导出格式 |

### 题目格式示例（CSV）

```csv
id,type,question,options,answer,explanation
q1,single,Python是什么类型的语言？,编译型|解释型|汇编型|机器语言,1,Python是解释型语言
q2,multiple,以下哪些是Python的特点？,简洁|开源|面向对象|强类型,0;1;2;3,全部都是Python的特点
q3,judge,Python使用缩进来定义代码块,True,0,Python使用缩进而非大括号
```

### FSRS 评级

学习时对每道题给出评级，算法据此安排下次复习时间：

| 评级 | 含义 | 说明 |
|------|------|------|
| AGAIN | 忘了 | 完全不会，重置记忆 |
| HARD | 困难 | 勉强记得，间隔缩短 |
| GOOD | 良好 | 正常回忆，标准间隔 |
| EASY | 简单 | 轻松回忆，间隔延长 |

## 🏗️ 项目结构

```
fsrs-trainer/
├── src/
│   ├── __init__.py
│   ├── app.py             # GUI 主程序
│   ├── fsrs.py            # FSRS-5.0 算法核心
│   ├── question.py        # 题目模型与导入
│   └── storage.py         # 进度持久化
├── examples/
│   ├── sample_quiz.csv    # 示例题库（CSV）
│   ├── sample_quiz.json   # 示例题库（JSON）
│   └── sample_quiz_motibang.xlsx  # 示例题库（磨题帮）
├── requirements.txt
└── README.md
```

## 🔧 技术栈

| 模块 | 技术 |
|------|------|
| GUI | tkinter + ttk |
| 算法 | FSRS-5.0（自定义实现） |
| 数据导入 | CSV / JSON / openpyxl |
| 持久化 | JSON |

## 💡 FSRS 算法简介

FSRS（Free Spaced Repetition Scheduler）是一种基于记忆模型的间隔重复算法：

- **记忆稳定性（Stability）**：回忆的牢固程度，决定下次复习间隔
- **检索难度（Difficulty）**：题目的难易程度，动态调整
- **四种评级**：Again / Hard / Good / Easy，映射到记忆更新

相比传统 SM-2 算法，FSRS 通过更精确的记忆模型，在更少复习次数下达到更好的记忆效果。

参考：[FSRS 算法文档](https://github.com/open-spaced-repetition/fsrs4anki/wiki/The-Algorithm)

## 📄 许可证

[MIT License](../LICENSE) — 自由使用、修改和分发。
