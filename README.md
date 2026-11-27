# 字里寻踪

当前六字网站与 Streamlit 应用的发布源为本仓库的 **gh-pages 分支**。启动文件为 `streamlit_app.py`；`main` 分支保存早期参赛材料，不能作为当前网站的发布源。

## 本地运行

```sh
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

百炼密钥放在 Streamlit Cloud Secrets 或本地 `.streamlit/secrets.toml` 中的 `DASHSCOPE_API_KEY`。可选配置为 `QWEN_MODEL`、`QWEN_BASE_URL`。密钥文件已排除在 Git 之外。

## 发布与验证

```sh
python check_release.py
```

这会检查发布依赖、构建真实网页、验证脚本语法并运行问答与预算回归测试。生成的 `validation-final.html` 只供本地检查，不提交。检查通过后，将同一提交推送到 `gh-pages`；Streamlit Cloud 继续使用该分支的 `streamlit_app.py`。

`published-theme.html` 保留原有设计与资源包，`release_quality.py` 对新增关键挂载点校验命中次数。修改模板或挂载点后必须重新验证；不要从临时目录复制部分文件发布。

## 本次稳定性改进

- 问答入口校验字段类型与长度，异常请求返回可读错误。
- 故事问答仅显示能在站内资料中逐字核对的摘录；模型自由生成的结论不会直接作为文化事实展示。摘录存在不等于原始资料事实已被独立核实，仍保留原始出处供读者判断。
- 每次实际模型调用（含重试）都占用共享预算，默认每分钟 40 次、每天 1000 次、最多 4 个并发。会话冷却另外保留。可通过环境变量 `QWEN_CALLS_PER_MINUTE`、`QWEN_CALLS_PER_DAY`、`QWEN_MAX_CONCURRENT` 调整。
- 预算使用 SQLite，默认保存在系统临时目录。同一主机的多个进程共享；不同主机需把 `QWEN_BUDGET_DB` 配到支持 SQLite 锁的共享本地存储，或另接集中式预算服务。当前实现不声称跨主机全局限流，也不是 token 费用的精确计费系统。
- 问答缓存有效期 10 分钟，并绑定资料哈希、提示版本和模型配置。
- 所有词典义项按读音显示；成功查询会保留浏览器缓存。`dictionary-cache.json` 中已保存的公开萌典条目可在网络失败时兜底，缓存显示会明确标注。原词条链接与来源署名保留，原始词典数据未改写。可用 `python update_dictionary_cache.py` 刷新示范字缓存；网络失败时不会覆盖现有文件。
- 图片通过现有 Streamlit 组件的资源目录提供，自动适配云端代理前缀，使用当前提交的素材。`python build_atlas.py` 从 `static/atlas` 生成尺寸不超过 1600 像素的 WebP 和内容哈希资源清单；更换素材后先重新生成，再运行发布检查。原始素材保留。
- 页面导航增加历史状态恢复和故事分享链接，快速切页会丢弃过期回调。
- 收藏支持逐条移除、JSON 备份导入/导出和文本笔记导出。收藏仍保存在当前浏览器，不需要账号。

## 仍需持续验证

真实移动设备与屏幕阅读器、长时负载测试、全部出处的事实核查和素材授权复核仍需单独进行。自动测试使用模拟模型响应，不会调用付费接口。
