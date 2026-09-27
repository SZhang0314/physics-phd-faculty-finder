# Physics PhD Atlas

面向物理学 PhD 申请者的学校级导师调研网站。当前版本按 **2027 QS 世界大学综合排名**筛出美国院校中的前 30 所，整理 30 个独立学校页、1,629 条教授/研究人员记录和 90 个重点实验室/研究平台入口。

## 页面功能

- 首页按学校展示 QS 名次、突出方向、方向分布与重点实验室
- 每所学校拥有独立详情页，可按姓名、关键词和细分方向筛选教师
- 教师条目提供研究方向摘要、研究方式、官方主页/名录和论文检索入口
- 教师条目可展开查看所属院系、职称、公开学位、PhD/暑研历年名额及组内学生公开背景
- 公开数据来源、收录人数、核验日期与跨校口径差异
- 响应式布局，可直接部署到 GitHub Pages

## 数据口径

- 学校范围：[QS World University Rankings 2027](https://www.topuniversities.com/qs-top-uni-wur)
- 导师资料：物理系官方在职名录、研究领域页面及研究生培养名单
- 最后核验：2026-09-27

收录以官方页面定义的 active/core/standing faculty 为主，并保留官网明确列出的联合或关联研究人员；排除荣休、纯教学、访问与兼职岗位。不同学校官网口径并不完全一致，因此网站逐校公开人数和来源，而不制造不可靠的统一覆盖百分比。页面中的导师不一定正在接收博士生；申请前应再次核对导师主页、近期论文、实验室成员、经费与院系招生要求。

招生名额必须有年份、人数和官方来源；“正在招人”不会被换算成人数，“未公开”也不等于 0。学生国籍只在本人或学校明确公开时记录，绝不通过姓名、照片或毕业学校推断。

## 数据与构建

- `research/sources/`：官方页面的检索存档
- `research/parsed.json`：标准化教师记录
- `research/public_enrichment.json`：逐条核验的学位、招生和课题组公开背景
- `scripts/parse_corpus.py`：名录解析与分类
- `scripts/build_site.py`：静态站点生成器
- `dist/data/schools.json`：网站使用的完整公开数据

重新生成：

```powershell
python -X utf8 scripts/parse_corpus.py --output research\parsed.json
python -X utf8 scripts/build_site.py
```

## 本地预览

无需安装依赖。用任意静态文件服务器打开 `dist` 目录即可，例如：

```powershell
python -m http.server 4173 --directory dist
```

然后访问 `http://127.0.0.1:4173`。

## 发布

仓库包含 GitHub Pages 工作流。推送到 `main` 分支后，会将 `dist` 目录发布为静态网站。
