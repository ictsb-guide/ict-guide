#!/usr/bin/env python3
"""Build a portable static website, with only the Python standard library."""
import argparse
import json
import re
import shutil
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parent
CATEGORIES = {"毕业与培养", "科研与指导", "工作与待遇", "沟通与管理", "其他经历"}
STATUSES = {"个人经历", "公开资料", "待补充", "已更正", "演示条目"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def string(value):
    return isinstance(value, str) and bool(value.strip())


def validate_source(source):
    require(isinstance(source, dict), "来源必须是对象")
    require(string(source.get("label")), "来源缺少 label")
    url = source.get("url", "")
    require(string(url), "来源缺少 url")
    parsed = urlsplit(url)
    if parsed.scheme:
        require(parsed.scheme in {"https", "http"} and bool(parsed.netloc), "来源仅支持 http/https")
    else:
        path = unquote(parsed.path)
        require(not parsed.netloc and path.startswith("evidence/") and "\\" not in path,
                "本地来源应使用 evidence/文件名")
        target = (ROOT / "public" / path).resolve()
        require(target.is_relative_to((ROOT / "public" / "evidence").resolve()), "来源路径不能越界")
        require(target.is_file(), f"找不到证据文件：{path}")


def load_data():
    site = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
    require(isinstance(site, dict), "site.json 必须是对象")
    for key in ("title", "institution", "description", "repository"):
        require(string(site.get(key)), f"site.json 缺少 {key}")
    require(site["repository"].startswith("https://github.com/"), "repository 必须是 GitHub 仓库地址")
    entries, ids, references = [], set(), []
    files = sorted((ROOT / "content" / "entries").glob("*.json"))
    files += sorted((ROOT / "content" / "collections").glob("*.json"))
    for file in files:
        try:
            payload = json.loads(file.read_text(encoding="utf-8"))
            if file.parent.name == "collections":
                require(isinstance(payload, dict) and isinstance(payload.get("entries"), list), "合集需要 entries 数组")
                for reference in payload.get("references", []):
                    require(isinstance(reference, dict) and string(reference.get("heading")) and string(reference.get("body")), "检索资料需要 heading 和 body")
                    require(isinstance(reference.get("sources"), list), "检索资料需要 sources 数组")
                    for source in reference["sources"]:
                        validate_source(source)
                    references.append(reference)
                items = payload["entries"]
            else:
                items = [payload]
            for item in items:
                validate_entry(item, ids)
                if not item["draft"]:
                    entries.append(item)
        except (ValueError, TypeError, KeyError) as exc:
            raise ValueError(f"{file.relative_to(ROOT)}：{exc}") from exc
    entries.sort(key=lambda x: x["id"], reverse=True)
    return {"site": site, "entries": entries, "references": references}


def validate_entry(item, ids):
    require(isinstance(item, dict), "条目必须是对象")
    for key in ("id", "advisor", "group", "title", "category", "summary", "status"):
        require(string(item.get(key)), f"缺少字符串字段 {key}")
    require(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", item["id"]), "id 应为小写英文、数字和连字符")
    require(item["id"] not in ids, f"重复 id：{item['id']}")
    ids.add(item["id"])
    require("updated" not in item and "period" not in item, "条目不应包含 updated 或 period 日期字段")
    require(item["category"] in CATEGORIES, "category 不在允许列表中")
    require(item["status"] in STATUSES, "status 不在允许列表中")
    for key in ("draft", "demo"):
        require(type(item.get(key)) is bool, f"{key} 必须是 true 或 false")
    require(item["demo"] == (item["status"] == "演示条目"), "演示条目的 demo 与 status 必须一致")
    require(isinstance(item.get("tags"), list) and all(string(x) for x in item["tags"]), "tags 必须是字符串数组")
    require(isinstance(item.get("sections"), list) and bool(item["sections"]), "sections 至少包含一个段落")
    for section in item["sections"]:
        require(isinstance(section, dict) and string(section.get("heading")) and string(section.get("body")), "段落需要 heading 和 body")
    require(isinstance(item.get("sources"), list), "sources 必须是数组")
    for source in item["sources"]:
        validate_source(source)
    require(isinstance(item.get("response", ""), str), "response 必须是字符串")
    require(item.get("scope", "advisor") in {"advisor", "overall"}, "scope 应为 advisor 或 overall")


def build(output):
    data = load_data()
    template = (ROOT / "index.template.html").read_text(encoding="utf-8")
    require(template.count("/*__SITE_DATA__*/") == 1, "模板必须包含一个数据插入点")
    # Escape script terminators and separators before embedding JSON in HTML.
    payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    output.mkdir(parents=True, exist_ok=True)
    # Remove old generated evidence so deleted files cannot survive a rebuild.
    evidence = output / "evidence"
    if evidence.exists():
        shutil.rmtree(evidence)
    public = ROOT / "public" / "evidence"
    if public.exists():
        shutil.copytree(public, evidence, ignore=shutil.ignore_patterns(".DS_Store", ".gitkeep"))
    (output / "index.html").write_text(template.replace("/*__SITE_DATA__*/", payload), encoding="utf-8")
    (output / ".nojekyll").touch()
    print(f"已生成 index.html，共 {len(data['entries'])} 条公开记录。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="仅检查内容")
    args = parser.parse_args()
    try:
        if args.check:
            data = load_data()
            print(f"内容检查通过：{len(data['entries'])} 条公开记录。")
        else:
            build(ROOT / "dist")
    except (ValueError, OSError) as exc:
        parser.exit(1, f"构建失败：{exc}\n")
