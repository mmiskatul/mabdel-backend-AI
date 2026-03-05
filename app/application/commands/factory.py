from app.application.commands.base import Command
from app.application.commands.invoice_commands import (
    InvoiceCancelCommand,
    InvoiceChangeAmountCommand,
    InvoiceSetDueDateCommand,
)
from app.application.commands.messaging_commands import ScheduleReplyCommand, SendMessageCommand, SummarizeCommand


class CommandFactory:
    def create(self, command_type: str, user_id: str, payload: dict) -> Command:
        mapping = {
            "SEND_MESSAGE": SendMessageCommand,
            "SUMMARIZE": SummarizeCommand,
            "INVOICE_CANCEL": InvoiceCancelCommand,
            "INVOICE_CHANGE_AMOUNT": InvoiceChangeAmountCommand,
            "INVOICE_SET_DUE_DATE": InvoiceSetDueDateCommand,
            "SCHEDULE_REPLY": ScheduleReplyCommand,
        }
        if command_type not in mapping:
            raise ValueError(f"Unsupported command_type: {command_type}")
        return mapping[command_type](user_id, payload)

