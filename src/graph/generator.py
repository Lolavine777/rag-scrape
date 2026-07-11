import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from src.config import settings
from .state import AgentState

logger = logging.getLogger(__name__)

def generate_answer(state: AgentState) -> dict:
    question = state.get("question")
    context = state.get("retrieved_context", "") or "Không có ngữ cảnh bổ sung được cung cấp."
    
    logger.info("Generating final answer for question: %s", question)
    
    llm = ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.gemini_api_key,
        temperature=0.7
    )
    
    prompt = (
        "Bạn là một trợ lý AI thông minh chuyên cào thông tin và trả lời câu hỏi bằng tiếng Việt.\n"
        "Hãy trả lời câu hỏi của người dùng dựa vào ngữ cảnh (context) được cung cấp dưới đây.\n"
        "Nếu ngữ cảnh không có thông tin liên quan, hãy trả lời dựa trên hiểu biết của bạn nhưng ghi rõ không tìm thấy trong dữ liệu cào được.\n\n"
        f"Câu hỏi: {question}\n\n"
        f"Ngữ cảnh (Context):\n{context}\n\n"
        "Trả lời bằng tiếng Việt lịch sự, chi tiết:"
    )
    
    try:
        response = llm.invoke(prompt)
        answer = response.content
        logger.info("Answer generated successfully.")
        return {"answer": answer}
    except Exception as e:
        logger.error("Error in generator node: %s", e)
        return {"answer": f"Đã xảy ra lỗi khi tạo câu trả lời: {str(e)}"}
