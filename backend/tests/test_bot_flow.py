from __future__ import annotations

from app.config import Settings
from app.services.ticket_service import TicketService
from bot import BotOrchestrator
from tests.fakes import (
    FakeAgentService,
    FakeAuditService,
    FakeCustomerRepository,
    FakeGroupRepository,
    FakeMessageRepository,
    FakeSettingService,
    FakeStatsService,
    FakeTelegramService,
    FakeTicketRepository,
)


def make_bot(privileged_agent=None):
    settings = Settings()
    group_repository = FakeGroupRepository()
    setting_service = FakeSettingService({"management_group_chat_id": -100999, "timezone": "Asia/Tashkent"})
    ticket_repo = FakeTicketRepository()
    message_repo = FakeMessageRepository()
    customer_repo = FakeCustomerRepository()
    ticket_service = TicketService(ticket_repo, message_repo, customer_repo, FakeAuditService())
    telegram_service = FakeTelegramService()
    bot = BotOrchestrator(
        settings=settings,
        group_repository=group_repository,
        setting_service=setting_service,
        agent_service=FakeAgentService(privileged_agent),
        ticket_service=ticket_service,
        stats_service=FakeStatsService(),
        telegram_service=telegram_service,
        audit_service=FakeAuditService(),
    )
    return bot, ticket_repo, telegram_service


async def test_command_auth_protection():
    bot, _, telegram = make_bot()
    update = {
        "update_id": 1,
        "message": {
            "message_id": 100,
            "date": 1_712_742_000,
            "text": "/stats",
            "chat": {"id": -100999, "type": "supergroup", "title": "Management"},
            "from": {"id": 555, "username": "outsider", "first_name": "Outsider"},
        },
    }
    seen = set()

    result = await bot.process_update(update, lambda update_id, update_hash: _claim_once(seen, update_id))

    assert result["status"] == "forbidden"
    assert "ruxsat" in telegram.sent_messages[-1]["text"]


async def test_non_agent_reply_does_not_close_ticket():
    bot, ticket_repo, _ = make_bot()
    seen = set()
    first = {
        "update_id": 1,
        "message": {
            "message_id": 10,
            "date": 1_712_742_000,
            "text": "Yordam kerak",
            "chat": {"id": -100100, "type": "supergroup", "title": "Support"},
            "from": {"id": 1001, "username": "customer1", "first_name": "Customer"},
        },
    }
    second = {
        "update_id": 2,
        "message": {
            "message_id": 11,
            "date": 1_712_742_120,
            "text": "Men ham qo'shilaman",
            "reply_to_message": {"message_id": 10},
            "chat": {"id": -100100, "type": "supergroup", "title": "Support"},
            "from": {"id": 1002, "username": "customer2", "first_name": "Customer2"},
        },
    }

    await bot.process_update(first, lambda update_id, update_hash: _claim_once(seen, update_id))
    await bot.process_update(second, lambda update_id, update_hash: _claim_once(seen, update_id))

    assert len(ticket_repo.tickets) == 2
    assert all(ticket["status"] == "open" for ticket in ticket_repo.tickets.values())


async def test_duplicate_update_idempotency():
    bot, ticket_repo, _ = make_bot()
    seen = set()
    update = {
        "update_id": 5,
        "message": {
            "message_id": 10,
            "date": 1_712_742_000,
            "text": "Takroriy update testi",
            "chat": {"id": -100100, "type": "supergroup", "title": "Support"},
            "from": {"id": 1001, "username": "customer1", "first_name": "Customer"},
        },
    }

    first = await bot.process_update(update, lambda update_id, update_hash: _claim_once(seen, update_id))
    second = await bot.process_update(update, lambda update_id, update_hash: _claim_once(seen, update_id))

    assert first["status"] == "ticket_recorded"
    assert second["status"] == "duplicate"
    assert len(ticket_repo.tickets) == 1


def _claim_once(seen: set[int], update_id: int) -> bool:
    if update_id in seen:
        return False
    seen.add(update_id)
    return True
