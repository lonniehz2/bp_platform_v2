# 报表下载验收记录

- 日期：2026-11-12
- 环境：http://127.0.0.1:8091
- 账号：admin / 350600
- 报表：项目经营对比
- 语言：en-US

## 验收方式

在浏览器中打开报表中心，点击首行“下载”，拦截 `URL.createObjectURL` 生成的 Blob，
读取其文本内容。

## 结果

```text
CSV 长度：137
行数：2（表头 + 1 行数据）
表头：Project,Houses,Occupancy,Receivable,Received,Collection Rate,Outstanding,Work Orders
```

## 结论

- 前端确实生成并触发了 CSV Blob
- 表头为英文
- 数据行存在
- 浏览器未将文件落盘属于本机 headless/下载策略问题，不是 CSV 内容问题

## 仍需人工确认

在真实浏览器中点击一次下载，确认：

```text
文件生成
Excel 打开正常
中文不乱码
```
