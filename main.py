# Copyright (c) Microsoft. All rights reserved.

import asyncio

import semantic_kernel as sk
import semantic_kernel.ai.open_ai as sk_oai

import glob
import os
from typing import Dict

from semantic_kernel.kernel_extensions.extends_kernel import ExtendsKernel
from semantic_kernel.orchestration.sk_function_base import SKFunctionBase
from semantic_kernel.semantic_functions.prompt_template import PromptTemplate
from semantic_kernel.semantic_functions.prompt_template_config import (
    PromptTemplateConfig,
)
from semantic_kernel.semantic_functions.semantic_function_config import (
    SemanticFunctionConfig,
)
from semantic_kernel.utils.validation import validate_skill_name

system_message = """
"""

kernel = sk.Kernel()

from semantic_kernel.ai.open_ai import AzureChatCompletion
from semantic_kernel.ai.open_ai import AzureTextCompletion

deployment, api_key, endpoint = sk.azure_openai_settings_from_dot_env()

kernel.config.add_chat_backend("dv", AzureChatCompletion(deployment, endpoint, api_key))
kernel.config.add_text_backend("text", AzureTextCompletion(deployment, endpoint, api_key))

prompt_config = sk.PromptTemplateConfig.from_completion_parameters(
    max_tokens=2000, temperature=0.7, top_p=0.8
)



async def chat() -> bool:
    context_vars = sk.ContextVariables()

    try:
        user_input = input("User:> ")
        context_vars["user_input"] = user_input
    except KeyboardInterrupt:
        print("\n\nExiting chat...")
        return False
    except EOFError:
        print("\n\nExiting chat...")
        return False

    if user_input == "exit":
        print("\n\nExiting chat...")
        return False

    assist = ""

    skills = import_chat_skill_from_directory("./questions", "PatternMatchingSkill")
    # loop skill and call skill
    for key, skill in skills.items():
        context = skill(user_input)
        print(f"{key}:> {context}")

    print(f"assist:> {assist}")
    return True


async def main() -> None:
    chatting = True
    while chatting:
        chatting = await chat()

def import_chat_skill_from_directory(
    parent_directory: str, skill_directory_name: str
    ) -> Dict[str, SKFunctionBase]:
        CONFIG_FILE = "config.json"
        PROMPT_FILE = "skprompt.txt"

        kernel =  sk.Kernel()

        validate_skill_name(skill_directory_name)

        skill_directory = os.path.join(parent_directory, skill_directory_name)
        skill_directory = os.path.abspath(skill_directory)

        if not os.path.exists(skill_directory):
            raise ValueError(f"Skill directory does not exist: {skill_directory_name}")

        skill = {}

        directories = glob.glob(skill_directory + "/*/")
        for directory in directories:
            dir_name = os.path.dirname(directory)
            function_name = os.path.basename(dir_name)
            prompt_path = os.path.join(directory, PROMPT_FILE)

            # Continue only if the prompt template exists
            if not os.path.exists(prompt_path):
                continue

            config = PromptTemplateConfig()
            config_path = os.path.join(directory, CONFIG_FILE)
            with open(config_path, "r") as config_file:
                config = config.from_json(config_file.read())

            # Load Prompt Template
            with open(prompt_path, "r") as prompt_file:
                template = sk.ChatPromptTemplate(
                    prompt_file.read(), kernel.prompt_template_engine, config
                )

            # Prepare lambda wrapping AI logic
            function_config = SemanticFunctionConfig(config, template)

            skill[function_name] = kernel.register_semantic_function(
                skill_directory_name, function_name, function_config
            )

if __name__ == "__main__":
    asyncio.run(main())
