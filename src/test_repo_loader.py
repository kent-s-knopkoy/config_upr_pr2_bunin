# src/test_repo_loader.py

class TestRepository:
    """
    Тестовый репозиторий.
    Формат файла:
        A:B C
        B:C D
        C:
        D:A

    Слева имя пакета, справа через пробел имена зависимостей.
    """

    def __init__(self, path: str):
        self.path = path
        self.packages: dict[str, list[str]] = {}
        self._load()

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if ":" not in line:
                        continue
                    name, deps_str = line.split(":", 1)
                    name = name.strip()
                    deps = deps_str.strip().split() if deps_str.strip() else []
                    self.packages[name] = deps
        except FileNotFoundError:
            raise RuntimeError(f"Файл тестового репозитория не найден: {self.path}")

    def get_dependencies(self, package: str) -> list[str]:
        if package not in self.packages:
            # в тестовом режиме лучше явно показывать ошибку
            raise ValueError(f"Пакет '{package}' не найден в тестовом репозитории")
        return self.packages[package]