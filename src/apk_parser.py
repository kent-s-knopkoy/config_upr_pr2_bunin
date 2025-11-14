import urllib.request
import tarfile
import io


class ApkRepository:
    def __init__(self, repo_url: str):
        self.repo_url = repo_url.rstrip("/")
        self.packages = {}  # { package: {version: [deps]} }

    def download_index(self):
        index_url = f"{self.repo_url}/APKINDEX.tar.gz"
        try:
            with urllib.request.urlopen(index_url) as response:
                return response.read()
        except Exception as e:
            raise RuntimeError(f"Не удалось скачать APKINDEX.tar.gz: {e}")

    def parse_index(self):
        data = self.download_index()

        #Распаковка tar.gz в память
        fileobj = io.BytesIO(data)
        with tarfile.open(fileobj=fileobj, mode="r:gz") as tar:
            member = tar.getmember("APKINDEX")
            raw = tar.extractfile(member).read().decode("utf-8")

        #Разбираем блоки пакетов
        current_pkg = {}
        for line in raw.splitlines():
            if line.startswith("P:"):  # имя
                current_pkg["name"] = line[2:]
            elif line.startswith("V:"):  # версия
                current_pkg["version"] = line[2:]
            elif line.startswith("D:"):  # зависимости
                deps = line[2:].split() if line[2:].strip() else []
                current_pkg["deps"] = deps
            elif line.strip() == "":
                #конец записи пакета
                if "name" in current_pkg and "version" in current_pkg:
                    name = current_pkg["name"]
                    version = current_pkg["version"]

                    if name not in self.packages:
                        self.packages[name] = {}

                    self.packages[name][version] = current_pkg.get("deps", [])

                current_pkg = {}

    def get_dependencies(self, package: str, version: str):
        if package not in self.packages:
            raise ValueError(f"Пакет '{package}' не найден")

        if version not in self.packages[package]:
            raise ValueError(f"Версия '{version}' для пакета '{package}' не найдена")

        return self.packages[package][version]