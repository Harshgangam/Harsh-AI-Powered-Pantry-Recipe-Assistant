from pathlib import Path
import sqlite3
from typing import Dict, List, Optional, Set, Tuple

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds

from backend.app.config import settings


class RecipeRetriever:
    """
    Handles high-performance candidate retrieval from the SQLite inverted index,
    selective batch detail loading from the Parquet dataset, and derived metadata loading.
    """

    def __init__(
        self,
        sqlite_path: Path = settings.SQLITE_INDEX_PATH,
        parquet_path: Path = settings.PARQUET_PATH,
        metadata_path: Optional[Path] = settings.METADATA_DB_PATH,
    ):
        self.sqlite_path = Path(sqlite_path)
        self.parquet_path = Path(parquet_path)
        self.metadata_path = Path(metadata_path) if metadata_path else None
        self._dataset = None

    def _get_dataset(self):
        if self._dataset is None and self.parquet_path.exists():
            self._dataset = ds.dataset(str(self.parquet_path), format="parquet")
        return self._dataset

    def retrieve_candidate_ids(
        self,
        pantry_variants: Set[str],
        limit: int = 150,
    ) -> List[Tuple[int, int, int]]:
        """
        Two-step high-speed candidate retrieval:
        1. Resolves text variants to integer ingredient IDs using index on ingredients(name).
        2. Queries recipe_ingredients clustered B-Tree by ingredient_id directly.

        Returns list of (recipe_id, matched_pantry_count, recipe_ner_count).
        """
        if not pantry_variants or not self.sqlite_path.exists():
            return []

        conn = sqlite3.connect(str(self.sqlite_path))
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA query_only = ON;")
        cur = conn.cursor()

        try:
            # Step 1: Resolve ingredient names to integer IDs
            variant_list = list(pantry_variants)
            placeholders = ",".join("?" for _ in variant_list)
            cur.execute(
                f"SELECT id, name FROM ingredients WHERE name IN ({placeholders});",
                variant_list,
            )
            ing_rows = cur.fetchall()
            if not ing_rows:
                return []

            ing_ids = [row[0] for row in ing_rows]

            # Step 2: Query candidate recipes using primary key on (ingredient_id, recipe_id)
            id_placeholders = ",".join("?" for _ in ing_ids)
            query = f"""
                SELECT
                    ri.recipe_id,
                    COUNT(ri.ingredient_id) AS matched_count,
                    rm.ner_count
                FROM recipe_ingredients ri
                JOIN recipes_metadata rm ON ri.recipe_id = rm.recipe_id
                WHERE ri.ingredient_id IN ({id_placeholders})
                GROUP BY ri.recipe_id
                ORDER BY matched_count DESC, (CAST(matched_count AS FLOAT) / rm.ner_count) DESC
                LIMIT ?;
            """
            cur.execute(query, ing_ids + [limit])
            candidates = cur.fetchall()
            return candidates

        finally:
            conn.close()

    def fetch_recipe_details(self, recipe_ids: List[int]) -> Dict[int, dict]:
        """
        Batch loads recipe details from Parquet for only the candidate recipe IDs.
        Returns a dict: recipe_id -> recipe_detail_dict.
        """
        if not recipe_ids:
            return {}

        dataset = self._get_dataset()
        if dataset is None:
            return {}

        id_array = pa.array(recipe_ids, type=pa.int64())
        filter_expr = pc.is_in(ds.field("recipe_id"), value_set=id_array)

        # Selective projection: load only required columns
        columns = [
            "recipe_id",
            "title",
            "ingredients",
            "directions",
            "link",
            "source",
            "ner",
            "ner_count",
        ]
        table = dataset.to_table(filter=filter_expr, columns=columns)
        pydict = table.to_pydict()

        details = {}
        row_count = len(pydict["recipe_id"])
        for i in range(row_count):
            r_id = pydict["recipe_id"][i]
            details[r_id] = {
                "recipe_id": r_id,
                "title": pydict["title"][i],
                "ingredients": list(pydict["ingredients"][i]),
                "directions": list(pydict["directions"][i]),
                "link": pydict["link"][i],
                "source": pydict["source"][i],
                "ner": [str(x) for x in pydict["ner"][i]],
                "ner_count": pydict["ner_count"][i],
            }

        return details

    def fetch_recipe_metadata(self, recipe_ids: List[int]) -> Dict[int, dict]:
        """
        Batch loads derived metadata from SQLite metadata store for candidate recipe IDs.
        Returns a dict: recipe_id -> metadata_dict.
        """
        if not recipe_ids or not self.metadata_path or not self.metadata_path.exists():
            return {}

        conn = sqlite3.connect(str(self.metadata_path))
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA query_only = ON;")
        cur = conn.cursor()

        try:
            placeholders = ",".join("?" for _ in recipe_ids)
            query = f"""
                SELECT
                    recipe_id,
                    cuisine,
                    cuisine_confidence,
                    cuisine_method,
                    dietary_compatibility,
                    dietary_confidence,
                    dietary_method,
                    estimated_time_minutes,
                    time_confidence,
                    time_method
                FROM recipe_metadata
                WHERE recipe_id IN ({placeholders});
            """
            cur.execute(query, recipe_ids)
            rows = cur.fetchall()
            meta_dict = {}
            for row in rows:
                meta_dict[row[0]] = {
                    "recipe_id": row[0],
                    "cuisine": row[1],
                    "cuisine_confidence": row[2],
                    "cuisine_method": row[3],
                    "dietary_compatibility": row[4],
                    "dietary_confidence": row[5],
                    "dietary_method": row[6],
                    "estimated_time_minutes": row[7],
                    "time_confidence": row[8],
                    "time_method": row[9],
                }
            return meta_dict
        finally:
            conn.close()
