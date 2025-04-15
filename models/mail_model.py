import datetime

class MailModel:
    def __init__(self, date, subject, body, sender, to, has_attachments):
        self.date = date
        self.subject = subject
        self.body = body
        self.sender = sender
        self.to = to
        self.has_attachments = has_attachments

    def to_dict(self):
        return {
            "date": self.date.isoformat(),
            "subject": self.subject,
            "body": self.body,
            "sender": self.sender,
            "to": self.to,
            "has_attachments": self.has_attachments
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            date=datetime.datetime.fromisoformat(data["date"]),
            subject=data["subject"],
            body=data["body"],
            sender=data["sender"],
            to=data["to"],
            has_attachments=data["has_attachments"]
        )
