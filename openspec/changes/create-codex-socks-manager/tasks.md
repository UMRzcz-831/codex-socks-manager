## 1. 项目与安全基础

- [x] 1.1 建立 Python 包、console script、MIT License、README、`.gitignore` 与 GitHub Actions，并验证包可安装且仓库无凭据样本
- [x] 1.2 实现 XDG 路径、文件锁、原子写入和权限工具，并以单元测试验证目录 0700、敏感文件 0600

## 2. 代理配置管理

- [x] 2.1 实现名称和 socks5h/socks5/http/https URL 校验、凭据脱敏，并验证无效输入和控制字符测试
- [x] 2.2 实现 add/list/edit/del/off/use 状态操作，并验证 JSON 输出、编辑回滚、活动删除保护和并发写入

## 3. Codex 运行时集成

- [x] 3.1 实现 standalone/npm/pnpm 发现和受管 launcher 安装，并用 fake 安装布局验证不递归和参数透传
- [x] 3.2 实现完整代理环境与 NO_PROXY 合并，并验证代理和 off 两种 launcher 行为不泄露凭据
- [x] 3.3 实现当前 UID 的 app-server 角色发现、有界重启与回滚，并用 fake 进程/runner 验证不会匹配无关进程
- [x] 3.4 实现 Codex Doctor HTTPS/WSS/app-server 诊断和 403 分类，并用 fixture 验证 WSS 非 101、代理故障和授权故障

## 4. 更新恢复与迁移

- [x] 4.1 实现 backup/restore 校验快照与被覆盖 launcher 恢复，并验证 symlink、缺失文件、校验失败和 pre-restore 场景
- [x] 4.2 实现 safe-update 固定流程及更新失败恢复，并验证保留新版真实 Codex、不执行二进制降级
- [x] 4.3 实现旧 guard 兼容入口和当前 JP/US 配置迁移命令，并通过脱敏迁移 fixture 验证幂等

## 5. 验证、部署与发布

- [x] 5.1 运行 pytest、compile、ShellCheck、OpenSpec strict validate 与密钥扫描，所有检查必须通过
- [x] 5.2 在当前 VPS 创建私密备份、安装工具、迁移 JP/US 配置并运行 check，验证 HTTPS ok、WSS 101 和 app-server 代理环境
- [ ] 5.3 初始化并提交 main 分支，创建公开 GitHub 仓库、Issues、Projects 看板和 v0.1.0 Release，并核对远程仓库不含凭据
