from .base import BaseChainGenerator


class LanguageTranslator(BaseChainGenerator):

    async def translate(self, resume_text):
        """
        Generate a translation
        """
        input_data = {"resume_text": resume_text}
        return await self.invoke_chain(input_data=input_data)
