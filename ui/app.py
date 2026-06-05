import streamlit as st
import uuid
from services.rag import RagService
from memory.file_history_store import get_history
from services.knowledge_base import KnowledgeBaseService
from pypdf import PdfReader
import docx
from io import BytesIO

kb_id = st.sidebar.text_input(
    "知识库ID",
    value="default"
)
# ====================== 页面配置 ======================
st.set_page_config(page_title="RAG 智能对话平台", layout="wide")
st.title("🧠 RAG 对话系统（文件知识库 + 记忆�?)

# ====================== 初始化会话状态（核心修改�?======================
if "kb_service" not in st.session_state:
    st.session_state.kb_service = {}

if kb_id not in st.session_state.kb_service:
    st.session_state.kb_service[kb_id] = KnowledgeBaseService(kb_id)

kb_service = st.session_state.kb_service[kb_id]

if "rags" not in st.session_state:
    st.session_state.rags = {}

if kb_id not in st.session_state.rags:
    st.session_state.rags[kb_id] = RagService(kb_service)

rag = st.session_state.rags[kb_id]

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

# ====================== 侧边�?======================
with st.sidebar:
    st.header("⚙️ 控制面板")
    st.caption(f"会话ID：{st.session_state.session_id[:16]}")

    if st.button("🆕 新建对话"):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

    if st.button("🗑�?清空本次历史"):
        get_history(st.session_state.session_id).clear()
        st.session_state.messages = []
        st.success("已清�?)

    if st.button("🧹 清空所有本地记�?):
        import os
        if os.path.exists("./chat_memory"):
            for f in os.listdir("./chat_memory"):
                os.remove(f"./chat_memory/{f}")
        st.success("已清空全部历�?)

    if st.button("🗑�?清空当前知识�?, type="primary"):
        with st.spinner("正在清空所有数�?.."):
            kb_service.clear_kb()
            st.success("�?当前知识库已完全清空�?)
            st.rerun()

    filename_to_del = st.text_input("输入要删除的文件名（含后缀�?)
    if st.button("�?删除该文�?):
        if not filename_to_del:
            st.warning("请输入要删除的文件名")
        else:
            with st.spinner(f"正在删除 {filename_to_del} ..."):
                kb_service.delete_file(filename_to_del)
                st.success(f"�?文件 {filename_to_del} 已删�?)
                st.rerun()

    if st.button("🔧 重建 ES 索引"):
        with st.spinner("正在重建索引，请勿关�?.."):
            kb_service.rebuild_es_index()
            st.success("�?ES 索引重建完成�?)
            st.rerun()

    st.divider()
    st.subheader("📁 知识库管�?)

    # 上传文件并持久化到session_state
    uploaded_file = st.file_uploader("上传 TXT / PDF / DOCX", type=["txt", "pdf", "docx"])
    if uploaded_file is not None:
        st.session_state.uploaded_file = uploaded_file
        st.success(f"已选择：{uploaded_file.name}")

        # 文件预览
        def get_file_preview(file_obj):
            file_name = file_obj.name
            content = ""
            if file_name.endswith(".txt"):
                content = file_obj.read().decode("utf-8", errors="ignore")
                file_obj.seek(0)
            elif file_name.endswith(".pdf"):
                reader = PdfReader(file_obj)
                for page in reader.pages:
                    page_text = page.extract_text() or ""
                    content += page_text + "\n\n"
                file_obj.seek(0)
            elif file_name.endswith(".docx"):
                doc = docx.Document(BytesIO(file_obj.read()))
                content = "\n".join([p.text for p in doc.paragraphs])
                file_obj.seek(0)
            return content.strip()

        preview_content = get_file_preview(uploaded_file)
        with st.expander("预览内容"):
            st.text(preview_content[:2000] + "..." if len(preview_content) > 2000 else preview_content)

    # 构建向量�?
    if st.button("🔁 构建向量�?):
        if "uploaded_file" not in st.session_state or st.session_state.uploaded_file is None:
            st.warning("请先上传文件")
        else:
            with st.spinner("解析文件、切分文本并入库..."):
                try:
                    # 用同一�?kb_service 实例上传文件
                    result_msg = kb_service.upload_file(st.session_state.uploaded_file)
                    
                    if result_msg == "ok,already.":
                        st.success("�?文件已成功入库，可开始对�?)
                    elif result_msg == "skip,completion.":
                        st.info("ℹ️ 该文件已存在于知识库，跳过重复入�?)
                    elif result_msg == "empty document":
                        st.error("�?文件内容为空，无法入�?)
                    else:
                        st.success(result_msg)
                    
                    del st.session_state.uploaded_file
                    st.rerun()
                except Exception as e:
                    st.error(f"入库失败：{str(e)}")

    st.divider()
    st.caption("�?上传文件 �?构建向量�?�?即可对话检�?)

# ====================== 聊天展示 ======================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "docs" in msg and msg["docs"]:
            with st.expander("📄 参考片�?, expanded=False):
                st.write(msg["docs"])

# ====================== 输入处理（核心修改） ======================
user_input = st.chat_input("输入问题...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    config = {"configurable": {"session_id": st.session_state.session_id}}

    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            try:
                # 标准调用：一次拿到答�?文档，只检索一�?
                res, docs = rag.chat(user_input, config=config)
                doc_show = "\n---\n".join([d.page_content for d in docs[:3]])

                # 整理参考来�?
                sources = []
                for doc in docs:
                    source = f"{doc.metadata.get('filename', '未知文件')} 第{doc.metadata.get('page', '未知')}页| 相关度：{doc.metadata.get("score",0.00)}"
                    if source not in sources:
                        sources.append(source)

                final_res = res
                if sources:
                    final_res += "\n\n### 参考来源\n"
                    for source in sources:
                        final_res += f"- {source}\n"

                st.markdown(final_res)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": final_res,
                    "docs": doc_show
                })
            except Exception as e:
                err = f"错误：{str(e)}"
                st.error(err)
                st.session_state.messages.append({"role": "assistant", "content": err})
