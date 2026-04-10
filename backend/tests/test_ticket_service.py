from __future__ import annotations

from datetime import timedelta

from app.services.ticket_service import TicketService
from tests.fakes import (
    FakeAuditService,
    FakeCustomerRepository,
    FakeMessageRepository,
    FakeTicketRepository,
    make_context,
    utc_now,
)


def make_service():
    ticket_repo = FakeTicketRepository()
    message_repo = FakeMessageRepository()
    customer_repo = FakeCustomerRepository()
    audit = FakeAuditService()
    service = TicketService(ticket_repo, message_repo, customer_repo, audit)
    return service, ticket_repo, message_repo


async def test_ticket_creation():
    service, ticket_repo, _ = make_service()
    group = {"id": "group-1", "chat_id": -1001}
    runtime = {"response_merge_window_minutes": 30, "reopen_window_minutes": 60, "default_language": "uz"}
    ctx = make_context(
        update_id=1,
        chat_id=-1001,
        message_id=10,
        user_id=101,
        username="customer1",
        full_name="Customer One",
        text="Salom, yordam kerak",
    )

    ticket = await service.ingest_customer_message(group, ctx, runtime)

    assert ticket["status"] == "open"
    assert len(ticket_repo.tickets) == 1
    assert ticket["source_message_id"] == 10


async def test_ticket_append_to_existing_open():
    service, ticket_repo, message_repo = make_service()
    group = {"id": "group-1", "chat_id": -1001}
    runtime = {"response_merge_window_minutes": 30, "reopen_window_minutes": 60, "default_language": "uz"}
    first = make_context(
        update_id=1,
        chat_id=-1001,
        message_id=10,
        user_id=101,
        username="customer1",
        full_name="Customer One",
        text="Salom",
        created_at=utc_now(),
    )
    second = make_context(
        update_id=2,
        chat_id=-1001,
        message_id=11,
        user_id=101,
        username="customer1",
        full_name="Customer One",
        text="Yana yozdim",
        created_at=utc_now() + timedelta(minutes=5),
    )

    first_ticket = await service.ingest_customer_message(group, first, runtime)
    second_ticket = await service.ingest_customer_message(group, second, runtime)

    assert first_ticket["id"] == second_ticket["id"]
    assert len(ticket_repo.tickets) == 1
    assert len(message_repo.messages) == 2


async def test_agent_reply_closes_ticket():
    service, ticket_repo, message_repo = make_service()
    group = {"id": "group-1", "chat_id": -1001}
    runtime = {"response_merge_window_minutes": 30, "reopen_window_minutes": 60, "default_language": "uz"}
    customer_ctx = make_context(
        update_id=1,
        chat_id=-1001,
        message_id=10,
        user_id=101,
        username="customer1",
        full_name="Customer One",
        text="Savol bor",
    )
    ticket = await service.ingest_customer_message(group, customer_ctx, runtime)
    agent_ctx = make_context(
        update_id=2,
        chat_id=-1001,
        message_id=20,
        user_id=202,
        username="agent1",
        full_name="Agent One",
        text="Javob berdim",
        reply_to_message_id=10,
        created_at=utc_now() + timedelta(minutes=2),
    )
    agent = {"id": "agent-1"}

    closed = await service.ingest_agent_message(group, agent, agent_ctx)

    assert closed["status"] == "closed"
    assert closed["closed_by_agent_id"] == "agent-1"
    assert closed["first_response_seconds"] == 120

