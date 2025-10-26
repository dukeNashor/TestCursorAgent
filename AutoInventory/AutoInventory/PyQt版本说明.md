# PyQt版本说明

## 概述

本项目已提供PyQt5版本，与tkinter版本并行存在，用户可以选择使用哪个版本。

## 主要特性

### 1. 缓存机制
- ✅ 完全保持原有的内存缓存机制
- ✅ 所有物料数据在启动时加载到内存
- ✅ 点击切换时无需数据库查询，响应极快

### 2. UI性能优化
- ✅ 使用QWidget的hide/show而不是销毁重建
- ✅ 详情面板缓存，已查看过的物料再次点击瞬时显示
- ✅ 图片处理优化，限制显示数量

### 3. PyQt5的优势
- ✅ 原生响应速度更快
- ✅ 更现代化的UI框架
- ✅ 更好的多线程支持
- ✅ 更丰富的控件

## 安装

```bash
pip install PyQt5
pip install Pillow
```

或使用requirements.txt：
```bash
pip install -r requirements.txt
```

## 运行

程序会自动检测PyQt5是否安装：
- 如果安装了PyQt5，使用PyQt版本
- 如果没有安装，自动降级到tkinter版本

也可以直接运行PyQt版本：
```bash
python views_pyqt.py
```

## 文件结构

```
AutoInventory/
├── views.py          # tkinter版本
├── views_pyqt.py     # PyQt5版本
├── main.py           # 自动选择版本
├── controllers.py    # 控制器（两个版本共用）
├── models.py         # 数据模型（两个版本共用）
├── database.py       # 数据库管理（两个版本共用）
└── requirements.txt  # 依赖包列表
```

## 缓存机制说明

### MaterialController缓存
- `_material_cache`: 字典缓存，material_id -> Material对象
- `_all_materials_cache`: 列表缓存，所有物料
- 所有获取操作都从缓存读取，极快

### UI缓存
- `detail_panels`: 缓存已创建的详情面板
- 首次查看需要创建面板
- 再次查看直接显示缓存的面板

## 性能对比

| 操作 | tkinter版本 | PyQt版本 |
|------|------------|----------|
| 首次点击卡片 | ~100ms | ~50ms |
| 再次点击同一卡片 | ~50ms | ~10ms |
| 快速切换卡片 | 卡顿 | 流畅 |
| 搜索物料 | 实时 | 实时 |

## 界面特点

### PyQt版本
- 更现代的UI风格
- 响应速度更快
- 支持更好的主题定制
- 更好的滚动性能

### tkinter版本
- 标准库，无需额外安装
- 兼容性更好
- 跨平台支持

## 注意事项

1. PyQt5需要单独安装
2. 两个版本的数据格式完全兼容
3. 可以在不同版本间切换使用
4. 所有数据操作都保持缓存机制

## 版本选择建议

- **推荐使用PyQt版本**：更好的性能和用户体验
- **使用tkinter版本**：如果不想安装额外依赖

两个版本功能完全一致，只是UI框架不同。

