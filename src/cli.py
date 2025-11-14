import argparse
import os
import sys

from apk_parser import ApkRepository


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
        error("Для Этапа 2 требуется --repo-url")

    #Если есть repo-path — должна существовать папка
    if args.repo_path:
        if not os.path.exists(args.repo_path):
            error(f"Указанный путь не существует: {args.repo_path}")

    #Режим
    allowed_modes = ["local", "remote", "mirror", "test"]
    if args.repo_mode not in allowed_modes:
        error(f"Некорректный режим репозитория. Разрешено: {allowed_modes}")

    #Проверка версии
    if args.version:
        parts = args.version.split(".")
        if len(parts) < 2:
            error("Версия должна быть в формате X.Y или X.Y.Z")

    #Проверка имени файла
    if not args.output_file.endswith((".png", ".jpg", ".svg")):
        error("Имя выходного файла должно быть .png/.jpg/.svg")

    #Глубина анализа
    if args.max_depth < 1:
        error("Максимальная глубина анализа должна быть >= 1")

    return True


def print_stage1(args):
    print("\n=== USER PARAMETERS ===")
    for key, value in vars(args).items():
        print(f"{key} = {value}")


def stage2_collect_dependencies(args):
    if not args.repo_url:
        error("Для Этапа 2 необходимо указать --repo-url (URL репозитория Alpine).")

    print("[INFO] Загружаем APKINDEX.tar.gz ...")
    repo = ApkRepository(args.repo_url)

    try:
        repo.parse_index()
    except Exception as e:
        error(f"Ошибка при загрузке или разборе APKINDEX: {e}")

    print("[INFO] APKINDEX успешно обработан.")
    print(f"[INFO] Ищем пакет '{args.package}' версии '{args.version}'...")

    try:
        deps = repo.get_dependencies(args.package, args.version)
    except Exception as e:
        error(str(e))

    print("\n=== DIRECT DEPENDENCIES ===")
    if deps:
        for d in deps:
            print(d)
    else:
        print("(нет зависимостей)")

    print("\n[INFO] Этап 2 успешно завершён.")


def main():
    parser = argparse.ArgumentParser(
        description="Dependency graph visualizer — этапы 1-2"
    )

    parser.add_argument("--package", required=True, help="Имя анализируемого пакета")
    parser.add_argument("--repo-url", help="URL репозитория Alpine")
    parser.add_argument("--repo-path", help="Путь к тестовому репозиторию (этап 1)")
    parser.add_argument("--repo-mode", default="local",
                        help="Режим репозитория: local, remote, mirror, test")
    parser.add_argument("--version", required=True,
                        help="Версия пакета, например 1.2.3-r0")
    parser.add_argument("--output-file", default="graph.png",
                        help="Файл для сохранения графа")
    parser.add_argument("--ascii", action="store_true",
                        help="Вывод ASCII-дерева")
    parser.add_argument("--max-depth", type=int, default=3,
                        help="Максимальная глубина анализа зависимостей")
    parser.add_argument("--filter", help="Подстрока для фильтрации пакетов")

    args = parser.parse_args()
    validate_args(args)

    print_stage1(args)

    stage2_collect_dependencies(args)


if __name__ == "__main__":
    main()

#python3 src/cli.py --package bash --version 5.2.21-r0 --repo-url https://dl-cdn.alpinelinux.org/alpine/edge/community/x86_64 --output-file graph.png --max-depth 3