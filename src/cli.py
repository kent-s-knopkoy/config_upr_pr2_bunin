import argparse
import os
import sys


def error(msg):
    print(f"[ERROR] {msg}")
    sys.exit(1)


def validate_args(args):
    #Имя пакета
    if not args.package or len(args.package.strip()) == 0:
        error("Имя пакета не может быть пустым.")

    #URL или путь к репозиторию
    if args.repo_url and args.repo_path:
        error("Укажите либо --repo-url, либо --repo-path, но не оба сразу.")

    if not args.repo_url and not args.repo_path:
        error("Необходимо указать хотя бы один источник: --repo-url или --repo-path.")

    #Если указали путь — он должен существовать
    if args.repo_path:
        if not os.path.exists(args.repo_path):
            error(f"Указанный путь не существует: {args.repo_path}")

    #Режим работы с тестовым репозиторием
    allowed_modes = ["local", "remote", "mirror", "test"]
    if args.repo_mode not in allowed_modes:
        error(f"Некорректный режим репозитория. Доступные варианты: {allowed_modes}")

    #Версия пакета
    #Допустимая версия должна быть вида X.Y.Z
    if args.version:
        parts = args.version.split(".")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            error("Версия должна быть в формате X.Y.Z, например 1.0.3")

    #Имя файла графа
    if not args.output_file.endswith((".png", ".jpg", ".svg")):
        error("Имя выходного файла должно иметь расширение .png, .jpg или .svg")

    #Максимальная глубина
    if args.max_depth < 1:
        error("Максимальная глубина должна быть >= 1")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Dependency graph visualizer — этап 1"
    )

    parser.add_argument("--package", required=True, help="Имя анализируемого пакета")
    parser.add_argument("--repo-url", help="URL репозитория")
    parser.add_argument("--repo-path", help="Путь к тестовому репозиторию")
    parser.add_argument("--repo-mode", default="local",
                        help="Режим работы с репозиторием (local, remote, mirror, test)")
    parser.add_argument("--version", help="Версия пакета (X.Y.Z)")
    parser.add_argument("--output-file", default="graph.png",
                        help="Имя файла для сохранения изображения графа")
    parser.add_argument("--ascii", action="store_true",
                        help="Вывод зависимостей в виде ASCII-дерева")
    parser.add_argument("--max-depth", type=int, default=3,
                        help="Максимальная глубина анализа зависимостей")
    parser.add_argument("--filter", help="Подстрока для фильтрации пакетов")

    args = parser.parse_args()

    #Проверяем параметры
    validate_args(args)

    #Выводим ключ-значение
    print("\n=== USER PARAMETERS ===")
    for key, value in vars(args).items():
        print(f"{key} = {value}")


if __name__ == "__main__":
    main()

# python3 src/cli.py --package numpy --repo-path ./test_repo --repo-mode local --version 1.0.0 --output-file graph.png --ascii --max-depth 3 --filter core