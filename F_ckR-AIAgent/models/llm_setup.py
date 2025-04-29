#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from langchain_openai import ChatOpenAI
from config import logger, MODEL_CONFIGS, DEEPSEEK_API_KEY, DEEPSEEK_API_BASE

def setup_llm(model_type="openai", for_crewai=False):
    """
    配置并返回语言模型实例
    
    参数:
        model_type: 模型类型，支持 "openai"、"deepseek-chat"、"deepseek-reasoner"、"openai-4o" 等
        for_crewai: 是否用于CrewAI框架，影响模型名称格式
        
    返回:
        配置好的LLM实例
    """
    if model_type == "openai":
        # OpenAI模型配置
        return ChatOpenAI(
            temperature=MODEL_CONFIGS[model_type]["temperature"],
            model=MODEL_CONFIGS[model_type]["model"]
        )
    elif model_type == "deepseek-chat" or model_type == "deepseek-reasoner":
        os.environ["OPENAI_API_KEY"] = DEEPSEEK_API_KEY
        os.environ["OPENAI_API_BASE"] = DEEPSEEK_API_BASE
        # 根据 for_crewai 区分模型名
        print("for_crewai:", for_crewai)
        if for_crewai:
            if model_type == "deepseek-chat":
                model_name = MODEL_CONFIGS[model_type]["crewai_model"]
            else:
                model_name = MODEL_CONFIGS[model_type]["crewai_model"]
        else:
            if model_type == "deepseek-chat":
                model_name = MODEL_CONFIGS[model_type]["model"]
            else:
                model_name = MODEL_CONFIGS[model_type]["model"]
        return ChatOpenAI(
            temperature=MODEL_CONFIGS[model_type]["temperature"],
            model=model_name,
            openai_api_key=DEEPSEEK_API_KEY,
            openai_api_base=DEEPSEEK_API_BASE,
            model_kwargs=MODEL_CONFIGS[model_type].get("model_kwargs", {})
        )
    elif model_type == "openai-4o":
        return ChatOpenAI(
            temperature=MODEL_CONFIGS[model_type]["temperature"],
            model=MODEL_CONFIGS[model_type]["model"]
        )
    else:
        # 默认使用OpenAI模型
        logger.warning(f"未知模型类型: {model_type}，使用默认OpenAI模型")
        return ChatOpenAI(
            temperature=MODEL_CONFIGS["openai"]["temperature"],
            model=MODEL_CONFIGS["openai"]["model"]
        )