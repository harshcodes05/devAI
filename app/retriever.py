import json
from pathlib import Path


class CodeRetriever:
    def __init__(self, index_path: str):
        self.index_path = Path(index_path)

        if not self.index_path.exists():
            raise FileNotFoundError(
                f"Code index not found: {self.index_path}"
            )

        with self.index_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            self.units = json.load(file)

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict]:
        """
        Retrieve relevant code units using
        keyword matching plus code-aware ranking.
        """

        query_words = {
            word.lower()
            for word in query.split()
            if len(word) > 2
        }

        results = []

        for unit in self.units:

            path = unit["path"].lower()
            name = unit["name"].lower()
            unit_type = unit["type"].lower()
            source = unit["source"].lower()

            score = 0

            # --------------------------------
            # 1. Match in the actual code
            # --------------------------------
            for word in query_words:
                if word in source:
                    score += min(source.count(word), 5)

            # --------------------------------
            # 2. Match in function/class name
            # Stronger signal than raw code text
            # --------------------------------
            for word in query_words:
                if word in name:
                    score += 10

            # --------------------------------
            # 3. Prefer functions over classes
            # for implementation questions
            # --------------------------------
            if unit_type == "function":
                score += 5

            elif unit_type == "class":
                score += 1

            # --------------------------------
            # 4. Prefer application source code
            # over tests
            # --------------------------------
            if path.startswith("tests/"):
                score -= 5

            elif path.startswith("app/"):
                score += 5

            # --------------------------------
            # 5. Penalty for test helper code
            # that isn't under tests/
            # --------------------------------
            if "/test" in path and not path.startswith("tests/"):
                score -= 5

            # --------------------------------
            # Keep only actual matches
            # --------------------------------
            if score > 0:
                results.append(
                    {
                        "score": score,
                        **unit,
                    }
                )

        results.sort(
            key=lambda result: result["score"],
            reverse=True,
        )

        return results[:top_k]