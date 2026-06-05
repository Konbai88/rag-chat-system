from evaluation.evaluation_data import qa_dataset
from retrieval.retrieval_service import RetrievalService
from services.knowlege_base import KnowledgeBaseService


def run_evaluation() -> None:
    """运行检索评估：计算 Hit Rate"""
    total = len(qa_dataset)
    hit_count = 0
    rag = RetrievalService(knowledge_base=KnowledgeBaseService(kb_id="python"))

    for qa in qa_dataset:
        question = qa["question"]
        expected_section = qa["source_section"]
        docs = rag.retrieve_and_rerank(question)
        retrieved_sections = [doc.metadata["page"] for doc in docs]
        print("question:", question)
        print("expected:", expected_section)
        print("retrieved:", retrieved_sections)
        if expected_section in retrieved_sections:
            hit_count += 1
            print("result: HIT")
        else:
            print("result: MISS")
        print("=" * 50)

    hit_rate = hit_count / total
    print("total:", total)
    print("hit:", hit_count)
    print("hit rate:", hit_rate)
    print("=" * 50)


if __name__ == "__main__":
    run_evaluation()
