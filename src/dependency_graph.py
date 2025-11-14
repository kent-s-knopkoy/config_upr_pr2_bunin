# src/dependency_graph.py

class DependencyGraph:
    """
    Хранит граф зависимостей и умеет его строить и печатать.
    Формат графа: { "pkg": ["dep1", "dep2", ...], ... }
    """

    def __init__(self, max_depth: int, filter_substring: str | None = None):
        self.max_depth = max_depth
        self.filter_substring = (
            filter_substring.lower() if filter_substring else None
        )
        self.graph: dict[str, list[str]] = {}

    def _should_skip(self, name: str) -> bool:
        """
        Возвращает True, если пакет надо игнорировать по фильтру.
        Пакет с таким именем не будет анализироваться глубже,
        но его можно оставить как "лист" у родителя.
        """
        if not self.filter_substring:
            return False
        return self.filter_substring in name.lower()

    def build(self, root_pkg: str, version: str | None, get_deps_func):
        """
        Строит граф зависимостей алгоритмом BFS с рекурсией.

        get_deps_func(package_name: str, version: str | None) -> list[str]
        """
        visited: set[str] = set()
        queue: list[tuple[str, int]] = [(root_pkg, 0)]

        # чтобы корень точно появился в графе
        if root_pkg not in self.graph:
            self.graph[root_pkg] = []

        def bfs_recursive(q: list[tuple[str, int]]):
            if not q:
                return

            pkg, depth = q.pop(0)  # "очередь" для BFS

            # не выходим за максимальную глубину
            if depth >= self.max_depth:
                return

            # чтобы не зациклиться
            if pkg in visited:
                return
            visited.add(pkg)

            # фильтр по подстроке: не анализируем глубже
            if self._should_skip(pkg):
                # но всё равно оставим в графе как "лист"
                if pkg not in self.graph:
                    self.graph[pkg] = []
                return

            try:
                deps = get_deps_func(pkg, version if depth == 0 else None)
            except Exception:
                deps = []

            # сохраняем зависимости в графе
            cleaned_deps: list[str] = []
            for d in deps:
                # не добавляем в граф те имена, которые сразу отфильтровали
                cleaned_deps.append(d)

            self.graph[pkg] = cleaned_deps

            # добавляем зависимости в очередь, если ещё не достигли глубины
            next_depth = depth + 1
            if next_depth < self.max_depth:
                for dep in cleaned_deps:
                    if dep not in visited:
                        q.append((dep, next_depth))

            # продолжаем BFS рекурсивно
            bfs_recursive(q)

        bfs_recursive(queue)
        return self.graph

    # ===== Вывод графа в виде ASCII-дерева =====

    def print_ascii(self, root_pkg: str):
        """
        Печатает граф в виде дерева с пометкой циклов.
        """

        def dfs(node: str, prefix: str, is_last: bool, path: set[str]):
            cycle = node in path

            # формируем строку для текущего узла
            line = ""
            if prefix:
                line += prefix
                line += "└── " if is_last else "├── "
            line += node
            if cycle:
                line += " (cycle)"

            print(line)

            if cycle:
                # дальше по циклу не идём
                return

            children = self.graph.get(node, [])
            if not children:
                return

            path.add(node)

            for index, child in enumerate(children):
                last_child = index == len(children) - 1
                # формируем новый префикс для потомков
                new_prefix = prefix
                if prefix:
                    new_prefix += "    " if is_last else "│   "
                dfs(child, new_prefix, last_child, path)

            path.remove(node)

        # корень рисуем отдельно (без префикса)
        print(root_pkg)
        children = self.graph.get(root_pkg, [])
        for idx, child in enumerate(children):
            last = idx == len(children) - 1
            dfs(child, "", last, set([root_pkg]))

    def find_reverse_dependencies(self, target: str) -> list[str]:
        """
        Возвращает список пакетов, которые зависят (транзитивно) от target.
        Используем BFS с рекурсией.
        """

        reverse_graph = {}  # ключ: пакет → список тех, кто от него зависит

        # строим обратную таблицу зависимостей
        for pkg, deps in self.graph.items():
            for d in deps:
                reverse_graph.setdefault(d, []).append(pkg)

        result = []
        visited = set()
        queue = [target]

        def bfs():
            if not queue:
                return

            cur = queue.pop(0)
            visited.add(cur)

            if cur in reverse_graph:
                for parent in reverse_graph[cur]:
                    if parent not in visited:
                        result.append(parent)
                        queue.append(parent)

            bfs()

        bfs()
        return result