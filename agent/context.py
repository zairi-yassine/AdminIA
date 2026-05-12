from datetime import datetime


class ContextManager:

    def __init__(self):
        self.collected_info: dict[str, str] = {}
        self.history: list[dict] = []
        self.procedure_id: str | None = None
        self.started_at: str = datetime.now().isoformat()

    def add_message(self, role: str, content: str):
        self.history.append({
            "role":      role,
            "content":   content,
            "timestamp": datetime.now().isoformat(),
        })

    def update_info(self, key: str, value: str):
        self.collected_info[key] = value

    def get_history_for_llm(self) -> list[dict]:
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in self.history
        ]

    def get_collected_info(self) -> str:
        if not self.collected_info:
            return "aucune information collectée"
        return ", ".join(f"{k}={v}" for k, v in self.collected_info.items())

    def summary(self) -> str:
        return (
            f"Procédure : {self.procedure_id or 'non définie'} | "
            f"Infos : {self.get_collected_info()} | "
            f"Messages : {len(self.history)}"
        )

    def reset(self):
        self.__init__()
