# Анализ зависимостей Alpine, графы, визуализация, CLI.

Программа представляет собой CLI-инструмент, который получает зависимости пакетов Alpine Linux из реального репозитория или тестового файла, парсит их, строит граф зависимостей алгоритмом BFS с учётом глубины и фильтрации, обрабатывает циклы, показывает прямые и обратные зависимости, умеет выводить дерево зависимостей в ASCII-виде, формирует Graphviz DOT-описание и при наличии Graphviz сохраняет граф в PNG.

# Запуск:

Этап 1
```
python3 src/cli.py --package numpy --repo-path ./test_repo --repo-mode local --version 1.0.0 --output-file graph.png --ascii --max-depth 3 --filter core
```

Этап 2
```
python3 src/cli.py --package bash --version 5.2.21-r0 --repo-url https://dl-cdn.alpinelinux.org/alpine/edge/community/x86_64 --output-file graph.png --max-depth 3
```
Этап 3
```
python3 src/cli.py --package bash --version 5.2.21-r0 --repo-url https://dl-cdn.alpinelinux.org/alpine/edge/community/x86_64 --max-depth 2 --ascii --output-file graph.png
```
Этап 4
```
python3 src/cli.py --package C --version TEST --repo-path ./test_repo1.txt --reverse
```
Этап 5 
```
python3 src/cli.py --package A --version TEST --repo-path ./test_repo.txt --max-depth 4 --ascii --output-file graph_test.png
```

# Структура проекта:
```
src/cli.py              — CLI и основной сценарий
src/apk_parser.py       — загрузка и парсинг APKINDEX
src/dependency_graph.py — построение графа, BFS, обратные зависимости, DOT
src/test_repo_loader.py — чтение тестового репозитория
```
# Пример

У нас есть ссылка
```
https://dl-cdn.alpinelinux.org/alpine/edge/main/x86_64
```
В ней мы хотим найти bash --version 5.3.3-r1, вводим опредленные параметры для поиска, на выходе получаем два файла Dot и png
```
digraph dependencies {
    rankdir=LR;
    node [shape=box, fontsize=10];
    "bash" -> "/bin/sh";
    "/bin/sh";
    "bash" -> "so:libc.musl-x86_64.so.1";
    "so:libc.musl-x86_64.so.1";
    "bash" -> "so:libreadline.so.8";
    "so:libreadline.so.8";
}
```
<img width="289" height="203" alt="graph" src="https://github.com/user-attachments/assets/284ceb8f-8055-4ddd-9694-ef58cbc8b963" />



