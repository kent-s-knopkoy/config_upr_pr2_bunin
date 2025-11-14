# src/cli.py

import argparse
import os
import sys
import subprocess
from pathlib import Path

from apk_parser import ApkRepository
from dependency_graph import DependencyGraph
from test_repo_loader import TestRepository


def error(msg: str):
    print(f"[ERROR] {msg}")
    sys.exit(1)


def validate_args(args):
    """
    Проверка параметров для этапов 1–5.
    """

    if not args.package or len(args.package.strip()) == 0:
        error("Имя пакета не может быть пустым.")

    # Либо repo-url, либо repo-path (тестовый режим)
    if args.repo_url and args.repo_path:
        error("Укажите либо --repo-url, либо --repo-path, но не оба сразу.")

    if not args.repo_url and not args.repo_path:
        error("Необходимо указать --repo-url (реальный) или --repo-path (тестовый).")

    # тестовый репозиторий — это файл
    if args.repo_path:
        if not os.path.exists(args.repo_path):
            error(f"Файл тестового репозитория не найден: {args.repo_path}")

    allowed_modes = ["local", "remote", "mirror", "test"]
    if args.repo_mode not in allowed_modes:
        error(f"Некорректный режим репозитория. Разрешено: {allowed_modes}")

    # Проверка версии (для реального репозитория)
    if args.repo_url:
        if not args.version:
            error("Для реального репозитория необходимо указать --version.")
        parts = args.version.split(".")
        if len(parts) < 2:
            error("Версия должна быть в формате X.Y или X.Y.Z.")

    # Имя файла для картинки
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


# === Вспомогательная функция для этапа 5 ===

def save_graph_image(dot_text: str, output_file: str):
    """
    Сохраняет DOT-файл и пытается сгенерировать PNG с помощью утилиты dot (Graphviz).
    Если dot не установлен, хотя бы оставляем .dot.
    """
    out_path = Path(output_file)
    dot_path = out_path.with_suffix(".dot")

    # сохраняем DOT
    with dot_path.open("w", encoding="utf-8") as f:
        f.write(dot_text)

    print(f"[INFO] DOT-файл сохранён: {dot_path}")

    # пробуем запустить Graphviz
    try:
        subprocess.run(
            ["dot", "-Tpng", str(dot_path), "-o", str(out_path)],
            check=True
        )
        print(f"[INFO] PNG изображение сохранено: {out_path}")
    except FileNotFoundError:
        print("[WARN] Утилита 'dot' (Graphviz) не найдена. "
              "PNG не создан, используйте DOT-файл для визуализации.")
    except subprocess.CalledProcessError as e:
        print(f"[WARN] Ошибка при генерации PNG через dot: {e}")


# === Этапы 2–5: работа с реальным репозиторием ===

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
        Корневой пакет — используем точную версию.
        Внутренние узлы — берём любую доступную версию.
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

    # Этап 4: обратные зависимости
    if args.reverse:
        print("\n=== REVERSE DEPENDENCIES (REAL REPO) ===")
        rev = graph_builder.find_reverse_dependencies(args.package)
        if not rev:
            print("(нет пакетов, зависящих от данного)")
        else:
            for r in rev:
                print(r)
        # для отчёта по этапу 4 этого достаточно, PNG можно не строить
        return

    # Этап 3: вывод графа
    print("\n=== DEPENDENCY GRAPH (REAL REPO) ===")
    if args.ascii:
        graph_builder.print_ascii(args.package)
    else:
        for pkg, deps in graph.items():
            deps_str = ", ".join(deps) if deps else "(нет)"
            print(f"{pkg}: {deps_str}")

    # Этап 5: DOT + PNG
    dot_text = graph_builder.to_dot(args.package)
    save_graph_image(dot_text, args.output_file)


# === Этапы 3–5: тестовый репозиторий ===

def build_graph_test_repo(args):
    """
    Тестовый режим (из файла test_repo*.txt).
    """
    print("\n[INFO] Режим: Тестовый репозиторий (файл)")

    repo = TestRepository(args.repo_path)

    graph_builder = DependencyGraph(args.max_depth, args.filter)

    def get_deps(package_name: str, version: str | None):
        return repo.get_dependencies(package_name)

    graph = graph_builder.build(args.package, args.version, get_deps)

    # Этап 4: обратные зависимости
    if args.reverse:
        print("\n=== REVERSE DEPENDENCIES (TEST REPO) ===")
        rev = graph_builder.find_reverse_dependencies(args.package)
        if not rev:
            print("(нет пакетов, зависящих от данного)")
        else:
            for r in rev:
                print(r)
        # здесь тоже можно не строить PNG, но если хочешь — сними return
        return

    # Этап 3: прямой граф
    print("\n=== DEPENDENCY GRAPH (TEST REPO) ===")
    if args.ascii:
        graph_builder.print_ascii(args.package)
    else:
        for pkg, deps in graph.items():
            deps_str = ", ".join(deps) if deps else "(нет зависимостей)"
            print(f"{pkg}: {deps_str}")

    # Этап 5: DOT + PNG (можно показать красивую картинку даже для тестового графа)
    dot_text = graph_builder.to_dot(args.package)
    save_graph_image(dot_text, args.output_file)


def main():
    parser = argparse.ArgumentParser(
        description="Dependency Graph Visualizer – этапы 1–5"
    )

    parser.add_argument("--package", required=True, help="Имя пакета")
    parser.add_argument("--repo-url", help="URL Alpine репозитория")
    parser.add_argument("--repo-path", help="Путь к тестовому репозиторию (файл)")
    parser.add_argument("--repo-mode", default="local",
                        help="Режим: local/remote/mirror/test")
    parser.add_argument("--version", help="Версия пакета (для реального репо)")
    parser.add_argument("--output-file", default="graph.png",
                        help="Файл для изображения графа (PNG/JPG/SVG)")
    parser.add_argument("--ascii", action="store_true",
                        help="Вывод зависимостей в виде ASCII-дерева")
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

    # Этапы 2–5
    if args.repo_path:
        build_graph_test_repo(args)
    else:
        build_graph_real_repo(args)

    print("\n[INFO] Этап 5 завершён.")


if __name__ == "__main__":
    main()

#python3 src/cli.py --package A --version TEST --repo-path ./test_repo.txt --max-depth 4 --ascii --output-file graph_test.png