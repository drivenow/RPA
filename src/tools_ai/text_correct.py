from transformers import AutoModelForCausalLM, AutoTokenizer,set_seed
set_seed(42)

model_name = "twnlp/ChineseErrorCorrector2-7B-AWQ"

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="auto",
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained(model_name, padding_side='left')

prompt = "你是一个文本纠错专家，纠正输入句子中的语法错误，添加标点符号，并输出正确的句子，输入句子为："
text_input = "少先队员因该为老人让坐。"
file6 = r"X:\RAG\rag_data\像素范\俞敏洪完胜罗永浩，什么是好老板和领头羊？有些东西不只是钱衡量.txt"

content = "".join(
    open(file6, "r", encoding="utf-8").readlines())
    
messages = [
    {"role": "user", "content": prompt + text_input}
]
text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True
)
model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

generated_ids = model.generate(
    **model_inputs,
    max_new_tokens=512
)
generated_ids = [
    output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
]

response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
print(response)
