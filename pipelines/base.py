from abc import ABC
from core.chain import create_chain
from langchain_core.output_parsers import StrOutputParser,JsonOutputParser


class BaseChainGenerator(ABC):
    """
    Abstract base class for creating different types of chains with common methods.
    """

    def __init__(self, query_template: str, output_parser=JsonOutputParser()):
        """
        Initialize the base chain generator with a query template.

        Args:
            query_template (str): A prompt template for generating output.
        """

        self.query_template = query_template
        self.output_parser = output_parser
        self.chain = None

    async def initialize_chain(self, input_vars):
        """
        Initialize the chain with the given input variables if it hasn't been initialized.
        """

        if not self.chain:
            self.chain = await create_chain(
                prompt_template=self.query_template,
                input_variables=input_vars,
                output_parser=self.output_parser,
            )
        return self.chain

    async def invoke_chain(self, input_data: dict):
        """
        Invoke the chain with provided input data.

        Args:
            input_data (dict): The input data to invoke the chain
        """

        await self.initialize_chain(list(input_data.keys()))
        return await self.chain.ainvoke(input_data)
