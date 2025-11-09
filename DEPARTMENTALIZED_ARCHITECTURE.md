# 部门化安全分析系统架构文档

## 概述

本项目已成功实现部门化架构，将原有的单一安全分析流程重构为多个专业部门协同工作的模式，提高了系统的模块化程度和可维护性。

## 架构特点

### 1. 部门化组织结构

系统现在包含以下专业部门：

- **进程部门 (Process Department)**: 负责系统进程监控和分析
- **日志部门 (Log Department)**: 负责系统日志收集和分析
- **服务部门 (Service Department)**: 负责系统服务状态监控
- **网络部门 (Network Department)**: 负责网络连接和安全分析
- **响应部门 (Response Department)**: 负责安全事件响应
- **协调部门 (Coordination Department)**: 负责部门间协调
- **威胁整合部门 (Secretary)**: 负责综合分析和报告生成

### 2. 工作流程

#### 顺序执行阶段
1. **数据收集阶段**: 各专业部门并行收集数据
   - 进程部门收集进程信息
   - 日志部门收集系统日志
   - 服务部门收集服务状态
   - 网络部门收集网络连接信息

2. **分析阶段**: 各部门对收集的数据进行专业分析
   - 每个部门使用专门的分析工具
   - 生成部门级别的安全评估报告

3. **整合阶段**: 威胁整合部门(秘书)进行综合分析
   - 收集所有部门的分析结果
   - 进行跨部门威胁关联分析
   - 生成最终的综合安全报告

## 技术实现

### 1. 核心文件修改

#### main.py
- 重构了 `run_custom_workflow` 函数
- 实现了部门化的顺序执行逻辑
- 添加了部门间数据传递机制

#### tools/security_tools.py
- 新增了部门历史管理功能
- 添加了专业化的安全分析工具
- 实现了数据持久化机制

#### agents/security_agents.py
- 扩展了工具集，添加了部门专用工具
- 增强了代理的专业化能力

### 2. GUI界面重构

#### 仪表盘功能移除
- 原dashboard_screen.py已被完全移除
- 系统现在专注于核心AI应急响应功能
- 用户界面简化，提升系统性能和维护性

### 3. 数据存储结构

#### 部门历史文件
位置: `data/department_history/{department_name}/history.json`

结构:
```json
{
    "department": "部门名称",
    "created_at": "创建时间",
    "updated_at": "更新时间",
    "analysis_history": [],
    "data_collection_history": [],
    "statistics": {
        "total_analyses": 0,
        "total_threats_detected": 0,
        "last_analysis_time": null
    }
}
```

## 新增功能

### 1. 部门历史管理
- `load_department_history()`: 加载部门历史数据
- `save_department_analysis()`: 保存部门分析结果
- 自动维护部门统计信息

### 2. 专业化分析工具
- `filter_processes_by_time()`: 按时间过滤进程
- `get_network_connections()`: 获取网络连接信息
- `analyze_network_security()`: 网络安全分析
- `analyze_service_security()`: 服务安全分析

### 3. 部门化GUI界面
- 多标签部门视图
- 实时状态监控
- 部门间数据对比
- 历史趋势分析

## 使用方式

### 1. 正常模式 (需要OpenAI API)
```bash
python main.py
```

### 2. 演示模式 (无需API)
```bash
python demo_departmentalized_gui.py
```

### 3. 测试模式
```bash
python test_departmentalized_system.py
```

## 优势

### 1. 模块化设计
- 每个部门职责明确
- 便于维护和扩展
- 支持独立测试

### 2. 可扩展性
- 易于添加新的专业部门
- 支持自定义分析工具
- 灵活的工作流程配置

### 3. 用户体验
- 直观的部门化界面
- 实时监控和更新
- 详细的历史记录

### 4. 数据管理
- 结构化的数据存储
- 完整的历史追踪
- 自动统计分析

## 未来扩展

1. **新增专业部门**
   - 内存分析部门
   - 文件系统监控部门
   - 用户行为分析部门

2. **高级功能**
   - 机器学习威胁检测
   - 自动化响应机制
   - 分布式部署支持

3. **集成能力**
   - SIEM系统集成
   - 第三方安全工具接口
   - 云平台支持

## 总结

部门化架构的实现显著提升了系统的专业化程度和可维护性。通过将复杂的安全分析任务分解为多个专业部门的协同工作，系统现在具备了更好的扩展性和用户体验。每个部门都有明确的职责和专业工具，同时保持了整体分析的一致性和完整性。