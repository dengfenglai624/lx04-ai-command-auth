# LX04 AI 命令授权系统 - 交接文档

> 更新时间：2026-10-22 21:12 | 状态：**可用，全链路已验证**
> 用途：AI（Codex / WorkBuddy）在 PC 上执行命令前，向小爱音箱 LX04 屏幕推送授权弹窗，用户点 YES/NO 决定是否放行。

---

## 1. 项目根目录

```
C:\Users\VALEO\Documents\Qoder\2026-10-21\17272210\firmware_work\lx04_auth\
```

## 2. 系统架构

```
[PC: AI Agent / WorkBuddy]
    │  HTTP POST /api/add （提交待授权命令）
    ▼
[PC: web_auth_server.py  0.0.0.0:8080]  ←—— 授权状态唯一存储（内存）
    ▲                                    │
    │  GET /api/pending (每2s轮询)        │  GET /api/pending (每2s轮询)
    │                                    ▼
    │                    [LX04 音箱 App com.lx04.codexauth]
    │                        OverlayService 前台服务 + 悬浮窗弹窗
    └── POST /api/auth ←──── 用户点击 DENY / ALLOW
```

- 两端都通过 HTTP 与服务器交互，**无直连**。服务器是纯内存状态（无数据库，重启即清空）。
- Web 页面（浏览器打开 `http://192.168.123.38:8080`）和音箱弹窗是两个平行的授权 UI，共用同一套 API。

## 3. 关键环境信息

| 项 | 值 |
|---|---|
| PC 局域网 IP | 192.168.123.38（服务器绑定 0.0.0.0:8080） |
| LX04 音箱 | 192.168.123.134:5555（adb over WiFi），屏幕 800x480，Android 8.1（API 27） |
| PC 上另一台 adb 设备 | 21065/C3VX26772（与本项目无关，操作时必须 `-s 192.168.123.134:5555`） |
| Android SDK | `C:\Users\VALEO\android-sdk`（local.properties 已配置） |
| JDK | ⚠️ **必须用 JDK 21**：`C:\Program Files\Microsoft\jdk-21.0.12.101-hotspot`（Eclipse Adoptium 目录下只有 JDK 25，JDK 25 与 Gradle 8.12 不兼容） |
| Gradle | 项目内置：`codex_app\gradle-8.12\bin\gradle`（无需 gradlew） |
| Python | 服务器用任意 Python 3 即可（标准库实现，零依赖） |

### 编译命令（坑已踩平，直接照抄）

```bash
cd codex_app
JAVA_HOME='C:\Program Files\Microsoft\jdk-21.0.12.101-hotspot' ./gradle-8.12/bin/gradle assembleDebug -q
```

⚠️ JAVA_HOME 必须用**反斜杠 Windows 路径**，正斜杠会被 gradle.bat 判定为 invalid directory。

### 安装 / 启动

```bash
adb connect 192.168.123.134:5555
adb -s 192.168.123.134:5555 install -r codex_app/app/build/outputs/apk/debug/app-debug.apk
adb -s 192.168.123.134:5555 shell am start -n com.lx04.codexauth/.MainActivity
# 界面上点 CODEX 或 WORK BUDDY 启动前台服务（内部用 startForegroundService，勿改回 startService）
```

### 服务器启动

```bash
cd lx04_auth
python web_auth_server.py
```

⚠️ 启动前确认 8080 端口只有一个进程：`netstat -ano | findstr :8080`。曾出现两个 python 同时监听导致请求分流、状态分裂的 bug。

## 4. HTTP API 规范

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/` | 科幻风 Web 授权页面 |
| GET | `/api/pending` | 待授权命令列表（App 和 Web 页轮询此接口） |
| GET | `/api/history` | 最近 50 条已处理记录 |
| GET | `/api/check/<id>` | 查询单条命令状态：`pending` / `authorized` / `denied` / `null`(不存在) |
| POST | `/api/auth` | body `{"id":"1","authorized":true}` —— App 弹窗按钮回传 |
| POST | `/api/add` | body `{"command":"...","description":"...","risk_level":"low|medium|high"}` → 返回 `{"status":"ok","id":"N"}` |

## 5. 文件清单

| 文件 | 说明 |
|---|---|
| `web_auth_server.py` | **核心服务器**。含 API + 内嵌科幻风 WEB_HTML + `add_command()` / `check_authorization()`（仅同进程可用） |
| `lx04_auth_client.py` | **外部 AI 接入推荐入口**。`request_authorization(command, description, risk_level, timeout)` 跨进程 HTTP 提交并阻塞等待结果，返回 True/False |
| `test_workbuddy.py` | 端到端测试脚本（HTTP 客户端版），运行后在音箱点 ALLOW 验证 |
| `test_codex.py` / `test_auth.py` / `test_web.py` | 早期测试脚本（import 模块方式，**跨进程无效**，仅参考） |
| `codex_app/` | Android 工程源码 |
| `build_codex.bat` / `install_codex.bat` | Windows 编译/安装脚本（bat 版，依赖 PATH 里的 java/gradle，实测建议用上面的 bash 命令） |
| `README.md` / `QUICKSTART*.md` | 早期文档，部分内容已过时，以本文档为准 |

### Android 端源码（codex_app/app/src/main/java/com/lx04/codexauth/）

| 文件 | 说明 |
|---|---|
| `MainActivity.java` | 启动页。ScrollView + CODEX / WORK BUDDY 两个模式按钮，Android 8+ 用 `startForegroundService()` 启动服务 |
| `OverlayService.java` | **核心服务**。前台服务 + 2s 轮询 `/api/pending` → `TYPE_APPLICATION_OVERLAY` 悬浮窗弹授权框 → 按钮回传 `/api/auth`。服务器地址硬编码在第 41 行 `pcServerUrl = "http://192.168.123.38:8080"` |
| `BootReceiver.java` | 开机自启广播接收器 |

- minSdk 26 / targetSdk 34，Java 8 语法（⚠️ 不能用 Java 9+ API，`readAllBytes()` 曾导致 8.1 闪退）
- 悬浮窗权限已授予；UI 为霓虹 HUD 风（drawable/ 下 9 个自定义 shape）

## 6. 已验证功能（2026-10-22 实测）

- ✅ App 编译 → 安装 → 服务启动 → 悬浮窗弹出 → 点 ALLOW → `/api/check` 返回 `authorized`（adb 模拟点击 `input tap 593 360` 验证 YES/ALLOW 按钮位置）
- ✅ 外部进程通过 `/api/add` 提交 → 音箱 2s 内弹窗
- ✅ Web 页面与音箱弹窗并行工作
- ✅ 科幻 UI 改版完成（Web + 音箱端）

## 7. 已知问题与改进方向（按优先级）

1. **API 无鉴权**：局域网内任何设备都能 `/api/add` / `/api/auth`。建议加 token 或绑定 MAC 白名单。
2. **服务器状态在内存**：重启丢失历史。需要持久化可加 SQLite/JSON 落盘。
3. **弹窗无超时**：用户不点击，弹窗永远挂着，且 `isShowing=true` 会阻塞后续命令弹窗。建议 OverlayService 加超时自动 remove + 上报 timeout。
4. **pending 队列无清理**：无人响应的命令永远留在列表里，App 每次都弹第一条。建议 `/api/add` 带 expiry 或服务器定期清理超时 pending。
5. **check_authorization() 双轨制**：`web_auth_server.py` 里的同进程版和 `lx04_auth_client.py` 的 HTTP 版并存，AI 接入**一律用后者**。可考虑删掉同进程版避免混淆。
6. **IP 硬编码**：App 的 `pcServerUrl`、测试脚本里的路径和 IP 都是硬编码，换网络需改三处（OverlayService.java 第 41 行要重新编译）。
7. **风险等级只影响颜色**：high/low 没有差异策略（如 high 强制二次确认）。
8. **串行弹窗**：多条 pending 时 App 只显示第一条（`commands.getJSONObject(0)`），处理完才能看下一条。

## 8. 快速自检命令（接手后先跑这个）

```bash
# 1. 设备在线？
adb devices   # 应看到 192.168.123.134:5555
# 2. 服务器活着？
curl http://192.168.123.38:8080/api/pending   # 应返回 []
# 3. App 服务在跑？
adb -s 192.168.123.134:5555 shell "pidof com.lx04.codexauth"
# 4. 全链路？
curl -X POST http://192.168.123.38:8080/api/add -H "Content-Type: application/json" \
  -d '{"command":"echo hello","description":"handoff test","risk_level":"low"}'
# 看音箱屏幕是否弹窗，点 ALLOW 后：
curl http://192.168.123.38:8080/api/check/1   # 应返回 authorized
```
