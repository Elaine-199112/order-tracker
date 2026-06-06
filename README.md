# 订单进度追踪系统 - 使用说明

## 📱 客户看到的页面

客户打开链接 → 输入订单编号 → 看到实时进度

包含：进度条（设计确认→面料采购→生产中→已发货）+ 时间线 + 预计发货日期

## ✏️ 如何更新订单状态

**只需要编辑 `orders.json` 这一个文件。**

### 1. 添加新订单

在 `"orders"` 里面加一条：

```json
"ORD-2026004": {
  "customer": "客户名字",
  "product": "产品描述（如：足球队服 · 20套）",
  "stage_key": "design",
  "estimated_delivery": "2026年7月1日",
  "updates": [
    { "date": "6月8日", "stage_key": "design", "note": "设计方案已确认" }
  ]
}
```

### 2. 更新订单进度

找到对应订单，改两处：
- **`stage_key`** — 改成当前阶段：`design` / `fabric` / `production` / `shipping`
- **`updates`** — 在数组里加一条新记录

例如：订单从"面料采购"进入"生产中"：
```json
"stage_key": "production",
"updates": [
  ...之前的记录...,
  { "date": "6月10日", "stage_key": "production", "note": "已进入缝制车间开始生产" }
]
```

### 3. 订单发货

把 `stage_key` 改成 `"shipping"`，加上快递信息：
```json
{ "date": "6月15日", "stage_key": "shipping", "note": "已打包发货，顺丰快递：SF1234567890" }
```

页面会自动显示 🎉 已发货 的庆祝状态。

### 4. stage_key 对应关系

| stage_key | 显示 |
|-----------|------|
| design | 设计确认 |
| fabric | 面料采购 |
| production | 生产中 |
| shipping | 已发货 |

## ⚠️ 注意事项

- 订单编号建议用统一格式（如 ORD-2026001），方便管理
- JSON 格式严格，注意逗号、引号不能少
- **改完文件后，刷新页面即可看到更新**（无需重新部署）
- 改完文件后告诉我，我帮你推送更新到线上

## 🔗 分享给客户

部署完成后会得到一个链接（如 `https://xxx.github.io/order-tracker/`），直接微信发给客户即可。
客户在手机浏览器打开，体验接近小程序。
