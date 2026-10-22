from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from documents.models import Document
from .models import ChatSession, ChatMessage
from rag.pipeline import rag_pipeline


@login_required
def chat_view(request):
    session_id = request.POST.get("session_id") or request.GET.get("session_id")
    chat_session = None

    if session_id:
        chat_session = get_object_or_404(
            ChatSession,
            id=session_id,
            user=request.user,
        )

    documents = Document.objects.filter(
        uploaded_by=request.user,
        status=Document.Status.PROCESSED,
    ).order_by("-uploaded_at")

    if request.method == "POST":
        question = request.POST.get("question", "").strip()

        if not question:
            return redirect("chat")

        if len(question) > 2000:
            return render(
                request,
                "chat/chat.html",
                {
                    "documents": documents,
                    "chat_session": chat_session,
                    "messages": (
                        chat_session.messages.order_by("created_at")
                        if chat_session else []
                    ),
                    "error": "Question must be 2000 characters or fewer.",
                },
            )

        if chat_session is None:
            chat_session = ChatSession.objects.create(
                user=request.user,
                title=question[:200],
            )

        ChatMessage.objects.create(
            session=chat_session,
            role="user",
            content=question,
        )

        try:
            result = rag_pipeline.ask_question(
                question=question,
                document_ids=list(documents.values_list("id", flat=True)),
            )
            answer = result["answer"]
            sources = result.get("sources", [])

        except Exception:
            answer = (
                "Sorry, answer generate nahi ho paya. "
                "Please dobara try karein."
            )
            sources = []

        ChatMessage.objects.create(
            session=chat_session,
            role="assistant",
            content=answer,
            sources=sources,
        )

        chat_session.updated_at = timezone.now()
        chat_session.save(update_fields=["updated_at"])

        return redirect("chat",) if False else redirect(
            f"/chat/?session_id={chat_session.id}"
        )

    messages = (
        chat_session.messages.order_by("created_at")
        if chat_session else []
    )

    return render(
        request,
        "chat/chat.html",
        {
            "documents": documents,
            "chat_session": chat_session,
            "messages": messages,
        },
    )


@login_required
def chat_history(request):
    chat_sessions = ChatSession.objects.filter(
        user=request.user
    ).order_by("-updated_at")

    return render(
        request,
        "chat/chat_history.html",
        {"chat_sessions": chat_sessions},
    )

# Delete a chat conversation
@login_required
def delete_chat(request, session_id):
    # Allow deletion only through POST
    if request.method == "POST":
        # Find the chat owned by the logged-in user
        chat_session = get_object_or_404(
            ChatSession, id=session_id, user=request.user
        )

        # Delete the chat and its related messages
        chat_session.delete()

    # Return to chat history
    return redirect("chat_history")
