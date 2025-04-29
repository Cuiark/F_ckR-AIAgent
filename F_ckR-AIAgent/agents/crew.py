#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from crewai import Crew, Process
from config import logger

def create_security_crew(agents, tasks, verbose=True):
    """
    创建安全分析团队
    
    参数:
        agents: 包含所有Agent的字典
        tasks: 包含所有Task的列表
        verbose: 是否输出详细日志
        
    返回:
        配置好的Crew实例
    """
    # 创建安全分析团队
    security_crew = Crew(
        agents=list(agents.values()),
        tasks=tasks,
        verbose=verbose,
        process=Process.sequential
    )
    
    return security_crew


class SecurityCrew:
    def __init__(self, group_name="default_group"):
        """初始化安全分析团队"""
        # 导入必要的模块
        from agents.security_agents import create_agents
        from agents.tasks import create_tasks
        from models import setup_llm
        from config import DEFAULT_MODEL_TYPE
        
        # 设置语言模型
        self.llm = setup_llm(model_type=DEFAULT_MODEL_TYPE, for_crewai=True)
        
        # 创建agents
        self.agents = create_agents(self.llm, group_name=group_name)
        
        # 创建tasks
        self.tasks = create_tasks(self.agents)
        
        # 创建crew
        self.crew = create_security_crew(self.agents, self.tasks)
        
        # 添加角色变更回调
        self.on_role_change = None
    
    def run(self):
        """运行安全分析任务"""
        try:
            # 为每个任务调用角色变更回调
            for task in self.tasks:
                agent = None
                for a in self.agents.values():
                    if a.role == task.agent.role:
                        agent = a
                        break
                
                if agent and self.on_role_change:
                    try:
                        self.on_role_change(agent)
                    except Exception as e:
                        print(f"调用角色变更回调时出错: {str(e)}")
            
            # 使用crew.kickoff()执行所有任务，而不是crew.run()
            result = self.crew.kickoff()
            
            # 处理结果
            if isinstance(result, str):
                return [result]
            elif isinstance(result, list):
                return result
            else:
                return [str(result)]
        except Exception as e:
            print(f"执行任务时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return [f"错误: {str(e)}"]