# RemovePostFixV2

一个用于处理 AUTOSAR ARXML 的脚本，按规则删除不需要的 `ComSignal` 容器，并输出严格格式化的 ARXML 文件。

## 功能概述

- 解析 AUTOSAR ARXML，自动识别命名空间。
- **步骤 1**：删除 `ComSignal` 容器中 `SHORT-NAME` 不匹配指定 `oCAN` 正则的条目。
- **步骤 2**：删除 `ComSignal` 容器中 `SHORT-NAME` 以 `XCP_Rx` 或 `XCP_Tx` 开头的条目。
- 输出文件强制使用指定的 XML 声明行，并统一为 **CRLF** 行尾。

## 环境依赖

- Python 3.8+
- `lxml`

安装依赖：

```bash
pip install lxml
```

## 使用方法

```bash
python3 RemovePostFixV2.py --in input.arxml --out output.arxml
```

### 参数说明

- `--in`：输入 ARXML 文件路径（必填）
- `--out`：输出 ARXML 文件路径（必填）
- `--ocan_regex`：匹配 `SHORT-NAME` 的正则（可选，默认 `oCAN00`）

示例：

```bash
python3 RemovePostFixV2.py \
  --in 1.arxml \
  --out 2.arxml \
  --ocan_regex "oCAN\\d{2}"
```

## 处理规则说明

1. **仅处理 ComSignal 容器**：通过 `DEFINITION-REF` 等于 `/MICROSAR/Com/ComConfig/ComSignal` 识别。
2. **Step 1（oCAN 正则匹配）**：`SHORT-NAME` 未匹配正则则删除该容器。
3. **Step 2（XCP 过滤）**：`SHORT-NAME` 以 `XCP_Rx` 或 `XCP_Tx` 开头则删除该容器。
4. **输出格式**：XML 声明固定为 `<?xml version="1.0" encoding="UTF-8" standalone="no"?>`，并强制 CRLF。

## 输出日志示例

脚本执行完成后会输出删除统计：

```
[OK] {'step': 1, 'scanned': 120, 'removed': 30} {'step': 2, 'scanned': 90, 'removed': 5, 'rule': 'SHORT-NAME startswith XCP_Rx / XCP_Tx'} out= output.arxml temp_step1= 2temp.arxml temp_step2= 3temp.arxml
```

## 测试阶段输出说明

当前仓库包含用于验证的“理想输出”与程序的“对比输出”：

- **理想输出**：`2.arxml`、`3.arxml`、`4.arxml`、`5.arxml`、`6.arxml`
- **程序输出（对比用）**：`2temp.arxml`、`3temp.arxml`、`4temp.arxml`、`5temp.arxml`、`6temp.arxml`

这些 `*temp.arxml` 文件是程序运行后生成的临时输出，用于和理想输出进行对比，验证处理逻辑是否正确。

## 文件说明

- `RemovePostFixV2.py`：主脚本。
- `*.arxml`：示例或测试 ARXML 文件。
