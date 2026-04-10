from __future__ import annotations

from app.services.auto_reply_service import AutoReplyService
from app.services.knowledge_service import KnowledgeService
from app.services.ticket_service import TicketService
from tests.fakes import (
    FakeAuditService,
    FakeCustomerRepository,
    FakeKnowledgeRepository,
    FakeMessageRepository,
    FakeSettingService,
    FakeStatsRepository,
    FakeTelegramService,
    FakeTicketRepository,
)


def make_auto_reply_service(entries=None):
    ticket_repo = FakeTicketRepository()
    message_repo = FakeMessageRepository()
    customer_repo = FakeCustomerRepository()
    audit = FakeAuditService()
    ticket_service = TicketService(ticket_repo, message_repo, customer_repo, audit)
    stats_repo = FakeStatsRepository()
    knowledge_repo = FakeKnowledgeRepository(entries or [])
    knowledge_service = KnowledgeService(
        knowledge_repo,
        "Assalomu alaykum. So'rovingiz qabul qilindi. Operator tez orada javob beradi.",
    )
    telegram_service = FakeTelegramService()
    settings_service = FakeSettingService()
    service = AutoReplyService(
        settings_service,
        stats_repo,
        knowledge_service,
        ticket_service,
        telegram_service,
        audit,
    )
    return service, ticket_repo, stats_repo, telegram_service


async def test_five_minute_auto_reply_logic():
    service, ticket_repo, stats_repo, telegram_service = make_auto_reply_service(
        [
            {
                "id": "kb-1",
                "title": "Yetkazib berish",
                "language": "uz",
                "category": "delivery",
                "answer_template": "Buyurtmangiz tez orada yetkaziladi.",
                "priority": 20,
                "is_active": True,
                "kb_terms": [
                    {"term_type": "keyword", "term_value": "yetkazib berish"},
                    {"term_type": "synonym", "term_value": "dostavka"},
                ],
            }
        ]
    )
    ticket = await ticket_repo.create_ticket(
        {
            "group_id": "group-1",
            "topic_id": None,
            "customer_id": "customer-1",
            "status": "open",
            "source_message_id": 10,
            "source_chat_id": -1001,
            "source_message_at": "2026-04-10T10:00:00+00:00",
            "last_customer_message_at": "2026-04-10T10:00:00+00:00",
            "latest_customer_message_id": 10,
            "latest_customer_message_text": "yetkazib berish qachon",
        }
    )
    stats_repo.stale_rows = [
        {
            "ticket_id": ticket["id"],
            "group_id": "group-1",
            "group_chat_id": -1001,
            "group_title": "Support Group",
            "topic_id": None,
            "customer_id": "customer-1",
            "customer_name": "Customer",
            "customer_username": "customer1",
            "latest_message_id": 10,
            "latest_message_text": "yetkazib berish qachon",
            "latest_message_normalized": "yetkazib berish qachon",
            "latest_message_created_at": "2026-04-10T10:00:00+00:00",
        }
    ]

    result = await service.run_due_auto_replies()

    assert result["processed"] == 1
    stored = ticket_repo.tickets[ticket["id"]]
    assert stored["status"] == "auto_replied"
    assert len(telegram_service.sent_messages) == 1


async def test_confidence_fallback_logic():
    service, _, _, _ = make_auto_reply_service([])
    preview = await service.simulate("mutlaqo noma'lum savol")

    assert preview["requires_escalation"] is True
    assert "qabul qilindi" in preview["answer_text"]
