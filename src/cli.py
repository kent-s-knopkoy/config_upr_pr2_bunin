# src/cli.py

import argparse
import os
import sys

from apk_parser import ApkRepository
from dependency_graph import DependencyGraph
from test_repo_loader import TestRepository


def error(msg: str):
    print(f"[ERROR] {msg}")
    sys.exit(1)


def validate_args(args):
    """
    Проверка параметров, актуальная для этапов 1–3.
    """

    # имя пакета
    if not args.package or len(args.package.strip()) == 0:
        error("Имя пакета не может быть пустым.")

    # URL или путь к репозиторию: должны быть ИЛИ-ИЛИ
    if args.repo_url and args.repo_path:
        error("Укажите либо --repo-url, либо --repo-path, но не оба сразу.")

    if not args.repo_url and not args.repo_path:
        error("Необходимо указать --repo-url (реальный репозиторий) или --repo-path (тестовый).")

    # если указан локальный путь — он должен существовать
    if args.repo_path:
        if not os.path.exists(args.repo_path):
            error(f"Указанный путь не существует: {args.repo_path}")

    # режим работы
    allowed_modes = ["local", "remote", "mirror", "test"]
    if args.repo_mode not in allowed_modes:
        error(f"Некорректный режим репозитория. Разрешено: {allowed_modes}")

    # версия пакета (для реального режима)
    if args.repo_url:
        if not args.version:
            error("Для реального репозитория необходимо указать --version.")
        parts = args.version.split(".")
        if len(parts) < 2:
            error("Версия должна быть в формате X.Y или X.Y.Z, например 5.2.21-r0.")

    # имя файла с графом
    if not args.output_file.endswith((".png", ".jpg", ".svg")):
        error("Имя выходного файла должно иметь расширение .png, .jpg или .svg.")

    # глубина анализа
    if args.max_depth < 1:
        error("Максимальная глубина анализа должна быть >= 1.")

    return True


def print_stage1(args):
    """
    Вывод параметров (Этап 1 — конфигурация).
    """
    print("\n=== USER PARAMETERS ===")
    for key, value in vars(args).items():
        print(f"{key} = {value}")


# ===== Этап 3: построение графа зависимостей =====

def build_graph_real_repo(args):
    """
    Реальный режим: работаем с Alpine-репозиторием через ApkRepository.
    """
    print("\n[INFO] Режим: реальный репозиторий (Alpine APKINDEX)")
    print("[INFO] Загружаем APKINDEX.tar.gz ...")

    repo = ApkRepository(args.repo_url)

    try:
        repo.parse_index()
    except Exception as e:
        error(f"Ошибка при загрузке или разборе APKINDEX: {e}")

    print("[INFO] APKINDEX успешно обработан.")
    print(f"[INFO] Строим граф зависимостей для пакета '{args.package}' версии '{args.version}' ...")

    graph_builder = DependencyGraph(args.max_depth, args.filter)

    def get_deps(package_name: str, version: str | None):
        """
        Функция-обёртка для получения зависимостей из ApkRepository.

        На корне используем заданную пользователем версию,
        на внутренних узлах — пытаемся взять любую доступную версию,
        если точная не указана.
        """
        # для корня используем точную версию
        if version is not None:
            return repo.get_dependencies(package_name, version)

        # для остальных узлов — любая доступная версия (если есть)
        if package_name in repo.packages:
            versions = list(repo.packages[package_name].keys())
            if versions:
                any_version = versions[-1]  # возьмём "последнюю" как некоторую
                return repo.get_dependencies(package_name, any_version)

        # если ничего не нашли — зависимостей нет
        return []

    graph = graph_builder.build(args.package, args.version, get_deps)

    print("\n=== DEPENDENCY GRAPH (REAL REPO) ===")
    if args.ascii:
        graph_builder.print_ascii(args.package)
    else:
        for pkg, deps in graph.items():
            deps_str = ", ".join(deps) if deps else "(нет зависимостей)"
            print(f"{pkg}: {deps_str}")


def build_graph_test_repo(args):
    """
    Тестовый режим: читаем граф из текстового файла с большими латинскими буквами.
    """
    print("\n[INFO] Режим: тестовый репозиторий (из файла)")
    print(f"[INFO] Загружаем тестовый репозиторий из файла: {args.repo_path}")

    repo = TestRepository(args.repo_path)

    graph_builder = DependencyGraph(args.max_depth, args.filter)

    def get_deps(package_name: str, version: str | None):
        # версия в тестовом режиме не важна
        return repo.get_dependencies(package_name)

    graph = graph_builder.build(args.package, args.version, get_deps)

    print("\n=== DEPENDENCY GRAPH (TEST REPO) ===")
    if args.ascii:
        graph_builder.print_ascii(args.package)
    else:
        for pkg, deps in graph.items():
            deps_str = ", ".join(deps) if deps else "(нет зависимостей)"
            print(f"{pkg}: {deps_str}")


def main():
    parser = argparse.ArgumentParser(
        description="Dependency graph visualizer — этапы 1–3"
    )

    parser.add_argument("--package", required=True, help="Имя анализируемого пакета")
    parser.add_argument("--repo-url", help="URL репозитория Alpine")
    parser.add_argument("--repo-path", help="Путь к тестовому репозиторию (файл описания графа)")
    parser.add_argument("--repo-mode", default="local",
                        help="Режим репозитория: local, remote, mirror, test")
    parser.add_argument("--version",
                        help="Версия пакета, например 5.2.21-r0 (для реального репозитория)")
    parser.add_argument("--output-file", default="graph.png",
                        help="Файл для сохранения изображения графа (этапы 4–5)")
    parser.add_argument("--ascii", action="store_true",
                        help="Вывод зависимостей в виде ASCII-дерева")
    parser.add_argument("--max-depth", type=int, default=3,
                        help="Максимальная глубина анализа зависимостей")
    parser.add_argument("--filter",
                        help="Подстрока для фильтрации пакетов (игнорировать имена, содержащие её)")

    args = parser.parse_args()
    validate_args(args)

    # Этап 1: вывести все параметры конфигурации
    print_stage1(args)

    # Этап 3: строим граф
    if args.repo_path:
        # режим тестового репозитория
        build_graph_test_repo(args)
    else:
        # режим реального репозитория
        build_graph_real_repo(args)

    print("\n[INFO] Этап 3 успешно завершён.")


if __name__ == "__main__":
    main()

#python3 src/cli.py --package bash --version 5.2.21-r0 --repo-url https://dl-cdn.alpinelinux.org/alpine/edge/community/x86_64 --max-depth 2 --ascii --output-file graph.png