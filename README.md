depviz — Dependency Visualizer (minimal prototype)

Коротко:

Проект реализует CLI-инструмент для получения зависимостей пакетов Alpine Linux:
в тестовом режиме — из текстового файла,
в реальном режиме — из APKINDEX репозитория Alpine.
Поддерживается построение графа зависимостей (BFS), вывод обратных зависимостей, ASCII-дерева и генерация Graphviz DOT-описания.

Запуск:

Этап 1 - python3 src/cli.py --package numpy --repo-path ./test_repo --repo-mode local --version 1.0.0 --output-file graph.png --ascii --max-depth 3 --filter core
Этап 2 - python3 src/cli.py --package bash --version 5.2.21-r0 --repo-url https://dl-cdn.alpinelinux.org/alpine/edge/community/x86_64 --output-file graph.png --max-depth 3
Этап 3 - python3 src/cli.py --package bash --version 5.2.21-r0 --repo-url https://dl-cdn.alpinelinux.org/alpine/edge/community/x86_64 --max-depth 2 --ascii --output-file graph.png
Этап 4 - python3 src/cli.py --package C --version TEST --repo-path ./test_repo1.txt --reverse
Этап 5 - python3 src/cli.py --package A --version TEST --repo-path ./test_repo.txt --max-depth 4 --ascii --output-file graph_test.png

Структура:

src/cli.py              — CLI и основной сценарий
src/apk_parser.py       — загрузка и парсинг APKINDEX
src/dependency_graph.py — построение графа, BFS, обратные зависимости, DOT
src/test_repo_loader.py — чтение тестового репозитория

Примечания:

Для реального анализа необходимо указать URL репозитория Alpine.
В тестовом режиме зависимости берутся из файла формата A:B C.
Инструмент не использует apk-tools и сторонние библиотеки для получения зависимостей.

