# 状态 — #BuildHybridAI 2026 参赛作品（CMC Hybrid Briefs）

## 已完成（2026-11-23）

- **官方规则已核实**（Devpost FAQ，2026-11-23 当天读取）：
  - 截止：**2026-11-30 14:00 PT = 2026-12-01 06:00 北京时间**（已用 `date` 换算确认）
  - 奖金：**总计 $30,000，冠军 $10,000**，一等奖 $7,000、二等奖 $4,000，最佳 iOS/Android/Web 各 $3,000
  - 中国大陆**不在**排除居住地名单里（排除：巴西、意大利、魁北克、克里米亚、古巴、伊朗、叙利亚、朝鲜、苏丹、白俄罗斯、俄罗斯、OFAC 制裁国家）
  - 要求：用 Firebase AI Logic 做的生成式 AI 应用，必须结合端侧 + 云端推理；公开 GitHub/GitLab 仓库 + ≤3 分钟 YouTube 演示视频；材料英文；Firebase App Check 必需
  - 配额 Sprint 3（最后一次）：**11-25 10:00 PT = 11-26 02:00 北京时间**截止申请
- **改编完成**，在 `~/workspace/hackathon-entries/buildhybridai/`，没有动 cmc-agent 的 main 分支（也没复制它的 `.env`，密钥没进任何文件）：
  - 新增 `web/` 网页应用（Chrome 平台）：Firebase AI Logic 混合推理真实代码 —— 快结论 `PREFER_ON_DEVICE`（Gemini Nano 4，失败自动回落云端）、深度简报 `PREFER_IN_CLOUD`（Gemini 2.5 Flash）、隐私开关 `ONLY_ON_DEVICE`；每条 AI 结论带 ON_DEVICE / IN_CLOUD 徽章 + 数字溯源检查
  - 新增 `cmc_agent/hybrid.py`：路由策略 + 接地提示词（模型只能用简报里的数字，不许编价格）+ 溯源检查
  - 新增 `cmc_agent/server.py`：纯标准库本地服务器，供网页用（数据桥，不调任何模型 API）
  - CLI 新增 `hybrid` 命令：只显示路由决策和提示词，不调模型
  - README、演示脚本、提交清单都是英文；本状态是中文
- **测试全部通过**：71 个测试（含新增的 hybrid 路由/提示词/溯源 14 个 + 服务器端到端 7 个），`web/app.js` 语法检查通过
- **真数据验证过**：用原仓库 `.env` 里的 key（只读，没打印、没复制）跑了 live 测试 —— BTC $60,823.56、3 credits、ETH 简报正常；服务器 `/api/brief`、`/api/hybrid-preview` 均返回 live 数据
- **演示视频已渲染完成**：`demo-video/buildhybridai-demo.mp4`，90 秒、1080×1920、8 MB，9 场景 × 10 秒；其中 4 个场景用了真实网页截图（mock 数据，诚实标注了"Firebase 未配置，上传前需用 live 项目重录"）。视频无配音，旁白词在脚本里；如需配音可按脚本重渲染

## 被堵住的 / 还没验证的

- **端侧推理没有真机跑通过**：网页里的 Firebase AI Logic 调用是真实代码，但还没有 Firebase 项目、这台机器也没有带 Gemini Nano 的 Chrome，所以 `PREFER_ON_DEVICE` → 真正在设备上跑通这条路只经过了代码检查 + 文档 + 单元测试，没有 live 验证。需要你建 Firebase 项目后在 Chrome 里实测。
- **云端模型已换，不用申请配额（2026-11-23 已改）**：`gemini-2.5-flash` 已废弃（Google 2026-11-02 公告：12 月 1 日起自动转到 `gemini-3.5-flash-lite`，且只有之前用过的项目能继续用 2.5），代码、配置和文档里的云端模型已统一改成 `gemini-3.5-flash-lite`。Gemini Developer API 后端下它是免费档的稳定文本模型，不用绑账单、不用提交 Sprint 3 配额申请，11-26 02:00 那个截止对这个项目不再适用（只有改用 Vertex AI 后端才要付费）。测试跑过，71 个仍全过。
- **视频里的应用画面是 mock 数据**：截图时 Firebase 未配置，所以 AI 结论区显示"not run"；视频里已加注说明。按脚本 shot list 用 live Firebase 项目重录 4–7 场景后再上传 YouTube。

## 需要你亲自做的事（Muse 不代办）

1. **Devpost 注册 + 提交**：截止 **12-01 06:00 北京时间**，你自己在 Devpost 上交。
2. **Firebase 项目**：控制台建项目，开 Firebase AI Logic + App Check，按 README 把 `web/firebase-config.js` 填好（本地开发用 debug token，公开部署改 reCAPTCHA v3）。
3. **CMC key**：免费 key 放到这个文件夹自己的 `.env` 里（`chmod 600 .env`），不要从原 cmc-agent 复制 `.env`。
4. **GitHub 公开仓库**：新建仓库推这个文件夹，确认 MIT 协议显示在 About 里；检查 `git status`，确保 `.env` 和 `firebase-config.js` 没进去。
5. **实测**：跑服务器，在 Chrome 里问个问题，确认出现 on-device 徽章（如果那台机器没有 Nano，徽章会显示云端回落——如实说就行，别造假）。
6. **演示视频**：按 `DEMO_VIDEO_SCRIPT.md` 最后的 shot list，用真实应用重录 4–7 场景，传 YouTube（公开，≤3 分钟），把链接填进提交表。
7. **配额**：如果云端模型要付费，11-26 02:00 北京时间前申请（表单 https://forms.gle/uPcDhaYW3iVo2AYw5）。

## 文件位置

- 文件夹：`~/workspace/hackathon-entries/buildhybridai/`
- 英文 README：`README.md`
- 提交清单：`SUBMISSION_CHECKLIST.md`
- 视频脚本：`DEMO_VIDEO_SCRIPT.md`
- 渲染视频（如果成功）：`demo-video/buildhybridai-demo.mp4`
