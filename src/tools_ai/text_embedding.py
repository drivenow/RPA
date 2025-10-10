from FlagEmbedding import FlagModel, FlagReranker
import time

retrieve_model = None
# 初始化重排序模型
rerank_model = None


def setup_embedding_model(retrieve_model_flag=True, rerank_model_flag=True):
    global retrieve_model
    global rerank_model
    t1 = time.time()
    if retrieve_model_flag and not retrieve_model:
        retrieve_model = FlagModel("BAAI/BGE-M3",  # 'BAAI/bge-large-zh-
                                   query_instruction_for_retrieval="为这个句子生成表示以用于检索相关文章：",
                                   devices="cuda:0",
                                   use_fp16=True)
    if rerank_model_flag and not rerank_model:
        rerank_model = FlagReranker("BAAI/bge-reranker-v2-m3", use_fp16=True, devices="cuda:0")
        print("embedding model setup time:", time.time() - t1)
    return retrieve_model, rerank_model


if __name__ == '__main__':
    setup_embedding_model()

    sentences_1 = ["样例数据-1", "样例数据-2"]
    sentences_2 = ["样例数据-3", "样例数据-4"]
    embeddings_1 = retrieve_model.encode(sentences_1)
    embeddings_2 = retrieve_model.encode(sentences_2)
    similarity = embeddings_1 @ embeddings_2.T
    print(similarity)

    # for s2p(short query to long passage) retrieval task, suggest to use encode_queries() which will automatically add the instruction to each query
    # corpus in retrieval task can still use encode() or encode_corpus(), since they don't need instruction
    queries = ['query_1', 'query_2']
    passages = ["样例文档-1", "样例文档-2"]
    q_embeddings = retrieve_model.encode_queries(queries)
    p_embeddings = retrieve_model.encode(passages)
    scores = q_embeddings @ p_embeddings.T
