import sqlite3
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple


class SQLiteIngredientIndexer:
    """
    Manages the inverted ingredient index in SQLite.
    Supports incremental chunk-based population, optimized schema,
    and fast candidate generation queries.
    """

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        # In-memory lookup cache: ingredient_name -> ingredient_id
        # Takes < 5 MB for ~50k unique ingredients, avoids thousands of SELECTs
        self._ingredient_id_cache: Dict[str, int] = {}
        self._next_ingredient_id: int = 1

    def connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.execute("PRAGMA journal_mode = WAL;")
            self._conn.execute("PRAGMA synchronous = NORMAL;")
            self._conn.execute("PRAGMA cache_size = -64000;")  # 64MB cache
            self._conn.execute("PRAGMA temp_store = MEMORY;")
        return self._conn

    def close(self):
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def init_schema(self, drop_existing: bool = False):
        """Initializes database tables and indexes."""
        conn = self.connect()
        with conn:
            if drop_existing:
                conn.execute("DROP TABLE IF EXISTS recipe_ingredients;")
                conn.execute("DROP TABLE IF EXISTS recipes_metadata;")
                conn.execute("DROP TABLE IF EXISTS ingredients;")

            conn.execute("""
                CREATE TABLE IF NOT EXISTS ingredients (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    recipe_count INTEGER DEFAULT 0
                );
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS recipes_metadata (
                    recipe_id INTEGER PRIMARY KEY,
                    ner_count INTEGER NOT NULL
                );
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS recipe_ingredients (
                    ingredient_id INTEGER NOT NULL,
                    recipe_id INTEGER NOT NULL,
                    PRIMARY KEY (ingredient_id, recipe_id)
                );
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_recipe_id
                ON recipe_ingredients (recipe_id);
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_ingredients_name
                ON ingredients (name);
            """)

        self._load_cache()

    def _load_cache(self):
        """Loads existing ingredients into in-memory cache."""
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("SELECT name, id FROM ingredients;")
        for name, ing_id in cur.fetchall():
            self._ingredient_id_cache[name] = ing_id
            if ing_id >= self._next_ingredient_id:
                self._next_ingredient_id = ing_id + 1

    def index_chunk(
        self,
        records: List[dict],
    ):
        """
        Incrementally indexes a chunk of validated recipe records.
        Each record must have: 'recipe_id', 'ner' (list of str), 'ner_count'.
        """
        if not records:
            return

        conn = self.connect()

        # Step 1: Identify all new ingredients in this chunk
        new_ingredients: Set[str] = set()
        for rec in records:
            for ing in rec["ner"]:
                if ing not in self._ingredient_id_cache:
                    new_ingredients.add(ing)

        # Step 2: Insert new ingredients and update cache
        if new_ingredients:
            new_ing_tuples = []
            for ing in sorted(new_ingredients):
                ing_id = self._next_ingredient_id
                self._next_ingredient_id += 1
                self._ingredient_id_cache[ing] = ing_id
                new_ing_tuples.append((ing_id, ing, 0))

            with conn:
                conn.executemany(
                    "INSERT OR IGNORE INTO ingredients (id, name, recipe_count) VALUES (?, ?, ?);",
                    new_ing_tuples,
                )

        # Step 3: Prepare batch inserts for metadata and inverted pairs
        meta_tuples = [(rec["recipe_id"], rec["ner_count"]) for rec in records]

        link_tuples = []
        # Track local frequency per ingredient to update counts later
        for rec in records:
            r_id = rec["recipe_id"]
            for ing in rec["ner"]:
                ing_id = self._ingredient_id_cache.get(ing)
                if ing_id is not None:
                    link_tuples.append((ing_id, r_id))

        with conn:
            conn.executemany(
                "INSERT OR REPLACE INTO recipes_metadata (recipe_id, ner_count) VALUES (?, ?);",
                meta_tuples,
            )
            conn.executemany(
                "INSERT OR IGNORE INTO recipe_ingredients (ingredient_id, recipe_id) VALUES (?, ?);",
                link_tuples,
            )

    def finalize_counts(self):
        """Updates recipe_count in the ingredients table."""
        conn = self.connect()
        with conn:
            conn.execute("""
                UPDATE ingredients
                SET recipe_count = (
                    SELECT COUNT(*)
                    FROM recipe_ingredients
                    WHERE recipe_ingredients.ingredient_id = ingredients.id
                );
            """)

    def find_recipes_by_ingredient(self, ingredient_name: str, limit: int = 100) -> List[int]:
        """Finds recipes containing a specific ingredient name."""
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("""
            SELECT ri.recipe_id
            FROM recipe_ingredients ri
            JOIN ingredients i ON ri.ingredient_id = i.id
            WHERE i.name = ?
            LIMIT ?;
        """, (ingredient_name.lower().strip(), limit))
        return [row[0] for row in cur.fetchall()]

    def find_recipes_by_pantry(
        self,
        pantry_ingredients: List[str],
        min_match: int = 1,
        limit: int = 100,
    ) -> List[Tuple[int, int, int]]:
        """
        Candidate generation query:
        Given pantry ingredients, finds recipe IDs containing at least min_match ingredients.
        Returns tuples of: (recipe_id, matched_pantry_count, total_recipe_ingredients).
        Ordered by matched_pantry_count DESC, then match ratio DESC.
        """
        if not pantry_ingredients:
            return []

        clean_pantry = [ing.lower().strip() for ing in pantry_ingredients if ing.strip()]
        if not clean_pantry:
            return []

        conn = self.connect()
        placeholders = ",".join("?" for _ in clean_pantry)

        query = f"""
            SELECT
                ri.recipe_id,
                COUNT(ri.ingredient_id) AS matched_count,
                rm.ner_count
            FROM recipe_ingredients ri
            JOIN ingredients i ON ri.ingredient_id = i.id
            JOIN recipes_metadata rm ON ri.recipe_id = rm.recipe_id
            WHERE i.name IN ({placeholders})
            GROUP BY ri.recipe_id
            HAVING matched_count >= ?
            ORDER BY matched_count DESC, (CAST(matched_count AS FLOAT) / rm.ner_count) DESC
            LIMIT ?;
        """

        cur = conn.cursor()
        cur.execute(query, clean_pantry + [min_match, limit])
        return cur.fetchall()

    def get_stats(self) -> dict:
        """Returns statistics on the SQLite index."""
        conn = self.connect()
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM recipes_metadata;")
        recipe_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM ingredients;")
        ingredient_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM recipe_ingredients;")
        link_count = cur.fetchone()[0]

        return {
            "indexed_recipes": recipe_count,
            "unique_ingredients": ingredient_count,
            "ingredient_recipe_links": link_count,
        }
