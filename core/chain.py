"""
In this module, we define the llm chains to be used
"""

from .llm_service import LLMService
from langchain.prompts.prompt import PromptTemplate


async def create_chain(prompt_template, input_variables, output_parser):
    llm = LLMService()
    prompt = PromptTemplate(template=prompt_template, input_variables=input_variables)
    chain = prompt | llm | output_parser
    return chain
