import os
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.test import TestModel

os.environ['OPENAI_API_KEY'] = 'sk-CJpKFYcAMJYlKpn9721bD96f4aFc443b91D36aA0C2217a92'
os.environ['OPENAI_BASE_URL'] = 'https://api.ai-yyds.com/v1'
model_name = 'gpt-4o'
# os.environ['OPENAI_API_KEY'] = 'sk-CJpKFYcAMJYlKpn9721bD96f4aFc443b91D36aA0C2217a92'
# os.environ['OPENAI_BASE_URL'] = 'http://192.168.1.2:11434/v1'
# model_name = "qwen2.5:14b"

# os.environ['OPENAI_BASE_URL'] = "https://api.siliconflow.cn/v1"
# os.environ['OPENAI_API_KEY'] = "sk-kcprjafyronffotrpxxovupsxzqolveqkypbmubjsopdbxec"
# model_name = "Pro/deepseek-ai/DeepSeek-R1"
#
# os.environ['OPENAI_BASE_URL'] = "https://api.deepseek.com"
# os.environ['OPENAI_API_KEY'] = "sk-eb7b2844c60a4c88918a325417ac81f7"
# model_name = "deepseek-reasoner"  # "deepseek-chat"  #
#
# os.environ['OPENAI_API_KEY'] = 'sk-CJpKFYcAMJYlKpn9721bD96f4aFc443b91D36aA0C2217a92'
# os.environ['OPENAI_BASE_URL'] = 'http://192.168.1.2:11434/v1'
# model_name = 'llama3.1:8b'

model = OpenAIModel(model_name, base_url=os.environ['OPENAI_BASE_URL'],
                    api_key=os.environ['OPENAI_API_KEY'])
# model = TestModel()

# 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