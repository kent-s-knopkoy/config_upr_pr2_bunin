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
    Проверка параметров для этапов 1–4.
    """

    if not args.package or len(args.package.strip()) == 0:
        error("Имя пакета не может быть пустым.")

    # Либо репо-url, либо репо-path (тестовый режим)
    if args.repo_url and args.repo_path:
        error("Укажите либо --repo-url, либо --repo-path, но не оба сразу.")

    if not args.repo_url and not args.repo_path:
        error("Необходимо указать --repo-url (реальный) или --repo-path (тестовый).")

    if args.repo_path:
        if not os.path.exists(args.repo_path):
            error(f"Файл тестового репозитория не найден: {args.repo_path}")

    allowed_modes = ["local", "remote", "mirror", "test"]
    if args.repo_mode not in allowed_modes:
        error(f"Некорректный режим репозитория. Разрешено: {allowed_modes}")

    # Проверка версии (для реального)
    if args.repo_url:
        if not args.version:
            error("Для реального репозитория необходимо указать --version.")
        parts = args.version.split(".")
        if len(parts) < 2:
            error("Версия должна быть в формате X.Y или X.Y.Z.")

    if not args.output_file.endswith((".png", ".jpg", ".svg")):
        error("Выходной файл должен быть формата .png/.jpg/.svg.")

    if args.max_depth < 1:
        error("Максимальная глубина анализа должна быть >= 1.")

    return True


def print_stage1(args):
    """
    Вывод всех параметров — Этап 1.
    """
    print("\n=== USER PARAMETERS ===")
    for key, value in vars(args).items():
        print(f"{key} = {value}")


# === Этап 3: построение графа ===

def build_graph_real_repo(args):
    """
    Реальный репозиторий Alpine.
    """
    print("\n[INFO] Режим: Реальный Alpine репозиторий")

    repo = ApkRepository(args.repo_url)
    print("[INFO] Загружаем APKINDEX.tar.gz...")

    try:
        repo.parse_index()
    except Exception as e:
        error(f"Не удалось обработать APKINDEX: {e}")

    print("[INFO] APKINDEX успешно загружен.")
    print(f"[INFO] Строим граф зависимостей для {args.package}:{args.version}")

    graph_builder = DependencyGraph(args.max_depth, args.filter)

    def get_deps(package_name: str, version: str | None):
        """
        Корень — используем точную версию.
        Остальные узлы — берём любую доступную версию.
        """
        if version is not None:
            return repo.get_dependencies(package_name, version)

        if package_name in repo.packages:
            versions = list(repo.packages[package_name].keys())
            if versions:
                any_version = versions[-1]
                return repo.get_dependencies(package_name, any_version)

        return []

    graph = graph_builder.build(args.package, args.version, get_deps)

    # Еcли пользователь запросил обратные зависимости — Этап 4
    if args.reverse:
        print("\n=== REVERSE DEPENDENCIES (REAL REPO) ===")
        rev = graph_builder.find_reverse_dependencies(args.package)
        if not rev:
            print("(нет)")
        else:
            for r in rev:
                print(r)
        return

    print("\n=== DEPENDENCY GRAPH (REAL REPO) ===")
    if args.ascii:
        graph_builder.print_ascii(args.package)
    else:
        for pkg, deps in graph.items():
            deps_str = ", ".join(deps) if deps else "(нет)"
            print(f"{pkg}: {deps_str}")


def build_graph_test_repo(args):
    """
    Тестовый режим (из файла test_repo.txt).
    """
    print("\n[INFO] Режим: Тестовый репозиторий (файл)")

    repo = TestRepository(args.repo_path)

    graph_builder = DependencyGraph(args.max_depth, args.filter)

    def get_deps(package_name: str, version: str | None):
        return repo.get_dependencies(package_name)

    graph = graph_builder.build(args.package, args.version, get_deps)

    # Этап 4 — обратные зависимости
    if args.reverse:
        print("\n=== REVERSE DEPENDENCIES (TEST REPO) ===")
        rev = graph_builder.find_reverse_dependencies(args.package)
        if not rev:
            print("(нет пакетов, зависящих от данного)")
        else:
            for r in rev:
                print(r)
        return

    print("\n=== DEPENDENCY GRAPH (TEST REPO) ===")
    if args.ascii:
        graph_builder.print_ascii(args.package)
    else:
        for pkg, deps in graph.items():
            deps_str = ", ".join(deps) if deps else "(нет зависимостей)"
            print(f"{pkg}: {deps_str}")


def main():
    parser = argparse.ArgumentParser(
        description="Dependency Graph Visualizer – этапы 1–4"
    )

    parser.add_argument("--package", required=True, help="Имя пакета")
    parser.add_argument("--repo-url", help="URL Alpine репозитория")
    parser.add_argument("--repo-path", help="Путь к тестовому репозиторию (файл)")
    parser.add_argument("--repo-mode", default="local",
                        help="Режим: local/remote/mirror/test")
    parser.add_argument("--version", help="Версия пакета (для реального репо)")
    parser.add_argument("--output-file", default="graph.png",
                        help="Файл для изображения графа")
    parser.add_argument("--ascii", action="store_true",
                        help="Вывод в ASCII-дереве")
    parser.add_argument("--max-depth", type=int, default=3,
                        help="Максимальная глубина анализа")
    parser.add_argument("--filter",
                        help="Игнорировать пакеты, содержащие подстроку")
    parser.add_argument("--reverse", action="store_true",
                        help="Вывести обратные зависимости (Этап 4)")

    args = parser.parse_args()
    validate_args(args)

    # Этап 1: вывод параметров
    print_stage1(args)

    # Этап 2 + Этап 3 + Этап 4
    if args.repo_path:
        build_graph_test_repo(args)
    else:
        build_graph_real_repo(args)

    print("\n[INFO] Этап 4 завершён.")


if __name__ == "__main__":
    main()

#python3 src/cli.py --package C --version TEST --repo-path ./test_repo1.txt --reverse