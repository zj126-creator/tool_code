"""
题目数据模型 — 支持单选、多选、判断三种题型
支持导入: CSV / Excel(.xlsx/.xls) / JSON / 磨题帮格式
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class Question:
    """题目基类"""
    id: str
    type: str  # 'single', 'multiple', 'judge'
    question: str
    options: List[str] = field(default_factory=list)
    answer: List[int] = field(default_factory=list)  # 正确答案的索引列表
    explanation: str = ""

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'type': self.type,
            'question': self.question,
            'options': self.options,
            'answer': self.answer,
            'explanation': self.explanation,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'Question':
        return cls(
            id=d['id'],
            type=d['type'],
            question=d['question'],
            options=d.get('options', []),
            answer=d.get('answer', []),
            explanation=d.get('explanation', ''),
        )

    def check_answer(self, user_answer: List[int]) -> bool:
        return sorted(user_answer) == sorted(self.answer)

    def get_correct_text(self) -> str:
        return " / ".join(self.options[i] if i < len(self.options) else str(i)
                          for i in sorted(self.answer))


# ─── 格式分发 ────────────────────────────────────────

def load_questions(filepath: str) -> List[Question]:
    """根据扩展名自动选择加载器"""
    p = Path(filepath)
    ext = p.suffix.lower()
    if ext == '.csv':
        return load_questions_from_csv(filepath)
    elif ext in ('.xlsx', '.xls'):
        return load_questions_from_excel(filepath)
    else:
        return load_questions_from_json(filepath)


# ─── JSON ────────────────────────────────────────────

def load_questions_from_json(filepath: str) -> List[Question]:
    """从 JSON 文件加载题库"""
    import json
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        data = json.load(f)
    items = data.get('questions', data if isinstance(data, list) else [])
    return [Question.from_dict(item) for item in items]


# ─── CSV ──────────────────────────────────────────────

def load_questions_from_csv(filepath: str) -> List[Question]:
    """从 CSV 文件加载题库

    列: id, type, question, options, answer, explanation
    - type: single / multiple / judge
    - options: 选项之间用 | 分隔
    - answer: 正确答案索引(从0开始)，多个用 | 分隔
    """
    import csv
    questions = []
    with open(filepath, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            q_type = (row.get('type') or '').strip().lower()
            opts_str = row.get('options') or ''
            options = [o.strip() for o in opts_str.split('|') if o.strip()] if opts_str else []
            ans_str = row.get('answer') or ''
            answer = [int(x.strip()) for x in ans_str.split('|') if x.strip().isdigit()] if ans_str else []
            if q_type == 'judge' and not options:
                options = ["正确", "错误"]
                if not answer:
                    ans_text = (row.get('answer') or '').strip()
                    if ans_text in ("正确", "对", "T", "True", "1"):
                        answer = [0]
                    elif ans_text in ("错误", "错", "F", "False", "0"):
                        answer = [1]
            q = Question(
                id=(row.get('id') or '').strip(),
                type=q_type,
                question=(row.get('question') or '').strip(),
                options=options,
                answer=answer,
                explanation=(row.get('explanation') or '').strip(),
            )
            if q.id and q.question:
                questions.append(q)
    return questions


# ─── Excel (通用 + 磨题帮格式) ────────────────────────

# 磨题帮题型 → 内部题型映射
_MOTIBANG_TYPE_MAP = {
    "顺序选择题": "single",
    "单选题": "single",
    "单选": "single",
    "不定项选择题": "multiple",
    "多选题": "multiple",
    "多选": "multiple",
    "顺序不定项选择题": "multiple",
    "有序不定项选择题": "multiple",
    "判断题": "judge",
    "判断": "judge",
}

# 字母 → 索引
_LETTER_TO_IDX = {chr(65 + i): i for i in range(26)}  # A→0, B→1, ...

# 判断题答案文本 → 索引 (0=正确, 1=错误)
_JUDGE_TEXT_MAP = {
    "正确": 0, "对": 0, "T": 0, "True": 0, "TRUE": 0, "是": 0, "√": 0,
    "错误": 1, "错": 1, "F": 1, "False": 1, "FALSE": 1, "否": 1, "×": 1, "X": 1,
}


def _parse_motibang_answer(ans_str: str, q_type: str) -> List[int]:
    """解析磨题帮答案字符串为索引列表

    磨题帮答案格式:
    - 单选: "A" / "B" / "C" / "D"
    - 多选: "AC" / "ABD" / "ACDE"
    - 判断: "对"/"错" / "正确"/"错误" / "A"/"B" (A=对, B=错)
    """
    ans_str = ans_str.strip()
    if not ans_str:
        return []
    # 判断题
    if q_type == "judge":
        if ans_str in _JUDGE_TEXT_MAP:
            return [_JUDGE_TEXT_MAP[ans_str]]
        if ans_str in _LETTER_TO_IDX:
            return [_LETTER_TO_IDX[ans_str]]  # A→0(正确), B→1(错误)
        return []
    # 选择题: 拆成单个字母
    indices = []
    for ch in ans_str:
        ch_upper = ch.upper()
        if ch_upper in _LETTER_TO_IDX:
            indices.append(_LETTER_TO_IDX[ch_upper])
    return sorted(set(indices))


def load_questions_from_excel(filepath: str) -> List[Question]:
    """从 Excel 文件加载题库

    支持三种格式 (自动识别):
    1. 磨题帮格式: 表头含 题干/题型/选择项1/答案 等
    2. 技能等级评价格式: 表头含 试题正文/试题选项/试题答案
    3. 通用格式: 表头含 id/type/question/options/answer/explanation
    """
    try:
        import openpyxl
    except ImportError:
        raise RuntimeError("读取 Excel 需要安装 openpyxl，请运行: pip install openpyxl")

    import tempfile, shutil
    real_path = filepath
    tmp_path = None

    # 检测文件真实格式: 如果是 .xls 但实际是 zip (xlsx)，复制为临时 .xlsx
    try:
        with open(filepath, 'rb') as f:
            magic = f.read(4)
        if magic[:2] == b'PK' and filepath.lower().endswith('.xls'):
            # 文件实际是 xlsx 格式但扩展名为 .xls
            tmp_path = tempfile.mktemp(suffix='.xlsx')
            shutil.copy2(filepath, tmp_path)
            real_path = tmp_path
    except Exception:
        pass

    try:
        wb = openpyxl.load_workbook(real_path, read_only=True, data_only=True)
    except Exception:
        # openpyxl 失败，尝试用 xlrd 读取真正的 .xls 格式
        try:
            import xlrd
            return _load_from_xlrd(filepath)
        except ImportError:
            raise RuntimeError("读取 .xls 文件需要安装 xlrd，请运行: pip install xlrd")
    finally:
        if tmp_path:
            try:
                import os
                os.unlink(tmp_path)
            except Exception:
                pass

    ws = wb.active

    # 读取前几行判断格式
    rows = list(ws.iter_rows(values_only=True))
    try:
        wb.close()
    except Exception:
        pass
    if not rows:
        return []

    # 收集所有行的非空单元格文本用于表头检测
    def _row_texts(row):
        return [str(c).strip() if c is not None else "" for c in row]

    # 磨题帮格式检测: 搜索前5行找表头
    header_row_idx = None
    is_motibang = False
    is_skill_eval = False
    headers = []
    for i in range(min(5, len(rows))):
        texts = _row_texts(rows[i])
        joined = "|".join(texts).lower()
        # 技能等级评价格式: 试题正文/试题选项/试题答案
        if "试题正文" in texts or "试题选项" in texts or "试题答案" in texts:
            header_row_idx = i
            headers = texts
            is_skill_eval = True
            break
        # 磨题帮格式: 题干/题型/选择项1
        if "题干" in texts or "题型" in texts or "选择项1" in texts:
            header_row_idx = i
            headers = texts
            is_motibang = True
            break
        if "question" in joined and ("type" in joined or "题型" in texts):
            header_row_idx = i
            headers = texts
            break

    if header_row_idx is None:
        # 没有明确表头，假设第一行是表头
        header_row_idx = 0
        headers = _row_texts(rows[0])

    # 建立列名→索引映射 (支持中英文)
    col_map = {}
    for idx, h in enumerate(headers):
        hl = h.lower().strip()
        if hl:
            col_map.setdefault(hl, idx)
            col_map.setdefault(h, idx)

    if is_skill_eval:
        return _parse_skill_eval_excel(rows, header_row_idx, col_map)
    elif is_motibang:
        return _parse_motibang_excel(rows, header_row_idx, col_map)
    else:
        return _parse_generic_excel(rows, header_row_idx, col_map)


def _parse_skill_eval_excel(rows, header_idx, col_map) -> List[Question]:
    """解析技能等级评价理论题库 Excel 格式

    特点:
    - 表头可能在第2行（第1行为标题）
    - 列名: 试题正文(题干)、试题选项($;分隔)、试题答案(字母)、题型、答案解析
    - 判断题选项为 '正确$;$错误'，答案为 A/B
    """

    def find_col(*names):
        for n in names:
            if n in col_map:
                return col_map[n]
            nl = n.lower()
            if nl in col_map:
                return col_map[nl]
        return None

    q_col = find_col("试题正文", "题干", "题目")
    type_col = find_col("题型")
    opt_col = find_col("试题选项", "选项", "options")
    ans_col = find_col("试题答案", "答案", "answer")
    explain_col = find_col("答案解析", "解析", "说明")

    questions = []
    q_counter = 0
    for r in range(header_idx + 1, len(rows)):
        row = rows[r]

        def cell(col):
            if col is None or col >= len(row):
                return ""
            return str(row[col]).strip() if row[col] else ""

        q_text = cell(q_col)
        if not q_text:
            continue

        # 题型
        type_raw = cell(type_col)
        q_type = _MOTIBANG_TYPE_MAP.get(type_raw, "")
        if not q_type:
            continue

        # 选项: 用 $;$ 分隔 (技能等级评价格式) 或 | 分隔
        opts_str = cell(opt_col)
        if opts_str:
            if "$;$" in opts_str:
                options = [o.strip() for o in opts_str.split("$;$") if o.strip()]
            else:
                options = [o.strip() for o in opts_str.split("|") if o.strip()]
        else:
            options = []

        # 判断题: 自动补充选项
        if q_type == "judge" and not options:
            options = ["正确", "错误"]

        # 答案: 字母 A/B/C/D 或连写 ABCD，判断题也可能是 A/B
        ans_str = cell(ans_col)
        answer = _parse_motibang_answer(ans_str, q_type)

        # 解析
        explanation = cell(explain_col)

        q_counter += 1
        q = Question(
            id=f"q{q_counter:04d}",
            type=q_type,
            question=q_text,
            options=options,
            answer=answer,
            explanation=explanation,
        )
        if q.question:
            questions.append(q)

    return questions


def _parse_motibang_excel(rows, header_idx, col_map) -> List[Question]:
    """解析磨题帮格式 Excel"""

    def find_col(*names):
        """在 col_map 中查找列索引"""
        for n in names:
            if n in col_map:
                return col_map[n]
            nl = n.lower()
            if nl in col_map:
                return col_map[nl]
        return None

    q_col = find_col("题干")
    type_col = find_col("题型")
    explain_col = find_col("解析", "说明")

    # 选择项列: 选择项1, 选择项2, ... 或 选项1, 选项2, ...
    opt_cols = []
    for i in range(1, 21):
        c = find_col(f"选择项{i}", f"选项{i}")
        if c is not None:
            opt_cols.append(c)
        else:
            break

    # 单列选项: "选项" (|分隔, 可能带 A- 前缀)
    opt_single_col = find_col("选项")
    if opt_single_col is not None and opt_single_col not in opt_cols:
        opt_cols = []  # 单列模式，清空多列
    else:
        opt_single_col = None

    # 答案列: 答案 (单列) 或 答案1, 答案2, ...
    ans_cols = []
    single_ans = find_col("答案")
    if single_ans is not None:
        ans_cols.append(single_ans)
    for i in range(1, 5):
        c = find_col(f"答案{i}")
        if c is not None and c not in ans_cols:
            ans_cols.append(c)
        elif c is None:
            break

    questions = []
    q_counter = 0
    for r in range(header_idx + 1, len(rows)):
        row = rows[r]
        q_text = str(row[q_col]).strip() if q_col is not None and q_col < len(row) and row[q_col] else ""
        if not q_text:
            continue

        # 题型
        type_raw = str(row[type_col]).strip() if type_col is not None and type_col < len(row) and row[type_col] else ""
        q_type = _MOTIBANG_TYPE_MAP.get(type_raw, "")
        if not q_type:
            # 跳过不支持的题型 (填空、匹配等)
            continue

        # 选项
        options = []
        if opt_single_col is not None:
            # 单列选项: | 分隔, 可能带 A- B- C- 前缀
            if opt_single_col < len(row) and row[opt_single_col]:
                raw = str(row[opt_single_col]).strip()
                if "$;$" in raw:
                    parts = raw.split("$;$")
                else:
                    parts = raw.split("|")
                for p in parts:
                    p = p.strip()
                    if not p:
                        continue
                    # 去掉 A- B- C- D- 等字母前缀
                    if len(p) > 2 and p[1] == "-" and p[0].upper() in _LETTER_TO_IDX:
                        p = p[2:].strip()
                    elif len(p) > 3 and p[2] == "-" and p[0:2].upper() in {"AB", "AC", "AD", "BC", "BD", "CD"}:
                        pass  # 不是前缀, 是题目内容
                    options.append(p)
        else:
            for oc in opt_cols:
                if oc < len(row) and row[oc]:
                    opt_text = str(row[oc]).strip()
                    if opt_text:
                        options.append(opt_text)

        # 判断题: 自动补充 正确/错误 选项
        if q_type == "judge" and not options:
            options = ["正确", "错误"]

        # 答案: 合并所有答案列
        ans_parts = []
        for ac in ans_cols:
            if ac < len(row) and row[ac]:
                ans_parts.append(str(row[ac]).strip())

        # 解析答案
        if q_type == "judge":
            # 判断题答案可能在答案列，也可能是 A/B 或 对/错
            ans_str = "".join(ans_parts)
            answer = _parse_motibang_answer(ans_str, "judge")
        else:
            # 选择题: 答案可能是 "A" / "AC" / "ABD" 等，分布在多个答案列
            ans_str = "".join(ans_parts)
            answer = _parse_motibang_answer(ans_str, q_type)

        # 解析
        explanation = ""
        if explain_col is not None and explain_col < len(row) and row[explain_col]:
            explanation = str(row[explain_col]).strip()

        q_counter += 1
        q = Question(
            id=f"q{q_counter:04d}",
            type=q_type,
            question=q_text,
            options=options,
            answer=answer,
            explanation=explanation,
        )
        if q.question:
            questions.append(q)

    return questions


def _parse_generic_excel(rows, header_idx, col_map) -> List[Question]:
    """解析通用 Excel 格式 (id/type/question/options/answer/explanation)"""

    def find_col(*names):
        for n in names:
            if n in col_map:
                return col_map[n]
            nl = n.lower()
            if nl in col_map:
                return col_map[nl]
        return None

    id_col = find_col("id")
    type_col = find_col("type", "题型")
    q_col = find_col("question", "题干", "题目")
    opt_col = find_col("options", "选项")
    ans_col = find_col("answer", "答案")
    explain_col = find_col("explanation", "解析", "说明")

    questions = []
    q_counter = 0
    for r in range(header_idx + 1, len(rows)):
        row = rows[r]
        def cell(col):
            if col is None or col >= len(row):
                return ""
            return str(row[col]).strip() if row[col] else ""

        q_text = cell(q_col)
        if not q_text:
            continue

        q_type = cell(type_col).lower()
        if q_type in _MOTIBANG_TYPE_MAP:
            q_type = _MOTIBANG_TYPE_MAP[q_type]

        # options: | 分隔 或 多列
        if opt_col is not None:
            opts_str = cell(opt_col)
            options = [o.strip() for o in opts_str.split('|') if o.strip()] if opts_str else []
        else:
            # 尝试读取 选项1/选项2/选择项1 等列
            options = []
            for i in range(1, 21):
                c = find_col(f"选项{i}", f"选择项{i}", f"option{i}")
                if c is not None:
                    v = cell(c)
                    if v:
                        options.append(v)
                else:
                    break

        ans_str = cell(ans_col)
        answer = [int(x.strip()) for x in ans_str.split('|') if x.strip().isdigit()] if ans_str else []
        if q_type == "judge" and not options:
            options = ["正确", "错误"]
            if not answer:
                if ans_str in _JUDGE_TEXT_MAP:
                    answer = [_JUDGE_TEXT_MAP[ans_str]]

        q_counter += 1
        q = Question(
            id=cell(id_col) or f"q{q_counter:04d}",
            type=q_type,
            question=q_text,
            options=options,
            answer=answer,
            explanation=cell(explain_col),
        )
        if q.question:
            questions.append(q)

    return questions


def _load_from_xlrd(filepath: str) -> List[Question]:
    """用 xlrd 读取真正的 .xls 格式文件"""
    import xlrd
    wb = xlrd.open_workbook(filepath)
    ws = wb.sheet_by_index(0)

    rows = []
    for r in range(ws.nrows):
        row = tuple(ws.cell_value(r, c) for c in range(ws.ncols))
        rows.append(row)
    wb.release_resources()

    if not rows:
        return []

    def _row_texts(row):
        return [str(c).strip() if c is not None else "" for c in row]

    # 检测表头
    header_row_idx = None
    is_motibang = False
    is_skill_eval = False
    headers = []
    for i in range(min(5, len(rows))):
        texts = _row_texts(rows[i])
        if "试题正文" in texts or "试题选项" in texts or "试题答案" in texts:
            header_row_idx = i
            headers = texts
            is_skill_eval = True
            break
        if "题干" in texts or "题型" in texts or "选择项1" in texts:
            header_row_idx = i
            headers = texts
            is_motibang = True
            break

    if header_row_idx is None:
        header_row_idx = 0
        headers = _row_texts(rows[0])

    col_map = {}
    for idx, h in enumerate(headers):
        hl = h.lower().strip()
        if hl:
            col_map.setdefault(hl, idx)
            col_map.setdefault(h, idx)

    if is_skill_eval:
        return _parse_skill_eval_excel(rows, header_row_idx, col_map)
    elif is_motibang:
        return _parse_motibang_excel(rows, header_row_idx, col_map)
    else:
        return _parse_generic_excel(rows, header_row_idx, col_map)


def load_questions_from_dict(data: dict) -> List[Question]:
    """从字典加载题库"""
    questions = []
    for item in data.get('questions', data if isinstance(data, list) else []):
        questions.append(Question.from_dict(item))
    return questions
