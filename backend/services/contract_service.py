import os
import json
import re
from dotenv import load_dotenv
from openai import OpenAI

# =========================
# 1. 加载 .env
# =========================
load_dotenv()

# =========================
# 2. MiniMax 客户端
# =========================
client = OpenAI(
    api_key=os.getenv("MINIMAX_API_KEY"),
    base_url=os.getenv("MINIMAX_BASE_URL")
)

# =========================
# 3. JSON解析工具（修复版 - 支持嵌套JSON）
# =========================
def fix_json(json_str: str):
    replacements = [
        ("‘", '"'), ("'", '"'),
        ("`", '"'),
        ("\n", " "),
        ("  ", " ")
    ]
    for old, new in replacements:
        json_str = json_str.replace(old, new)
    return json_str


# =========================
# 3.1 审查点定义
# =========================
ALL_CHECKS = [
    "penalty",           # 违约金
    "confidentiality",   # 保密条款
    "payment",           # 付款条款
    "dispute",           # 争议解决
    "liability",         # 责任限制
    "termination",       # 终止条款
    "non_compete",       # 竞业禁止
    "privacy",           # 隐私保护
    "ip_ownership",      # 知识产权
    "force_majeure",     # 不可抗力
    "working_hours",     # 工时制度
    "social_insurance",  # 社保福利
    "delivery",          # 交付条款
    "interest_rate",     # 利率条款
    "warranty",          # 质保/维修
]


# =========================
# 3.2 合同类型 -> 推荐审查点 映射表
# =========================
CONTRACT_CHECKS_MAP = {
    "劳动合同": ["penalty", "payment", "termination", "non_compete", "confidentiality", "privacy", "dispute", "working_hours", "social_insurance"],
    "房屋租赁合同": ["penalty", "payment", "termination", "force_majeure", "dispute", "liability", "warranty"],
    "房屋买卖合同": ["penalty", "payment", "termination", "dispute", "liability", "force_majeure", "warranty"],
    "软件开发合同": ["penalty", "payment", "ip_ownership", "confidentiality", "termination", "dispute", "liability", "delivery"],
    "采购合同": ["penalty", "payment", "termination", "dispute", "liability", "delivery", "warranty"],
    "销售合同": ["penalty", "payment", "termination", "dispute", "liability", "delivery", "warranty"],
    "服务合同": ["penalty", "payment", "termination", "dispute", "liability"],
    "委托合同": ["penalty", "payment", "termination", "confidentiality", "dispute", "liability"],
    "借款合同": ["penalty", "payment", "termination", "privacy", "dispute", "liability", "interest_rate"],
    "保密协议": ["confidentiality", "termination", "dispute", "liability", "penalty"],
    "竞业禁止协议": ["non_compete", "penalty", "termination", "dispute", "liability", "payment"],
    "合伙协议": ["penalty", "payment", "termination", "dispute", "liability", "confidentiality"],
    "投资协议": ["penalty", "payment", "ip_ownership", "termination", "dispute", "liability", "confidentiality"],
}


def get_recommended_checks(contract_type: str):
    return CONTRACT_CHECKS_MAP.get(contract_type, ["penalty", "payment", "dispute"])


def extract_json(text: str):
    def find_json_block(text: str):
        start_idx = text.find("{")
        if start_idx == -1:
            return None
        depth = 0
        for i in range(start_idx, len(text)):
            char = text[i]
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    return text[start_idx:i+1]
        return None

    def try_parse(json_str):
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None

    try:
        match = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", text)
        if match:
            result = try_parse(match.group(1))
            if result:
                return result

        json_str = find_json_block(text)
        if json_str:
            result = try_parse(json_str)
            if result:
                return result

            cleaned = fix_json(json_str)
            result = try_parse(cleaned)
            if result:
                return result

    except Exception as e:
        print("JSON解析异常：", e)

    return None


# =========================
# 4. 🧠 合同类型识别 Agent
# =========================
def identify_contract_type(text: str):
    response = client.chat.completions.create(
        model="MiniMax-M2.5-highspeed",
        messages=[
            {
                "role": "system",
                "content": (
                    "你是一名专业的合同审查律师，擅长识别各类合同类型。"
                    "你必须严格输出JSON，不允许任何解释或思考过程。"
                )
            },
            {
                "role": "user",
                "content": f"""
请分析以下合同文本，识别合同类型。

-----------------------
【强制规则】
1. 只输出JSON格式，不允许任何解释
2. contract_type 必须是标准中文合同类型名称
3. 如果无法确定具体类型，返回较宽泛的类型

-----------------------
【常见合同类型】
- 劳动合同
- 房屋租赁合同
- 房屋买卖合同
- 软件开发合同
- 采购合同
- 销售合同
- 服务合同
- 委托合同
- 借款合同
- 保密协议
- 竞业禁止协议
- 合伙协议
- 投资协议
- 其他（如果无法归类）

-----------------------
【输出JSON（严格）】
{{
  "contract_type": "劳动合同"
}}

-----------------------
【合同内容】
{text[:2000]}
"""
            }
        ],
        temperature=0.1
    )

    content = response.choices[0].message.content
    data = extract_json(content)

    if not data:
        return {
            "contract_type": "未知合同类型",
            "recommended_checks": ["penalty", "payment", "dispute"]
        }

    contract_type = data.get("contract_type", "未知合同类型")
    return {
        "contract_type": contract_type,
        "recommended_checks": get_recommended_checks(contract_type)
    }


# =========================
# 5. 🧠 审查点配置 -> Prompt规则生成（立场感知版）
# =========================
def build_rules(config: dict, stance: str = "employee"):
    rules = []

    is_employee = (stance == "employee")

    check_items = [
        ("penalty", "违约金", [
            "检查违约金条款是否过高或不合理、是否显失公平",  # employee
            "检查违约金条款是否能有效约束对方、赔偿金额是否足够"  # employer
        ]),
        ("confidentiality", "保密条款", [
            "检查保密条款是否完善、保密期限是否合理",  # employee
            "检查保密条款是否足够保护企业商业秘密、违约责任是否明确"  # employer
        ]),
        ("payment", "付款条款", [
            "检查付款周期是否过长或存在资金风险",  # employee
            "检查付款周期是否合理、是否存在资金风险"  # employer
        ]),
        ("dispute", "争议解决", [
            "检查争议解决条款是否合理、是否对己方过于不利",  # employee
            "检查争议解决条款是否合理、是否对己方有利"  # employer
        ]),
        ("liability", "责任限制", [
            "检查责任限制条款是否对己方过于苛刻",  # employee
            "检查责任限制条款是否对己方有利、能有效免责"  # employer
        ]),
        ("termination", "终止条款", [
            "检查终止条款是否对己方过于苛刻、是否需要赔偿",  # employee
            "检查终止条款是否对己方有利、违约成本是否足够"  # employer
        ]),
        ("non_compete", "竞业禁止", [
            "检查竞业禁止条款范围是否过宽、补偿是否合理",  # employee
            "检查竞业禁止条款是否有效约束员工、范围期限是否合理"  # employer
        ]),
        ("privacy", "隐私保护", [
            "检查是否过度收集或使用个人信息、是否符合《个人信息保护法》",  # employee
            "检查隐私条款是否符合法规要求、是否存在法律风险"  # employer
        ]),
        ("ip_ownership", "知识产权", [
            "检查知识产权归属是否合理、是否过度让渡自身权益",  # employee
            "检查知识产权归属是否明确、是否有利于企业"  # employer
        ]),
        ("force_majeure", "不可抗力", [
            "检查不可抗力条款是否完善、是否明确界定范围",  # employee
            "检查不可抗力条款是否完善、是否能合理免责"  # employer
        ]),
        ("working_hours", "工时制度", [
            "检查工时制度是否符合劳动法规定、加班费是否合理",  # employee
            "检查工时制度是否合法、加班成本是否可控"  # employer
        ]),
        ("social_insurance", "社保福利", [
            "检查社保福利缴纳是否合规、是否按规定足额缴纳",  # employee
            "检查社保缴纳是否合规、是否按规定操作"  # employer
        ]),
        ("delivery", "交付条款", [
            "检查交付条款的时间、地点、方式是否明确",  # employee
            "检查交付条款的时间、地点、方式是否明确"  # employer
        ]),
        ("interest_rate", "利率条款", [
            "检查利率条款是否合法、是否超过法定上限",  # employee
            "检查利率条款是否合法、是否符合监管要求"  # employer
        ]),
        ("warranty", "质保维修", [
            "检查质保维修条款是否合理、是否对己方过于苛刻",  # employee
            "检查质保维修条款是否合理、是否能保护己方权益"  # employer
        ]),
    ]

    for key, name, rule_list in check_items:
        if config.get(key):
            rule = rule_list[0] if is_employee else rule_list[1]
            rules.append(f"{len(rules) + 1}. 检查{name}：{rule}")

    return "\n".join(rules) if rules else "未指定审查点，请自行进行基础风险分析"


# =========================
# 6. 🧠 核心AI函数（升级版 Agent）
# =========================
def analyze_contract(text: str, config: dict, stance: str = None):
    if stance is None:
        stance = config.get("stance", "employee")

    rules_text = build_rules(config, stance)

    response = client.chat.completions.create(
        model="MiniMax-M2.5-highspeed",
        messages=[
            {
                "role": "system",
                "content": (
                    "你是一名拥有10年经验的中国企业合同审查律师，"
                    "擅长合同条款识别、风控与法律审查、条款定位与文本标注。"
                    "你必须严格输出JSON，不允许任何解释或思考过程。"
                )
            },
            {
                "role": "user",
                "content": f"""
你现在的任务是对合同进行专业法律风险审查，并输出可用于PDF定位的结构化结果。

-----------------------
【用户启用的审查点】
{rules_text}

-----------------------
【强制规则】
1. 只能分析用户启用的审查点
2. 不得编造合同中不存在内容
3. 必须定位条款位置（第X条 / 第X款 / 或整体判断）
4. 必须提取"可用于PDF高亮的原文片段"
5. evidence 必须是合同原文逐字引用
6. 必须生成 anchor.text（用于前端高亮匹配）
7. 风险必须法律化表达
8. 禁止任何解释性输出

-----------------------
【新增关键规则（PDF联动）】
- anchor.text 必须是：
  ✔ 最短有效匹配片段（5~30字）
  ✔ 必须能在PDF中直接搜索到
- match_mode：
  - exact（完全匹配优先）
  - fuzzy（无法精确匹配时）

-----------------------
【风险等级】

high：
- 合同可能无效 / 高额损失

medium：
- 存在争议风险

low：
- 轻微瑕疵

-----------------------
【输出JSON（严格）】

{{
  "risks": [
    {{
      "point": "条款名称",
      "level": "high | medium | low",

      "clause_location": "第X条 / 未明确分条款",

      "evidence": "合同原文逐字引用",

      "anchor": {{
        "text": "用于PDF定位的关键短语",
        "match_mode": "exact | fuzzy"
      }},

      "issue": "法律风险分析（专业表达）",

      "suggestion": "具体修改建议"
    }}
  ],
  "summary": "整体法律风险总结（1-3句）"
}}

-----------------------
【合同内容】
{text}
"""
            }
        ],
        temperature=0.2
    )

    content = response.choices[0].message.content
    print("=" * 50)
    print("AI原始输出:")
    print(content[:1000])
    print("=" * 50)
    data = extract_json(content)

    if not data:
        print("JSON解析失败，尝试备用解析...")
        data = fallback_parse(content)

    if not data:
        print("完全解析失败")
        return {
            "risks": [],
            "summary": "解析失败（AI输出不是标准JSON）",
            "raw": content[:500],
            "stance": stance
        }

    data["stance"] = stance
    return data


def fallback_parse(content: str):
    import re
    summary_match = re.search(r'["\']summary["\']\s*:\s*["\'](.+?)["\']', content, re.S)
    risks = []

    risk_blocks = re.findall(r'\{[^{}]*"point"[^{}]*\}', content, re.S)
    for block in risk_blocks[:5]:
        point_match = re.search(r'["\']point["\']\s*:\s*["\'](.+?)["\']', block)
        level_match = re.search(r'["\']level["\']\s*:\s*["\'](.+?)["\']', block)
        location_match = re.search(r'["\']clause_location["\']\s*:\s*["\'](.+?)["\']', block)
        evidence_match = re.search(r'["\']evidence["\']\s*:\s*["\'](.+?)["\']', block)

        if point_match:
            risks.append({
                "point": point_match.group(1),
                "level": level_match.group(1) if level_match else "medium",
                "clause_location": location_match.group(1) if location_match else "未知",
                "evidence": evidence_match.group(1)[:200] if evidence_match else "",
                "anchor": {"text": point_match.group(1)[:20], "match_mode": "fuzzy"},
                "issue": "需要进一步分析",
                "suggestion": "建议人工复核"
            })

    summary = summary_match.group(1) if summary_match else "分析完成"

    if risks or summary != "分析完成":
        return {"risks": risks, "summary": summary}

    return None
