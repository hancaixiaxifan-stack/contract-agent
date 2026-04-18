# Contract Agent

![截图](image/屏幕截图 2026-04-18 151502.png)

AI驱动的智能合同审查工具，支持PDF和文本合同分析，自动识别合同类型并检测潜在法律风险。

## 功能特点

- 📄 **多格式支持** - 支持PDF和纯文本合同上传分析
- 🤖 **AI智能识别** - 自动识别劳动合同、租赁合同、软件开发合同等13种合同类型
- ⚠️ **风险检测** - 从15个维度审查合同风险（违约金、保密条款、付款条款、争议解决等）
- 👤 **立场感知** - 支持"求职者"和"用人单位"两种审查立场
- 🔒 **数据安全** - 无状态部署，每次访问数据重置，保护隐私
- 🐳 **Docker一键部署** - 无需配置环境，`docker-compose up` 即可运行

## 快速开始

### 环境要求

- Docker
- Docker Compose

### 安装步骤

1. 克隆项目
```bash
git clone https://github.com/hancaixiaxifan-stack/contract-agent
cd contract-agent
```

2. 创建并编辑环境变量文件
```bash
cp .env.example .env
```

**手动用记事本打开 `.env` 文件，将 `MINIMAX_API_KEY=your_api_key_here` 改成你真实的API密钥：**
```
MINIMAX_API_KEY=你真实的API密钥
MINIMAX_BASE_URL=https://api.minimaxi.com/v1
```

3. 启动服务
```bash
docker-compose up -d
```

4. 访问应用

- 前端页面：http://localhost:5173
- 后端API：http://localhost:8000
- API文档：http://localhost:8000/docs

## 审查维度

| 维度 | 说明 |
|------|------|
| 违约金 | 检查违约金条款是否过高或不合理 |
| 保密条款 | 检查保密条款是否完善、保密期限是否合理 |
| 付款条款 | 检查付款周期是否过长或存在资金风险 |
| 争议解决 | 检查争议解决条款是否合理 |
| 责任限制 | 检查责任限制条款是否对己方过于苛刻 |
| 终止条款 | 检查终止条款是否对己方过于苛刻 |
| 竞业禁止 | 检查竞业禁止条款范围是否过宽 |
| 隐私保护 | 检查是否过度收集或使用个人信息 |
| 知识产权 | 检查知识产权归属是否合理 |
| 不可抗力 | 检查不可抗力条款是否完善 |
| 工时制度 | 检查工时制度是否符合劳动法规定 |
| 社保福利 | 检查社保福利缴纳是否合规 |
| 交付条款 | 检查交付条款的时间、地点、方式是否明确 |
| 利率条款 | 检查利率条款是否合法、是否超过法定上限 |
| 质保维修 | 检查质保维修条款是否合理 |

## 技术栈

**后端**
- FastAPI
- SQLite
- MiniMax API

**前端**
- Vue 3
- Vue Router
- Axios
- PDF.js

**部署**
- Docker
- Docker Compose

## 项目结构

```
contract-agent/
├── backend/                  # 后端服务
│   ├── main.py              # FastAPI入口
│   ├── api/analyze.py       # API路由
│   ├── models/file_model.py # 数据库模型
│   └── services/           # 业务逻辑
│       ├── contract_service.py  # AI审查
│       ├── pdf_service.py        # PDF处理
│       └── file_service.py       # 文件管理
├── frontend/                # 前端应用
│   ├── src/pages/          # 页面组件
│   └── Dockerfile          # 前端镜像
├── docker-compose.yml      # 服务编排
└── Dockerfile             # 后端镜像
```

## 注意事项

- 部署后数据存储在容器内存中，**容器重启后数据会清空**
- 请勿删除 `.env.example` 文件，其他用户需要用它创建 `.env`
- 如需持久化存储，可修改 `docker-compose.yml` 添加 volume 挂载

## License

MIT
