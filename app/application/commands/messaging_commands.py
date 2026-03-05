from app.application.commands.base import Command


class SendMessageCommand(Command):
    async def execute(self, services: dict) -> dict:
        inbox = services["inbox"]
        message = await inbox.queue_outbound_message(
            self.user_id,
            self.payload["conversation_id"],
            self.payload["text"],
            self.payload.get("attachments", []),
            self.payload.get("send_as_ai", False),
        )
        return {"result": "completed", "message": message}


class SummarizeCommand(Command):
    async def execute(self, services: dict) -> dict:
        agent = services["agent"]
        summary = await agent.conversation_summary(self.user_id, self.payload["conversation_id"])
        return {"result": "completed", "summary": summary.model_dump()}


class ScheduleReplyCommand(Command):
    async def execute(self, services: dict) -> dict:
        queue = services["queue"]
        job_id = await queue.enqueue(
            "send_message",
            {
                "message_id": self.payload["message_id"],
                "scheduled_at": self.payload.get("scheduled_at"),
            },
        )
        return {"result": "queued", "job_id": job_id}

