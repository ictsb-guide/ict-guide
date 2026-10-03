# 计算所 · 避坑指南

[打开网站](https://ictsb-guide.github.io/ict-guide/)

按导师与计算所整体评价浏览记录。投稿请发邮件至 **sbictsb@gmail.com**：主题填写导师名字，正文填写评价。

## 维护内容

- `content/entries/`：一份 JSON 文件对应一条记录，增删文件即可增删记录。
- `content/collections/`：批量记录，编辑或删除 `entries` 数组中的对象。
- `examples/entry-template.json`：新记录模板。设置唯一 `id`，写好正文后将 `draft` 改为 `false`。
- `index.template.html`：网页样式与结构。
- `site.json`：网站标题与简介。

提交到 `main` 后，GitHub Actions 自动构建并发布。首次在仓库 Settings → Pages 中选择 GitHub Actions。

## 检查与预览

使用 Python 标准库，无需安装依赖：

```bash
python3 build.py --check
python3 build.py
python3 -m http.server 8000 --directory dist --bind 127.0.0.1
```

仅提交经过脱敏、可公开的内容。不要填写日期、私人联系方式或身份线索，草稿文件在公开仓库中也能被访问。
