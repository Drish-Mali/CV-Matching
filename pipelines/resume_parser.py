from .base import BaseChainGenerator

class ResumeParser(BaseChainGenerator):
  

    async def parser(self, resume_text, resume_schema):
        
        input_data = {"resume_text": resume_text, "resume_schema": resume_schema}
        return await self.invoke_chain(input_data=input_data)
